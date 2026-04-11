from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional


Side = Literal["中心", "叶子"]


class ConstraintError(ValueError):
    pass


class NotFoundError(KeyError):
    pass


class BusinessStarGraphByMatrix:
    """
    带业务操作星型图
    ----------------
    实现方式：
    - 顶点表 vertex_table
    - 内容表 content_table
    - 邻接矩阵 adj_matrix

    约定：
    - 内容 content 必须包含唯一 id 字段
    - 中心顶点唯一
    - 每个叶子必须且只能连接到中心
    """

    CENTER: Side = "中心"
    LEAF: Side = "叶子"

    def __init__(self, *, allow_empty_star: bool = True) -> None:
        # 顶点表: vertex_id -> {vertex_id, side}
        self.vertex_table: Dict[str, Dict[str, Any]] = {}

        # 内容表: vertex_id -> content
        self.content_table: Dict[str, Dict[str, Any]] = {}

        # 业务索引: biz_id -> vertex_id
        self.biz_id_index: Dict[Any, str] = {}

        # 邻接矩阵配套索引
        self.vertex_order: List[str] = []
        self.vertex_pos: Dict[str, int] = {}
        self.adj_matrix: List[List[int]] = []

        self.allow_empty_star = allow_empty_star

    # =========
    # 基础工具
    # =========

    @staticmethod
    def _extract_biz_id(content: Dict[str, Any]) -> Any:
        if "id" not in content:
            raise ConstraintError("业务内容必须包含 id 字段。")
        return content["id"]

    @staticmethod
    def _make_vertex_id(side: Side, biz_id: Any) -> str:
        prefix = "x" if side == "中心" else "y"
        return f"{prefix}:{biz_id}"

    def _has_vertex(self, vertex_id: str) -> bool:
        return vertex_id in self.vertex_table

    def _get_pos(self, vertex_id: str) -> int:
        if vertex_id not in self.vertex_pos:
            raise NotFoundError(f"顶点 {vertex_id} 不存在。")
        return self.vertex_pos[vertex_id]

    def _side_of(self, vertex_id: str) -> Side:
        if vertex_id not in self.vertex_table:
            raise NotFoundError(f"顶点 {vertex_id} 不存在。")
        return self.vertex_table[vertex_id]["side"]

    def _center_vertices(self) -> List[str]:
        return [v for v, row in self.vertex_table.items() if row["side"] == self.CENTER]

    def _leaf_vertices(self) -> List[str]:
        return [v for v, row in self.vertex_table.items() if row["side"] == self.LEAF]

    def _center_vertex(self) -> Optional[str]:
        centers = self._center_vertices()
        if len(centers) == 0:
            return None
        if len(centers) > 1:
            raise ConstraintError("中心顶点超过 1 个，违反单星型图约束。")
        return centers[0]

    def _find_vertex_by_biz_id(self, biz_id: Any) -> str:
        vertex_id = self.biz_id_index.get(biz_id)
        if vertex_id is None:
            raise NotFoundError(f"未找到业务 id={biz_id} 对应的顶点。")
        return vertex_id

    # =========
    # 邻接矩阵操作
    # =========

    def _matrix_add_vertex(self, vertex_id: str) -> None:
        n = len(self.vertex_order)
        self.vertex_order.append(vertex_id)
        self.vertex_pos[vertex_id] = n

        for row in self.adj_matrix:
            row.append(0)
        self.adj_matrix.append([0] * (n + 1))

    def _matrix_delete_vertex(self, vertex_id: str) -> None:
        pos = self._get_pos(vertex_id)

        # 删除对应行
        self.adj_matrix.pop(pos)

        # 删除对应列
        for row in self.adj_matrix:
            row.pop(pos)

        # 删除顺序表
        self.vertex_order.pop(pos)

        # 重建位置索引
        self.vertex_pos = {v: i for i, v in enumerate(self.vertex_order)}

    def _matrix_set_edge(self, u: str, v: str, value: int) -> None:
        if u == v:
            raise ConstraintError("不允许自环。")
        i = self._get_pos(u)
        j = self._get_pos(v)
        self.adj_matrix[i][j] = value
        self.adj_matrix[j][i] = value

    def _matrix_has_edge(self, u: str, v: str) -> bool:
        i = self._get_pos(u)
        j = self._get_pos(v)
        return self.adj_matrix[i][j] == 1

    def _neighbors(self, vertex_id: str) -> List[str]:
        i = self._get_pos(vertex_id)
        row = self.adj_matrix[i]
        return [self.vertex_order[j] for j, val in enumerate(row) if val == 1]

    def _degree(self, vertex_id: str) -> int:
        i = self._get_pos(vertex_id)
        return sum(self.adj_matrix[i])

    # =========
    # Base 层：顶点 / 边 / 内容
    # =========

    def add_vertex(self, vertex_id: str, side: Side) -> None:
        if self._has_vertex(vertex_id):
            raise ConstraintError(f"顶点 {vertex_id} 已存在。")

        if side == self.CENTER:
            if len(self._center_vertices()) >= 1:
                raise ConstraintError("单星型图只允许一个中心顶点。")
        elif side != self.LEAF:
            raise ConstraintError(f"未知侧别: {side}")

        self.vertex_table[vertex_id] = {
            "vertex_id": vertex_id,
            "side": side,
        }
        self._matrix_add_vertex(vertex_id)

    def delete_vertex(self, vertex_id: str) -> None:
        if not self._has_vertex(vertex_id):
            raise NotFoundError(f"顶点 {vertex_id} 不存在。")

        # 删除内容表与业务索引
        if vertex_id in self.content_table:
            biz_id = self.content_table[vertex_id]["id"]
            self.biz_id_index.pop(biz_id, None)
            del self.content_table[vertex_id]

        # 删除矩阵与顶点表
        self._matrix_delete_vertex(vertex_id)
        del self.vertex_table[vertex_id]

    def add_edge(self, u: str, v: str) -> None:
        if not self._has_vertex(u) or not self._has_vertex(v):
            raise ConstraintError("新增边时，u 和 v 必须都已存在。")
        if u == v:
            raise ConstraintError("不允许自环。")

        side_u = self._side_of(u)
        side_v = self._side_of(v)

        # 跨侧连接约束
        if side_u == side_v:
            raise ConstraintError("不允许同侧连边。")

        # Y侧度一
        if side_u == self.LEAF and self._degree(u) >= 1 and not self._matrix_has_edge(u, v):
            raise ConstraintError(f"叶子顶点 {u} 的度必须为 1。")
        if side_v == self.LEAF and self._degree(v) >= 1 and not self._matrix_has_edge(u, v):
            raise ConstraintError(f"叶子顶点 {v} 的度必须为 1。")

        self._matrix_set_edge(u, v, 1)

    def delete_edge(self, u: str, v: str) -> None:
        if not self._has_vertex(u) or not self._has_vertex(v):
            raise ConstraintError("删边时，u 和 v 必须都存在。")
        if not self._matrix_has_edge(u, v):
            raise NotFoundError(f"边 ({u}, {v}) 不存在。")
        self._matrix_set_edge(u, v, 0)

    def add_content(self, vertex_id: str, content: Dict[str, Any]) -> None:
        if not self._has_vertex(vertex_id):
            raise ConstraintError(f"顶点 {vertex_id} 不存在。")
        if vertex_id in self.content_table:
            raise ConstraintError(f"顶点 {vertex_id} 已有内容。")

        biz_id = self._extract_biz_id(content)
        if biz_id in self.biz_id_index:
            raise ConstraintError(f"业务 id={biz_id} 已存在。")

        self.content_table[vertex_id] = deepcopy(content)
        self.biz_id_index[biz_id] = vertex_id

    def update_content(self, vertex_id: str, new_content: Dict[str, Any]) -> None:
        if vertex_id not in self.content_table:
            raise NotFoundError(f"顶点 {vertex_id} 没有内容。")

        old_content = self.content_table[vertex_id]
        old_biz_id = old_content["id"]
        new_biz_id = self._extract_biz_id(new_content)

        occupied = self.biz_id_index.get(new_biz_id)
        if occupied is not None and occupied != vertex_id:
            raise ConstraintError(f"业务 id={new_biz_id} 已被占用。")

        self.content_table[vertex_id] = deepcopy(new_content)

        if new_biz_id != old_biz_id:
            del self.biz_id_index[old_biz_id]
            self.biz_id_index[new_biz_id] = vertex_id

    def delete_content(self, vertex_id: str) -> None:
        if vertex_id not in self.content_table:
            raise NotFoundError(f"顶点 {vertex_id} 没有内容。")
        biz_id = self.content_table[vertex_id]["id"]
        del self.content_table[vertex_id]
        self.biz_id_index.pop(biz_id, None)

    def query_neighbors(self, vertex_id: str) -> List[str]:
        if not self._has_vertex(vertex_id):
            raise NotFoundError(f"顶点 {vertex_id} 不存在。")
        return self._neighbors(vertex_id)

    # =========
    # Principles 校验
    # =========

    def validate(self) -> None:
        vertices = list(self.vertex_table.keys())
        centers = self._center_vertices()
        leaves = self._leaf_vertices()

        # 单星型图：中心唯一
        if len(centers) != 1:
            raise ConstraintError("单星型图要求且仅允许一个中心顶点。")

        center = centers[0]

        # 每个顶点都必须有内容
        if set(vertices) != set(self.content_table.keys()):
            raise ConstraintError("所有顶点都必须绑定内容。")

        # 业务索引一致
        if len(self.biz_id_index) != len(self.content_table):
            raise ConstraintError("业务索引与内容表数量不一致。")
        for biz_id, vertex_id in self.biz_id_index.items():
            if vertex_id not in self.content_table:
                raise ConstraintError(f"业务 id={biz_id} 指向了不存在内容的顶点。")
            if self.content_table[vertex_id]["id"] != biz_id:
                raise ConstraintError(f"业务 id={biz_id} 与内容表不一致。")

        # 不允许有中心-中心 / 叶子-叶子边
        for i, u in enumerate(self.vertex_order):
            for j, v in enumerate(self.vertex_order):
                if i >= j:
                    continue
                if self.adj_matrix[i][j] == 1:
                    su = self._side_of(u)
                    sv = self._side_of(v)
                    if su == sv:
                        raise ConstraintError("存在同侧连边，违反二分图约束。")

        # 每个叶子度必须为 1，且必须连向中心
        for leaf in leaves:
            if self._degree(leaf) != 1:
                raise ConstraintError(f"叶子 {leaf} 的度必须等于 1。")
            if not self._matrix_has_edge(center, leaf):
                raise ConstraintError(f"叶子 {leaf} 必须连接到唯一中心 {center}。")

        # 中心完全连接所有叶子
        for leaf in leaves:
            if not self._matrix_has_edge(center, leaf):
                raise ConstraintError("中心必须与所有叶子相连。")

        # 不允许存在额外边
        expected_degree = len(leaves)
        if self._degree(center) != expected_degree:
            raise ConstraintError("中心的度必须等于叶子数。")

        # 无孤立点：允许初始化时只有中心无叶子
        if not self.allow_empty_star and len(leaves) == 0:
            raise ConstraintError("当前不允许空星型图。")

        if len(leaves) > 0 and self._degree(center) == 0:
            raise ConstraintError("存在叶子时，中心不能是孤立点。")

    # =========
    # Boundary：业务增删改查
    # =========

    def 业务增(self, side: Side, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        业务增：
        - 新增中心：只允许一次
        - 新增叶子：自动与中心连边
        """
        biz_id = self._extract_biz_id(content)
        vertex_id = self._make_vertex_id(side, biz_id)

        self.add_vertex(vertex_id, side)
        try:
            self.add_content(vertex_id, content)

            if side == self.LEAF:
                center = self._center_vertex()
                if center is None:
                    raise ConstraintError("新增叶子前必须先存在中心。")
                self.add_edge(center, vertex_id)

            self.validate()
            return self._view_of(vertex_id)

        except Exception:
            # 回滚
            if self._has_vertex(vertex_id):
                self.delete_vertex(vertex_id)
            raise

    def 业务删(self, biz_id: Any, *, cascade: bool = False) -> None:
        """
        业务删：
        - 删叶子：直接删
        - 删中心：默认不允许；cascade=True 时级联删整张图
        """
        vertex_id = self._find_vertex_by_biz_id(biz_id)
        side = self._side_of(vertex_id)

        if side == self.LEAF:
            self.delete_vertex(vertex_id)
            if len(self.vertex_table) > 0:
                self.validate()
            return

        # 删中心
        leaves = self._leaf_vertices()
        if leaves and not cascade:
            raise ConstraintError("中心下还有叶子，不能直接删除中心；如需整图删除，请设置 cascade=True。")

        if cascade:
            for leaf in list(leaves):
                self.delete_vertex(leaf)
            self.delete_vertex(vertex_id)
            return

        self.delete_vertex(vertex_id)

    def 业务改(self, biz_id: Any, new_content: Dict[str, Any]) -> Dict[str, Any]:
        vertex_id = self._find_vertex_by_biz_id(biz_id)

        old_content = deepcopy(self.content_table[vertex_id])
        old_index = dict(self.biz_id_index)

        try:
            self.update_content(vertex_id, new_content)
            self.validate()
            return self._view_of(vertex_id)
        except Exception:
            self.content_table[vertex_id] = old_content
            self.biz_id_index = old_index
            raise

    def 业务查(self, biz_id: Any) -> Dict[str, Any]:
        vertex_id = self._find_vertex_by_biz_id(biz_id)
        return self._view_of(vertex_id)

    # =========
    # 视图输出
    # =========

    def _view_of(self, vertex_id: str) -> Dict[str, Any]:
        neighbors = self._neighbors(vertex_id)
        return {
            "vertex_id": vertex_id,
            "side": self._side_of(vertex_id),
            "degree": self._degree(vertex_id),
            "content": deepcopy(self.content_table.get(vertex_id)),
            "neighbor_vertex_ids": neighbors,
            "neighbor_contents": [
                deepcopy(self.content_table[n]) for n in neighbors if n in self.content_table
            ],
        }

    def dump(self) -> Dict[str, Any]:
        return {
            "vertex_table": deepcopy(self.vertex_table),
            "content_table": deepcopy(self.content_table),
            "biz_id_index": deepcopy(self.biz_id_index),
            "vertex_order": list(self.vertex_order),
            "adj_matrix": deepcopy(self.adj_matrix),
        }


if __name__ == "__main__":
    g = BusinessStarGraphByMatrix()

    # 新增中心
    g.业务增("中心", {
        "id": "parent-001",
        "name": "父任务A",
        "status": "running"
    })

    # 新增叶子
    g.业务增("叶子", {
        "id": "child-001",
        "name": "子任务1",
        "status": "todo"
    })

    g.业务增("叶子", {
        "id": "child-002",
        "name": "子任务2",
        "status": "doing"
    })

    print("=== 当前图 ===")
    print(g.dump())

    print("\n=== 查询 child-001 ===")
    print(g.业务查("child-001"))

    print("\n=== 修改 child-001 ===")
    print(g.业务改("child-001", {
        "id": "child-001",
        "name": "子任务1",
        "status": "done"
    }))

    print("\n=== 删除 child-002 ===")
    g.业务删("child-002")
    print(g.dump())

    print("\n=== 级联删除中心 ===")
    g.业务删("parent-001", cascade=True)
    print(g.dump())
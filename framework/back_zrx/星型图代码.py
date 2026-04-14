from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Dict, Literal, Optional, Set, FrozenSet


Side = Literal["中心", "叶子"]


class ConstraintError(ValueError):
    """违反图约束时抛出。"""


class NotFoundError(KeyError):
    """查不到顶点/内容时抛出。"""


class BusinessStarGraph:
    """
    带业务操作星型图
    ----------------
    对应你的定义：

    - 顶点集 V
    - 中心顶点集 Vx
    - 叶子顶点集 Vy
    - 无向边集 E
    - 顶点-内容映射 val : V -> C

    业务约定：
    - 内容用 dict 表示
    - 每个内容必须包含唯一 id 字段
    - 业务查/改/删按内容 id 进行
    """

    CENTER: Side = "中心"
    LEAF: Side = "叶子"

    def __init__(self, *, allow_empty_star: bool = True) -> None:
        # Base
        self.V: Set[str] = set()
        self.Vx: Set[str] = set()
        self.Vy: Set[str] = set()
        self.E: Set[FrozenSet[str]] = set()

        # val : V -> C
        self.val: Dict[str, Dict[str, Any]] = {}

        # 业务层索引：内容 id -> 顶点 id
        self._biz_id_to_vertex: Dict[Any, str] = {}

        # 是否允许“只有中心、还没有叶子”的初始化状态
        self.allow_empty_star = allow_empty_star

    # =========
    # 基础工具
    # =========

    @staticmethod
    def _edge(u: str, v: str) -> FrozenSet[str]:
        if u == v:
            raise ConstraintError("不允许自环：{u, u}。")
        return frozenset((u, v))

    @staticmethod
    def _extract_content_id(content: Dict[str, Any]) -> Any:
        if "id" not in content:
            raise ConstraintError("业务内容必须包含唯一标识字段 id。")
        return content["id"]

    @staticmethod
    def _make_vertex_id(side: Side, biz_id: Any) -> str:
        prefix = "x" if side == "中心" else "y"
        return f"{prefix}:{biz_id}"

    def _snapshot(self):
        return (
            set(self.V),
            set(self.Vx),
            set(self.Vy),
            set(self.E),
            deepcopy(self.val),
            dict(self._biz_id_to_vertex),
        )

    def _restore(self, snap) -> None:
        self.V, self.Vx, self.Vy, self.E, self.val, self._biz_id_to_vertex = snap

    @contextmanager
    def _transaction(self):
        snap = self._snapshot()
        try:
            yield
        except Exception:
            self._restore(snap)
            raise

    # =========
    # Base 层操作
    # =========

    def addV(self, v: str, side: Side) -> None:
        """
        增加顶点 := addV(v)
        """
        if v in self.V:
            raise ConstraintError(f"顶点 {v} 已存在。")

        if side == self.CENTER:
            if len(self.Vx) >= 1:
                raise ConstraintError("单星型图要求中心顶点唯一，不能新增第二个中心。")
            self.Vx.add(v)
        elif side == self.LEAF:
            self.Vy.add(v)
        else:
            raise ConstraintError(f"未知侧别: {side}")

        self.V.add(v)

    def addE(self, u: str, v: str) -> None:
        """
        增加边 := addE(u, v)
        """
        if u not in self.V or v not in self.V:
            raise ConstraintError("新增边时，u 和 v 必须都已在 V 中。")

        edge = self._edge(u, v)

        # 跨侧连接约束：不允许 X-X 或 Y-Y
        if (u in self.Vx and v in self.Vx) or (u in self.Vy and v in self.Vy):
            raise ConstraintError("违反跨侧连接约束：不允许 X-X 或 Y-Y 直接连边。")

        # Y侧度一：每个叶子只能连一条边
        if u in self.Vy and self.deg(u) >= 1 and edge not in self.E:
            raise ConstraintError(f"叶子顶点 {u} 的度必须为 1，不能新增第二条边。")
        if v in self.Vy and self.deg(v) >= 1 and edge not in self.E:
            raise ConstraintError(f"叶子顶点 {v} 的度必须为 1，不能新增第二条边。")

        self.E.add(edge)

    def delE(self, u: str, v: str) -> None:
        """
        删除边 := delE(u, v)
        """
        edge = self._edge(u, v)
        if edge not in self.E:
            raise NotFoundError(f"边 {{{u}, {v}}} 不存在。")
        self.E.remove(edge)

    def delV(self, v: str) -> None:
        """
        删除顶点 := delV(v)
        """
        if v not in self.V:
            raise NotFoundError(f"顶点 {v} 不存在。")

        # 删所有关联边
        related_edges = {e for e in self.E if v in e}
        self.E -= related_edges

        # 删内容
        if v in self.val:
            biz_id = self.val[v]["id"]
            self._biz_id_to_vertex.pop(biz_id, None)
            del self.val[v]

        # 删顶点归属
        self.V.discard(v)
        self.Vx.discard(v)
        self.Vy.discard(v)

    def Query(self, v: str) -> Set[str]:
        """
        查询邻点 := Query(v)
        Q(v) = {u | {u, v} ∈ E}
        """
        if v not in self.V:
            raise NotFoundError(f"顶点 {v} 不存在。")

        neighbors: Set[str] = set()
        for e in self.E:
            if v in e:
                neighbors |= set(e)
        neighbors.discard(v)
        return neighbors

    def addVal(self, v: str, content: Dict[str, Any]) -> None:
        """
        内容新增 := addVal(c)
        将内容绑定到一个顶点上。
        """
        if v not in self.V:
            raise ConstraintError(f"顶点 {v} 不存在，不能绑定内容。")
        if v in self.val:
            raise ConstraintError(f"顶点 {v} 已经绑定内容，不能重复新增。")

        biz_id = self._extract_content_id(content)
        if biz_id in self._biz_id_to_vertex:
            raise ConstraintError(f"内容 id={biz_id} 已存在，必须唯一。")

        self.val[v] = deepcopy(content)
        self._biz_id_to_vertex[biz_id] = v

    def setVal(self, v: str, new_content: Dict[str, Any]) -> None:
        """
        内容修改 := setVal(c, c')
        """
        if v not in self.V:
            raise ConstraintError(f"顶点 {v} 不存在，不能修改内容。")
        if v not in self.val:
            raise ConstraintError(f"顶点 {v} 尚未绑定内容，不能修改。")

        old_content = self.val[v]
        old_id = old_content["id"]
        new_id = self._extract_content_id(new_content)

        # 允许改 id，但新 id 不能占用别人的
        occupied_vertex = self._biz_id_to_vertex.get(new_id)
        if occupied_vertex is not None and occupied_vertex != v:
            raise ConstraintError(f"内容 id={new_id} 已被其他顶点占用。")

        self.val[v] = deepcopy(new_content)

        if new_id != old_id:
            del self._biz_id_to_vertex[old_id]
            self._biz_id_to_vertex[new_id] = v

    def delVal(self, v: str) -> None:
        """
        内容删除 := delVal(c)
        """
        if v not in self.val:
            raise NotFoundError(f"顶点 {v} 没有绑定内容。")

        biz_id = self.val[v]["id"]
        del self.val[v]
        self._biz_id_to_vertex.pop(biz_id, None)

    # =========
    # Principles
    # =========

    def deg(self, v: str) -> int:
        if v not in self.V:
            raise NotFoundError(f"顶点 {v} 不存在。")
        return sum(1 for e in self.E if v in e)

    @property
    def center_vertex(self) -> Optional[str]:
        if len(self.Vx) == 0:
            return None
        if len(self.Vx) > 1:
            raise ConstraintError("当前图存在多个中心顶点，已违反单星型图约束。")
        return next(iter(self.Vx))

    def validate(self) -> None:
        """
        校验当前是否满足“带业务操作星型图”的核心约束。
        """

        # 1) 顶点集二分 / 两侧互不相交
        if not self.Vx.issubset(self.V):
            raise ConstraintError("Vx 必须是 V 的子集。")
        if not self.Vy.issubset(self.V):
            raise ConstraintError("Vy 必须是 V 的子集。")
        if self.Vx & self.Vy:
            raise ConstraintError("Vx 与 Vy 必须互不相交。")
        if self.V != (self.Vx | self.Vy):
            raise ConstraintError("必须满足 V = Vx ∪ Vy。")

        # 2) 单星型图：中心唯一
        if len(self.Vx) != 1:
            raise ConstraintError("单星型图要求 |Vx| = 1。")

        center = self.center_vertex
        assert center is not None

        # 3) 每个顶点都要有内容映射
        if set(self.val.keys()) != self.V:
            raise ConstraintError("带业务操作星型图要求每个顶点都必须有且仅有一份内容。")

        # 4) val : V -> C 一一落在当前图顶点上；业务 id 唯一
        if len(self._biz_id_to_vertex) != len(self.val):
            raise ConstraintError("业务 id 索引与 val 映射数量不一致。")

        for biz_id, v in self._biz_id_to_vertex.items():
            if v not in self.V:
                raise ConstraintError(f"业务 id={biz_id} 指向了不存在的顶点 {v}。")
            if self.val[v]["id"] != biz_id:
                raise ConstraintError(f"业务 id 索引与顶点内容不一致：顶点 {v}。")

        # 5) 跨侧连接约束
        for e in self.E:
            if len(e) != 2:
                raise ConstraintError("边必须恰好连接两个不同顶点。")
            u, v = tuple(e)
            if u not in self.V or v not in self.V:
                raise ConstraintError("边集 E 中不能出现不在 V 内的顶点。")

            if (u in self.Vx and v in self.Vx) or (u in self.Vy and v in self.Vy):
                raise ConstraintError("违反跨侧连接约束：不允许 X-X 或 Y-Y 直接连边。")

        # 6) Y侧度一
        for y in self.Vy:
            if self.deg(y) != 1:
                raise ConstraintError(f"叶子顶点 {y} 的度必须等于 1。")

        # 7) X侧完全连接 + 单中心
        # 在单中心场景下，等价于：每个叶子都与唯一中心相连，且不存在多余边
        expected_edges = {self._edge(center, y) for y in self.Vy}
        if self.E != expected_edges:
            raise ConstraintError("当前边集不满足单星型图的完全连接约束。")

        # 8) 无孤立点（可执行放宽版）
        # 允许初始化时只有中心、没有叶子；一旦有叶子，就必须不存在孤立点
        if not self.allow_empty_star and len(self.Vy) == 0:
            raise ConstraintError("当前不允许空星型图：必须至少有一个叶子。")

        if len(self.Vy) > 0:
            if self.deg(center) < 1:
                raise ConstraintError("存在叶子时，中心不能是孤立点。")

    # =========
    # 业务操作（Boundary）
    # =========

    def 业务增(self, side: Side, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        in<view> 业务增 := {c | c 是新增的内容}

        约定：
        - side = 中心 / 叶子
        - content 必须有 id
        - 新增叶子时自动与中心连边
        """
        with self._transaction():
            biz_id = self._extract_content_id(content)
            v = self._make_vertex_id(side, biz_id)

            self.addV(v, side)
            self.addVal(v, content)

            if side == self.LEAF:
                center = self.center_vertex
                if center is None:
                    raise ConstraintError("新增叶子前必须先存在中心顶点。")
                self.addE(center, v)

            self.validate()
            return self._vertex_view(v)

    def 业务删(self, biz_id: Any, *, cascade: bool = False) -> None:
        """
        in<view> 业务删 := {c | c 是删除的内容}
        实际按内容 id 删除。

        - 删叶子：直接删
        - 删中心：
            - 默认不允许（因为会破坏整张星型图）
            - cascade=True 时，级联删除整张星型图
        """
        with self._transaction():
            v = self._find_vertex_by_biz_id(biz_id)
            side = self._side_of(v)

            if side == self.LEAF:
                self.delV(v)
            else:
                if len(self.Vy) > 0 and not cascade:
                    raise ConstraintError("中心下仍有叶子，不能单独删除中心；若要整图删除，请使用 cascade=True。")

                if cascade:
                    # 删除整张星型图
                    for leaf in list(self.Vy):
                        self.delV(leaf)
                    self.delV(v)
                else:
                    self.delV(v)

            if len(self.V) > 0:
                self.validate()

    def 业务改(self, biz_id: Any, new_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        in<view> 业务改 := {c | c 是待修改的内容}
        实际按旧 biz_id 定位，再替换成 new_content。
        """
        with self._transaction():
            v = self._find_vertex_by_biz_id(biz_id)
            self.setVal(v, new_content)
            self.validate()
            return self._vertex_view(v)

    def 业务查(self, biz_id: Any) -> Dict[str, Any]:
        """
        in<view> 业务查 := {x | x 为 c 中的身份标识(id), c ∈ C}
        """
        v = self._find_vertex_by_biz_id(biz_id)
        return self._vertex_view(v)

    # =========
    # 对外辅助视图
    # =========

    def _find_vertex_by_biz_id(self, biz_id: Any) -> str:
        v = self._biz_id_to_vertex.get(biz_id)
        if v is None:
            raise NotFoundError(f"未找到业务内容 id={biz_id}。")
        return v

    def _side_of(self, v: str) -> Side:
        if v in self.Vx:
            return self.CENTER
        if v in self.Vy:
            return self.LEAF
        raise NotFoundError(f"顶点 {v} 不存在于 Vx 或 Vy。")

    def _vertex_view(self, v: str) -> Dict[str, Any]:
        neighbors = self.Query(v)
        neighbor_contents = [deepcopy(self.val[n]) for n in neighbors]

        return {
            "vertex_id": v,
            "side": self._side_of(v),
            "degree": self.deg(v),
            "content": deepcopy(self.val[v]),
            "neighbor_vertex_ids": list(neighbors),
            "neighbor_contents": neighbor_contents,
        }

    def dump(self) -> Dict[str, Any]:
        """
        导出当前整张图的状态
        """
        return {
            "V": sorted(self.V),
            "Vx": sorted(self.Vx),
            "Vy": sorted(self.Vy),
            "E": [sorted(tuple(e)) for e in self.E],
            "val": deepcopy(self.val),
        }


if __name__ == "__main__":
    g = BusinessStarGraph()

    # 1) 新增中心
    g.业务增("中心", {
        "id": "center-001",
        "name": "父任务A",
        "status": "running"
    })

    # 2) 新增叶子
    g.业务增("叶子", {
        "id": "leaf-001",
        "name": "子任务1",
        "status": "todo"
    })

    g.业务增("叶子", {
        "id": "leaf-002",
        "name": "子任务2",
        "status": "doing"
    })

    print("=== 当前图 ===")
    print(g.dump())

    print("\n=== 查询 leaf-001 ===")
    print(g.业务查("leaf-001"))

    print("\n=== 修改 leaf-001 ===")
    print(g.业务改("leaf-001", {
        "id": "leaf-001",
        "name": "子任务1",
        "status": "done",
        "updated_at": "2026-04-11"
    }))

    print("\n=== 删除 leaf-002 ===")
    g.业务删("leaf-002")
    print(g.dump())

    print("\n=== 级联删除中心 ===")
    g.业务删("center-001", cascade=True)
    print(g.dump())
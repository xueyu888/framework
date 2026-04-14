from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Generic, List, Optional, Sequence, TypeVar, Literal


K = TypeVar("K")  # 注册键类型
O = TypeVar("O")  # 算子类型
B = Literal["yes", "no"]


@dataclass
class DynamicKeyedOrderedRegistry(Generic[K, O]):
    """
    动态键控有序注册表

    对应描述中的内部状态：
    - R    : 当前注册键序列，保持注册先后顺序
    - bind : 注册键到算子的唯一映射

    语义约束：
    1. 键唯一
    2. 每个键唯一关联一个算子
    3. 注册成功时追加到序列末尾
    4. 删除时保持其余键相对顺序不变
    """

    _R: List[K] = field(default_factory=list)
    _bind: Dict[K, O] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初始化后一致性检查。"""
        self._validate_internal_state()

    def _validate_internal_state(self) -> None:
        """
        检查内部状态是否合法：
        - R 中键唯一
        - R 中的键集合与 bind 的键集合一致
        """
        if len(self._R) != len(set(self._R)):
            raise ValueError("非法内部状态：注册键序列 R 中存在重复键。")

        if set(self._R) != set(self._bind.keys()):
            raise ValueError("非法内部状态：R 与 bind 的键集合不一致。")

    def reg(self, k: K, o: O) -> B:
        """
        注册 reg : K × O -> B

        规则：
        - 若 k 不在当前状态中，则注册成功，返回 "yes"
          并使 R' = R ⋅ <k>，bind' = bind ∪ {k ↦ o}
        - 若 k 已存在，则注册失败，返回 "no"
          且内部状态不变
        """
        if k in self._bind:
            return "no"

        self._R.append(k)
        self._bind[k] = o
        return "yes"

    def delete(self, k: K) -> B:
        """
        删除 del : K -> B

        规则：
        - 若 k 在当前状态中，则删除成功，返回 "yes"
          且从 R 中移除 k，并保持其余键相对顺序不变
        - 若 k 不在当前状态中，则返回 "no"
          且内部状态不变
        """
        if k not in self._bind:
            return "no"

        del self._bind[k]
        self._R.remove(k)
        return "yes"

    def has(self, k: K) -> B:
        """
        存在性查询 has : K -> B

        - 存在返回 "yes"
        - 否则返回 "no"
        """
        return "yes" if k in self._bind else "no"

    def resolve(self, k: K) -> Optional[O]:
        """
        按键解析算子 resolve : K -> O ∪ {⊥}

        - 若 k 存在，则返回 bind(k)
        - 若 k 不存在，则返回 None（对应 ⊥）
        """
        return self._bind.get(k, None)

    def idx(self, i: int) -> Optional[K]:
        """
        按下标查询注册键 idx : N -> K ∪ {⊥}

        注意：
        - 这里严格按你的数学描述，使用 1-based 下标
        - 若 1 <= i <= n，则返回第 i 个注册键
        - 若 i > n 或 i <= 0，则返回 None（对应 ⊥）
        """
        if 1 <= i <= len(self._R):
            return self._R[i - 1]
        return None

    def enum(self) -> List[K]:
        """
        枚举 enum : ∅ -> K^(<ω>)

        返回当前注册键序列，保持注册先后顺序。
        返回的是副本，避免外部直接破坏内部状态。
        """
        return list(self._R)

    def size(self) -> int:
        """返回当前注册项数量。"""
        return len(self._R)

    def clear(self) -> None:
        """清空内部状态。"""
        self._R.clear()
        self._bind.clear()

    def snapshot(self) -> dict:
        """
        返回当前内部状态快照，便于调试或测试。
        """
        return {
            "R": list(self._R),
            "bind": dict(self._bind),
        }

    def __len__(self) -> int:
        return len(self._R)

    def __contains__(self, k: K) -> bool:
        return k in self._bind

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(R={self._R!r}, bind={self._bind!r})"
        )


if __name__ == "__main__":
    registry = DynamicKeyedOrderedRegistry[str, str]()

    print("初始状态:", registry.snapshot())

    # 注册
    print("reg('opA', '算子A') ->", registry.reg("opA", "算子A"))
    print("reg('opB', '算子B') ->", registry.reg("opB", "算子B"))
    print("reg('opA', '算子A-重复注册') ->", registry.reg("opA", "算子A-重复注册"))

    print("注册后状态:", registry.snapshot())

    # 存在性查询
    print("has('opA') ->", registry.has("opA"))
    print("has('opX') ->", registry.has("opX"))

    # 按键解析
    print("resolve('opA') ->", registry.resolve("opA"))
    print("resolve('opX') ->", registry.resolve("opX"))

    # 按下标查询（1-based）
    print("idx(1) ->", registry.idx(1))
    print("idx(2) ->", registry.idx(2))
    print("idx(3) ->", registry.idx(3))

    # 枚举
    print("enum() ->", registry.enum())

    # 删除
    print("delete('opA') ->", registry.delete("opA"))
    print("delete('opX') ->", registry.delete("opX"))

    print("删除后状态:", registry.snapshot())
    print("enum() ->", registry.enum())
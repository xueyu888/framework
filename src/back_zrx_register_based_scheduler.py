from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar


InputT = TypeVar("InputT")
ActionT = TypeVar("ActionT")
TriggerDecision = Literal["yes", "no"]


@dataclass(frozen=True, slots=True)
class RegisteredOperator(Generic[InputT, ActionT]):
    """
    对应《docs/back_zrx/注册式调度器.sf》里的算子 O。

    - ``trigger`` 对应 g : O × I -> B
    - ``action_builder`` 对应 m : O × I -> A
    """

    name: str
    trigger: Callable[[InputT], bool | TriggerDecision]
    action_builder: Callable[[InputT], ActionT]

    def decision_for(self, scheduler_input: InputT) -> TriggerDecision:
        decision = self.trigger(scheduler_input)
        if decision is True:
            return "yes"
        if decision is False:
            return "no"
        if decision in ("yes", "no"):
            return decision
        raise ValueError(
            f"operator {self.name!r} returned invalid trigger decision {decision!r}; "
            "expected bool, 'yes', or 'no'"
        )

    def build_action(self, scheduler_input: InputT) -> ActionT:
        return self.action_builder(scheduler_input)


def register(
    sequence: Sequence[RegisteredOperator[InputT, ActionT]],
    operator: RegisteredOperator[InputT, ActionT],
) -> tuple[RegisteredOperator[InputT, ActionT], ...]:
    """
    对应文档里的 reg(R, o)。

    新算子总是追加到注册序列末端，不做重排或去重。
    """

    return tuple(sequence) + (operator,)


def schedule(
    sequence: Sequence[RegisteredOperator[InputT, ActionT]],
    scheduler_input: InputT,
) -> tuple[ActionT, ...]:
    """
    对应文档里的 d(R, x)。

    只收集触发判定为 yes 的算子动作，并保持注册顺序。
    """

    actions: list[ActionT] = []
    for operator in sequence:
        if operator.decision_for(scheduler_input) == "yes":
            actions.append(operator.build_action(scheduler_input))
    return tuple(actions)


@dataclass(slots=True)
class RegisterBasedScheduler(Generic[InputT, ActionT]):
    """
    一个面向运行时使用的轻量封装。

    底层语义仍然保持为：
    1. ``register`` 只负责把算子追加进注册序列；
    2. ``schedule`` 只负责按序触发并输出动作序列。
    """

    _operators: list[RegisteredOperator[InputT, ActionT]] = field(default_factory=list)

    @property
    def registration_sequence(self) -> tuple[RegisteredOperator[InputT, ActionT], ...]:
        return tuple(self._operators)

    def register(self, operator: RegisteredOperator[InputT, ActionT]) -> tuple[RegisteredOperator[InputT, ActionT], ...]:
        self._operators.append(operator)
        return self.registration_sequence

    def register_many(
        self,
        operators: Iterable[RegisteredOperator[InputT, ActionT]],
    ) -> tuple[RegisteredOperator[InputT, ActionT], ...]:
        self._operators.extend(operators)
        return self.registration_sequence

    def schedule(self, scheduler_input: InputT) -> tuple[ActionT, ...]:
        return schedule(self.registration_sequence, scheduler_input)

from __future__ import annotations

from dataclasses import dataclass
import unittest

from back_zrx_register_based_scheduler import RegisterBasedScheduler, RegisteredOperator, register, schedule


@dataclass(frozen=True)
class DemoInput:
    enabled_operators: frozenset[str]
    payload: str


def _operator(name: str) -> RegisteredOperator[DemoInput, str]:
    return RegisteredOperator(
        name=name,
        trigger=lambda scheduler_input: name in scheduler_input.enabled_operators,
        action_builder=lambda scheduler_input: f"{name}:{scheduler_input.payload}",
    )


class RegisterBasedSchedulerTest(unittest.TestCase):
    def test_register_appends_operator_to_sequence_tail(self) -> None:
        sequence = register((), _operator("first"))
        sequence = register(sequence, _operator("second"))
        sequence = register(sequence, _operator("first"))

        self.assertEqual([operator.name for operator in sequence], ["first", "second", "first"])

    def test_schedule_only_collects_triggered_actions_in_registration_order(self) -> None:
        sequence = (
            _operator("first"),
            _operator("second"),
            _operator("third"),
        )

        actions = schedule(
            sequence,
            DemoInput(enabled_operators=frozenset({"third", "first"}), payload="payload"),
        )

        self.assertEqual(actions, ("first:payload", "third:payload"))

    def test_scheduler_wrapper_reuses_same_reg_and_schedule_semantics(self) -> None:
        scheduler = RegisterBasedScheduler[DemoInput, str]()
        scheduler.register_many((_operator("alpha"), _operator("beta"), _operator("gamma")))

        actions = scheduler.schedule(
            DemoInput(enabled_operators=frozenset({"beta"}), payload="done"),
        )

        self.assertEqual(actions, ("beta:done",))
        self.assertEqual(
            [operator.name for operator in scheduler.registration_sequence],
            ["alpha", "beta", "gamma"],
        )

    def test_trigger_accepts_yes_no_literals(self) -> None:
        literal_operator = RegisteredOperator[DemoInput, str](
            name="literal",
            trigger=lambda scheduler_input: "yes" if scheduler_input.payload == "run" else "no",
            action_builder=lambda scheduler_input: f"literal:{scheduler_input.payload}",
        )

        actions = schedule((literal_operator,), DemoInput(enabled_operators=frozenset(), payload="run"))

        self.assertEqual(actions, ("literal:run",))

    def test_invalid_trigger_decision_raises_value_error(self) -> None:
        invalid_operator = RegisteredOperator[DemoInput, str](
            name="invalid",
            trigger=lambda scheduler_input: "maybe",
            action_builder=lambda scheduler_input: scheduler_input.payload,
        )

        with self.assertRaisesRegex(ValueError, "invalid trigger decision"):
            schedule((invalid_operator,), DemoInput(enabled_operators=frozenset(), payload="x"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping, cast

from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
    UNSET,
)
from project_runtime.static_modules.common import (
    StaticBaseContract,
    StaticRuleContract,
    _require_boundary_dict,
)

MESSAGE_QUEUE_L0_M0_MODULE_ID = "message_queue.L0.M0"
MESSAGE_QUEUE_L0_M0_MODULE_KEY = "message_queue__L0__M0"
MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP = {
    "MESSAGEFORM": "messageform",
    "CAPACITY": "capacity",
    "LIFETIME": "lifetime",
    "ORDERRANGE": "orderrange",
    "HANDOFF": "handoff",
    "ACCESSRELATION": "accessrelation",
}

@dataclass(frozen=True, slots=True)
class MessageQueueL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    messageform: object = None
    capacity: object = None
    lifetime: object = None
    orderrange: object = None
    handoff: object = None
    accessrelation: object = None

    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class MessageQueueL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    messageform: object = UNSET
    capacity: object = UNSET
    lifetime: object = UNSET
    orderrange: object = UNSET
    handoff: object = UNSET
    accessrelation: object = UNSET

    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP)

class MessageQueueL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME")

class MessageQueueL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ORDERRANGE", "HANDOFF", "LIFETIME")

class MessageQueueL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "message_queue.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("ACCESSRELATION", "HANDOFF")

class MessageQueueL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME")

    def __init__(self, base_b1: MessageQueueL0M0B1Base) -> None:
        self._base_b1 = base_b1

class MessageQueueL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B1")
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME")

    def __init__(self, base_b1_1: MessageQueueL0M0B1Base, base_b1_2: MessageQueueL0M0B1Base) -> None:
        self._base_b1_1 = base_b1_1
        self._base_b1_2 = base_b1_2

class MessageQueueL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("ORDERRANGE", "HANDOFF", "LIFETIME")

    def __init__(self, base_b1: MessageQueueL0M0B1Base, base_b2: MessageQueueL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class MessageQueueL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "LIFETIME", "ACCESSRELATION", "HANDOFF")

    def __init__(self, base_b1: MessageQueueL0M0B1Base, base_b3: MessageQueueL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class MessageQueueL0M0R5Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "message_queue.L0.M0.R5"
    framework_rule_short_id: ClassVar[str] = "R5"
    owner_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("message_queue.L0.M0.B1", "message_queue.L0.M0.B2", "message_queue.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("MESSAGEFORM", "CAPACITY", "LIFETIME", "ORDERRANGE", "HANDOFF", "ACCESSRELATION")

    def __init__(self, base_b1: MessageQueueL0M0B1Base, base_b2: MessageQueueL0M0B2Base, base_b3: MessageQueueL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class MessageQueueL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_ID
    module_key: ClassVar[str] = MESSAGE_QUEUE_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        MessageQueueL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        MessageQueueL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            MessageQueueL0M0B1Base,
            MessageQueueL0M0B2Base,
            MessageQueueL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            MessageQueueL0M0R1Rule,
            MessageQueueL0M0R2Rule,
            MessageQueueL0M0R3Rule,
            MessageQueueL0M0R4Rule,
            MessageQueueL0M0R5Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(MESSAGE_QUEUE_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: MessageQueueL0M0StaticBoundaryParams,
        runtime_params: MessageQueueL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = MessageQueueL0M0B1Base(self)
        self.b2 = MessageQueueL0M0B2Base(self)
        self.b3 = MessageQueueL0M0B3Base(self)
        self.r1 = MessageQueueL0M0R1Rule(self.b1)
        self.r2 = MessageQueueL0M0R2Rule(self.b1, self.b1)
        self.r3 = MessageQueueL0M0R3Rule(self.b1, self.b2)
        self.r4 = MessageQueueL0M0R4Rule(self.b1, self.b3)
        self.r5 = MessageQueueL0M0R5Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> MessageQueueL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, MessageQueueL0M0StaticBoundaryParams):
            raise TypeError("MessageQueueL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, MessageQueueL0M0RuntimeBoundaryParams):
            raise TypeError("MessageQueueL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

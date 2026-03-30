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

FRONTEND_L0_M1_MODULE_ID = "frontend.L0.M1"
FRONTEND_L0_M1_MODULE_KEY = "frontend__L0__M1"
FRONTEND_L0_M1_BOUNDARY_FIELD_MAP = {
    "VALUE": "value",
    "ACTION": "action",
    "STATE": "state",
    "RESET": "reset",
    "FEEDBACK": "feedback",
    "TRANSFER": "transfer",
}

@dataclass(frozen=True, slots=True)
class FrontendL0M1StaticBoundaryParams(StaticBoundaryParamsContract):
    value: object = None
    action: object = None
    state: object = None
    reset: object = None
    feedback: object = None
    transfer: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL0M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    value: object = UNSET
    action: object = UNSET
    state: object = UNSET
    reset: object = UNSET
    feedback: object = UNSET
    transfer: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M1_BOUNDARY_FIELD_MAP)

class FrontendL0M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("VALUE", "ACTION", "RESET", "TRANSFER")

class FrontendL0M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("STATE", "FEEDBACK", "TRANSFER")

class FrontendL0M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M1.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("VALUE", "ACTION", "RESET", "TRANSFER")

    def __init__(self, base_b1: FrontendL0M1B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL0M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M1.B1", "frontend.L0.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("STATE", "FEEDBACK", "TRANSFER", "VALUE", "ACTION", "RESET")

    def __init__(self, base_b1: FrontendL0M1B1Base, base_b2: FrontendL0M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M1.B1", "frontend.L0.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("VALUE", "ACTION", "STATE", "RESET", "FEEDBACK", "TRANSFER")

    def __init__(self, base_b1: FrontendL0M1B1Base, base_b2: FrontendL0M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L0_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL0M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL0M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL0M1B1Base,
            FrontendL0M1B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL0M1R1Rule,
            FrontendL0M1R2Rule,
            FrontendL0M1R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL0M1StaticBoundaryParams,
        runtime_params: FrontendL0M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL0M1B1Base(self)
        self.b2 = FrontendL0M1B2Base(self)
        self.r1 = FrontendL0M1R1Rule(self.b1)
        self.r2 = FrontendL0M1R2Rule(self.b1, self.b2)
        self.r3 = FrontendL0M1R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL0M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL0M1StaticBoundaryParams):
            raise TypeError("FrontendL0M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL0M1RuntimeBoundaryParams):
            raise TypeError("FrontendL0M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

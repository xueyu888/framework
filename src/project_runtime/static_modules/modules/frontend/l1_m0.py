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

FRONTEND_L1_M0_MODULE_ID = "frontend.L1.M0"
FRONTEND_L1_M0_MODULE_KEY = "frontend__L1__M0"
FRONTEND_L1_M0_BOUNDARY_FIELD_MAP = {
    "TRIGGER": "trigger",
    "PICK": "pick",
    "OPTION": "option",
    "ACTION": "action",
    "STATUS": "status",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    trigger: object = None
    pick: object = None
    option: object = None
    action: object = None
    status: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    trigger: object = UNSET
    pick: object = UNSET
    option: object = UNSET
    action: object = UNSET
    status: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M0_BOUNDARY_FIELD_MAP)

class FrontendL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRIGGER", "ACTION", "STATUS")

class FrontendL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PICK", "OPTION", "ACTION", "A11Y")

class FrontendL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRIGGER", "ACTION", "STATUS")

    def __init__(self, base_b1: FrontendL1M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M0.B1", "frontend.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PICK", "OPTION", "A11Y", "ACTION", "STATUS")

    def __init__(self, base_b1: FrontendL1M0B1Base, base_b2: FrontendL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M0.B1", "frontend.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TRIGGER", "PICK", "OPTION", "ACTION", "STATUS", "A11Y")

    def __init__(self, base_b1: FrontendL1M0B1Base, base_b2: FrontendL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M0B1Base,
            FrontendL1M0B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M0R1Rule,
            FrontendL1M0R2Rule,
            FrontendL1M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M0StaticBoundaryParams,
        runtime_params: FrontendL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M0B1Base(self)
        self.b2 = FrontendL1M0B2Base(self)
        self.r1 = FrontendL1M0R1Rule(self.b1)
        self.r2 = FrontendL1M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M0R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M0StaticBoundaryParams):
            raise TypeError("FrontendL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M0RuntimeBoundaryParams):
            raise TypeError("FrontendL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

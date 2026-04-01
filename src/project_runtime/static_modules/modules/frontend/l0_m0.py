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

FRONTEND_L0_M0_MODULE_ID = "frontend.L0.M0"
FRONTEND_L0_M0_MODULE_KEY = "frontend__L0__M0"
FRONTEND_L0_M0_BOUNDARY_FIELD_MAP = {
    "SURFACE": "surface",
    "SLOT": "slot",
    "HOST": "host",
    "PROP": "prop",
    "FOCUS": "focus",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    surface: object = None
    slot: object = None
    host: object = None
    prop: object = None
    focus: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    surface: object = UNSET
    slot: object = UNSET
    host: object = UNSET
    prop: object = UNSET
    focus: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M0_BOUNDARY_FIELD_MAP)

class FrontendL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "SLOT")

class FrontendL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "PROP", "FOCUS", "A11Y")

class FrontendL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "SLOT")

    def __init__(self, base_b1: FrontendL0M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M0.B1", "frontend.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "PROP", "FOCUS", "A11Y", "SURFACE", "SLOT")

    def __init__(self, base_b1: FrontendL0M0B1Base, base_b2: FrontendL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L0.M0.B1", "frontend.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "SLOT", "HOST", "PROP", "FOCUS", "A11Y")

    def __init__(self, base_b1: FrontendL0M0B1Base, base_b2: FrontendL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L0_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL0M0B1Base,
            FrontendL0M0B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL0M0R1Rule,
            FrontendL0M0R2Rule,
            FrontendL0M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL0M0StaticBoundaryParams,
        runtime_params: FrontendL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL0M0B1Base(self)
        self.b2 = FrontendL0M0B2Base(self)
        self.r1 = FrontendL0M0R1Rule(self.b1)
        self.r2 = FrontendL0M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL0M0R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL0M0StaticBoundaryParams):
            raise TypeError("FrontendL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL0M0RuntimeBoundaryParams):
            raise TypeError("FrontendL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

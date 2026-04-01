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

FRONTEND_L1_M2_MODULE_ID = "frontend.L1.M2"
FRONTEND_L1_M2_MODULE_KEY = "frontend__L1__M2"
FRONTEND_L1_M2_BOUNDARY_FIELD_MAP = {
    "TEXT": "text",
    "PANEL": "panel",
    "VIEWPORT": "viewport",
    "META": "meta",
    "EMPTY": "empty",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class FrontendL1M2StaticBoundaryParams(StaticBoundaryParamsContract):
    text: object = None
    panel: object = None
    viewport: object = None
    meta: object = None
    empty: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL1M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    text: object = UNSET
    panel: object = UNSET
    viewport: object = UNSET
    meta: object = UNSET
    empty: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M2_BOUNDARY_FIELD_MAP)

class FrontendL1M2B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M2.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TEXT", "META", "A11Y")

class FrontendL1M2B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L1.M2.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PANEL", "VIEWPORT", "EMPTY", "A11Y")

class FrontendL1M2R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M2.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M2.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("TEXT", "META", "A11Y")

    def __init__(self, base_b1: FrontendL1M2B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL1M2R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M2.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M2.B1", "frontend.L1.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("PANEL", "VIEWPORT", "EMPTY", "TEXT", "META", "A11Y")

    def __init__(self, base_b1: FrontendL1M2B1Base, base_b2: FrontendL1M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M2R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L1.M2.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L1.M2.B1", "frontend.L1.M2.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("TEXT", "PANEL", "VIEWPORT", "META", "EMPTY", "A11Y")

    def __init__(self, base_b1: FrontendL1M2B1Base, base_b2: FrontendL1M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL1M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L1_M2_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L1_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL1M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL1M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL1M2B1Base,
            FrontendL1M2B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL1M2R1Rule,
            FrontendL1M2R2Rule,
            FrontendL1M2R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L1_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL1M2StaticBoundaryParams,
        runtime_params: FrontendL1M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL1M2B1Base(self)
        self.b2 = FrontendL1M2B2Base(self)
        self.r1 = FrontendL1M2R1Rule(self.b1)
        self.r2 = FrontendL1M2R2Rule(self.b1, self.b2)
        self.r3 = FrontendL1M2R3Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL1M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL1M2StaticBoundaryParams):
            raise TypeError("FrontendL1M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL1M2RuntimeBoundaryParams):
            raise TypeError("FrontendL1M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

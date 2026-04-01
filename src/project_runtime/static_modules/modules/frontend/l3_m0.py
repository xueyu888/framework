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

FRONTEND_L3_M0_MODULE_ID = "frontend.L3.M0"
FRONTEND_L3_M0_MODULE_KEY = "frontend__L3__M0"
FRONTEND_L3_M0_BOUNDARY_FIELD_MAP = {
    "PAGESET": "pageset",
    "HOST": "host",
    "RUNTIME": "runtime",
    "BOOT": "boot",
    "TRACE": "trace",
    "ROUTE": "route",
    "RETURN": "return_value",
}

@dataclass(frozen=True, slots=True)
class FrontendL3M0StaticBoundaryParams(StaticBoundaryParamsContract):
    pageset: object = None
    host: object = None
    runtime: object = None
    boot: object = None
    trace: object = None
    route: object = None
    return_value: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L3_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L3_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL3M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    pageset: object = UNSET
    host: object = UNSET
    runtime: object = UNSET
    boot: object = UNSET
    trace: object = UNSET
    route: object = UNSET
    return_value: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L3_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L3_M0_BOUNDARY_FIELD_MAP)

class FrontendL3M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L3.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("PAGESET", "HOST", "ROUTE", "RETURN")

class FrontendL3M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L3.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "BOOT", "TRACE")

class FrontendL3M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L3.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "BOOT", "TRACE", "ROUTE")

class FrontendL3M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("PAGESET", "HOST", "ROUTE", "RETURN")

    def __init__(self, base_b1: FrontendL3M0B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL3M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1", "frontend.L3.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "HOST", "BOOT", "TRACE", "PAGESET", "ROUTE", "RETURN")

    def __init__(self, base_b1: FrontendL3M0B1Base, base_b2: FrontendL3M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL3M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1", "frontend.L3.M0.B2", "frontend.L3.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("BOOT", "TRACE", "HOST", "RUNTIME", "ROUTE", "RETURN", "PAGESET")

    def __init__(self, base_b1: FrontendL3M0B1Base, base_b2: FrontendL3M0B2Base, base_b3: FrontendL3M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL3M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L3.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L3.M0.B1", "frontend.L3.M0.B2", "frontend.L3.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "HOST", "BOOT", "TRACE", "PAGESET", "ROUTE", "RETURN")

    def __init__(self, base_b1: FrontendL3M0B1Base, base_b2: FrontendL3M0B2Base, base_b3: FrontendL3M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL3M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L3_M0_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L3_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL3M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL3M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL3M0B1Base,
            FrontendL3M0B2Base,
            FrontendL3M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL3M0R1Rule,
            FrontendL3M0R2Rule,
            FrontendL3M0R3Rule,
            FrontendL3M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L3_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL3M0StaticBoundaryParams,
        runtime_params: FrontendL3M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL3M0B1Base(self)
        self.b2 = FrontendL3M0B2Base(self)
        self.b3 = FrontendL3M0B3Base(self)
        self.r1 = FrontendL3M0R1Rule(self.b1)
        self.r2 = FrontendL3M0R2Rule(self.b1, self.b2)
        self.r3 = FrontendL3M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = FrontendL3M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL3M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL3M0StaticBoundaryParams):
            raise TypeError("FrontendL3M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL3M0RuntimeBoundaryParams):
            raise TypeError("FrontendL3M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

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

FRONTEND_L2_M1_MODULE_ID = "frontend.L2.M1"
FRONTEND_L2_M1_MODULE_KEY = "frontend__L2__M1"
FRONTEND_L2_M1_BOUNDARY_FIELD_MAP = {
    "HOST": "host",
    "RUNTIME": "runtime",
    "RENDERER": "renderer",
    "STYLE": "style",
    "SCRIPT": "script",
    "BOOT": "boot",
    "TRACE": "trace",
}

@dataclass(frozen=True, slots=True)
class FrontendL2M1StaticBoundaryParams(StaticBoundaryParamsContract):
    host: object = None
    runtime: object = None
    renderer: object = None
    style: object = None
    script: object = None
    boot: object = None
    trace: object = None

    framework_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class FrontendL2M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    host: object = UNSET
    runtime: object = UNSET
    renderer: object = UNSET
    style: object = UNSET
    script: object = UNSET
    boot: object = UNSET
    trace: object = UNSET

    framework_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M1_BOUNDARY_FIELD_MAP)

class FrontendL2M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "RENDERER", "BOOT")

class FrontendL2M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "STYLE", "SCRIPT", "RENDERER")

class FrontendL2M1B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "frontend.L2.M1.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("BOOT", "TRACE", "HOST")

class FrontendL2M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("HOST", "RENDERER", "BOOT")

    def __init__(self, base_b1: FrontendL2M1B1Base) -> None:
        self._base_b1 = base_b1

class FrontendL2M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1", "frontend.L2.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "RENDERER", "STYLE", "SCRIPT", "HOST", "BOOT")

    def __init__(self, base_b1: FrontendL2M1B1Base, base_b2: FrontendL2M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class FrontendL2M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1", "frontend.L2.M1.B2", "frontend.L2.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("BOOT", "TRACE", "HOST", "RUNTIME", "STYLE", "SCRIPT", "RENDERER")

    def __init__(self, base_b1: FrontendL2M1B1Base, base_b2: FrontendL2M1B2Base, base_b3: FrontendL2M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL2M1R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "frontend.L2.M1.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("frontend.L2.M1.B1", "frontend.L2.M1.B2", "frontend.L2.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("RUNTIME", "HOST", "RENDERER", "STYLE", "SCRIPT", "BOOT", "TRACE")

    def __init__(self, base_b1: FrontendL2M1B1Base, base_b2: FrontendL2M1B2Base, base_b3: FrontendL2M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class FrontendL2M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = FRONTEND_L2_M1_MODULE_ID
    module_key: ClassVar[str] = FRONTEND_L2_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        FrontendL2M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        FrontendL2M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            FrontendL2M1B1Base,
            FrontendL2M1B2Base,
            FrontendL2M1B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            FrontendL2M1R1Rule,
            FrontendL2M1R2Rule,
            FrontendL2M1R3Rule,
            FrontendL2M1R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(FRONTEND_L2_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: FrontendL2M1StaticBoundaryParams,
        runtime_params: FrontendL2M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = FrontendL2M1B1Base(self)
        self.b2 = FrontendL2M1B2Base(self)
        self.b3 = FrontendL2M1B3Base(self)
        self.r1 = FrontendL2M1R1Rule(self.b1)
        self.r2 = FrontendL2M1R2Rule(self.b1, self.b2)
        self.r3 = FrontendL2M1R3Rule(self.b1, self.b2, self.b3)
        self.r4 = FrontendL2M1R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> FrontendL2M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, FrontendL2M1StaticBoundaryParams):
            raise TypeError("FrontendL2M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, FrontendL2M1RuntimeBoundaryParams):
            raise TypeError("FrontendL2M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

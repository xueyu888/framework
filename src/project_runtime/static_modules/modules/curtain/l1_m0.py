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

CURTAIN_L1_M0_MODULE_ID = "curtain.L1.M0"
CURTAIN_L1_M0_MODULE_KEY = "curtain__L1__M0"
CURTAIN_L1_M0_BOUNDARY_FIELD_MAP = {
    "INSTALL": "install",
    "ALIGN": "align",
    "POWER": "power",
    "CTRL": "ctrl",
    "CAL": "cal",
    "FAULT": "fault",
    "MAINT": "maint",
}

@dataclass(frozen=True, slots=True)
class CurtainL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    install: object = None
    align: object = None
    power: object = None
    ctrl: object = None
    cal: object = None
    fault: object = None
    maint: object = None

    framework_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class CurtainL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    install: object = UNSET
    align: object = UNSET
    power: object = UNSET
    ctrl: object = UNSET
    cal: object = UNSET
    fault: object = UNSET
    maint: object = UNSET

    framework_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L1_M0_BOUNDARY_FIELD_MAP)

class CurtainL1M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L1.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("INSTALL", "ALIGN", "MAINT")

class CurtainL1M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L1.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CTRL", "POWER", "ALIGN")

class CurtainL1M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "curtain.L1.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CAL", "FAULT", "MAINT")

class CurtainL1M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("INSTALL", "ALIGN", "MAINT")

    def __init__(self, base_b1: CurtainL1M0B1Base) -> None:
        self._base_b1 = base_b1

class CurtainL1M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1", "curtain.L1.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CTRL", "POWER", "ALIGN", "INSTALL")

    def __init__(self, base_b1: CurtainL1M0B1Base, base_b2: CurtainL1M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class CurtainL1M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1", "curtain.L1.M0.B2", "curtain.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CAL", "FAULT", "MAINT", "CTRL")

    def __init__(self, base_b1: CurtainL1M0B1Base, base_b2: CurtainL1M0B2Base, base_b3: CurtainL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL1M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "curtain.L1.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("curtain.L1.M0.B1", "curtain.L1.M0.B2", "curtain.L1.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("INSTALL", "ALIGN", "POWER", "CTRL", "CAL", "FAULT", "MAINT")

    def __init__(self, base_b1: CurtainL1M0B1Base, base_b2: CurtainL1M0B2Base, base_b3: CurtainL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class CurtainL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CURTAIN_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CURTAIN_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        CurtainL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        CurtainL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            CurtainL1M0B1Base,
            CurtainL1M0B2Base,
            CurtainL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            CurtainL1M0R1Rule,
            CurtainL1M0R2Rule,
            CurtainL1M0R3Rule,
            CurtainL1M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CURTAIN_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: CurtainL1M0StaticBoundaryParams,
        runtime_params: CurtainL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = CurtainL1M0B1Base(self)
        self.b2 = CurtainL1M0B2Base(self)
        self.b3 = CurtainL1M0B3Base(self)
        self.r1 = CurtainL1M0R1Rule(self.b1)
        self.r2 = CurtainL1M0R2Rule(self.b1, self.b2)
        self.r3 = CurtainL1M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = CurtainL1M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> CurtainL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, CurtainL1M0StaticBoundaryParams):
            raise TypeError("CurtainL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, CurtainL1M0RuntimeBoundaryParams):
            raise TypeError("CurtainL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

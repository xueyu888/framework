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

SHELF_L0_M0_MODULE_ID = "shelf.L0.M0"
SHELF_L0_M0_MODULE_KEY = "shelf__L0__M0"
SHELF_L0_M0_BOUNDARY_FIELD_MAP = {
    "LOAD": "load",
    "SIZE": "size",
    "GRID": "grid",
    "JOINT": "joint",
    "SAFE": "safe",
    "SCENE": "scene",
}

@dataclass(frozen=True, slots=True)
class ShelfL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    load: object = None
    size: object = None
    grid: object = None
    joint: object = None
    safe: object = None
    scene: object = None

    framework_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ShelfL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    load: object = UNSET
    size: object = UNSET
    grid: object = UNSET
    joint: object = UNSET
    safe: object = UNSET
    scene: object = UNSET

    framework_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L0_M0_BOUNDARY_FIELD_MAP)

class ShelfL0M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L0.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "SAFE")

class ShelfL0M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L0.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("JOINT", "SIZE")

class ShelfL0M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "shelf.L0.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("GRID", "SCENE", "SAFE")

class ShelfL0M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "JOINT", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b2: ShelfL0M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class ShelfL0M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("GRID", "SIZE", "SCENE", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b3: ShelfL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class ShelfL0M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B2", "shelf.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "GRID", "JOINT", "SCENE", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b2: ShelfL0M0B2Base, base_b3: ShelfL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL0M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "shelf.L0.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("shelf.L0.M0.B1", "shelf.L0.M0.B2", "shelf.L0.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("LOAD", "SIZE", "GRID", "JOINT", "SCENE", "SAFE")

    def __init__(self, base_b1: ShelfL0M0B1Base, base_b2: ShelfL0M0B2Base, base_b3: ShelfL0M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ShelfL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = SHELF_L0_M0_MODULE_ID
    module_key: ClassVar[str] = SHELF_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ShelfL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ShelfL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ShelfL0M0B1Base,
            ShelfL0M0B2Base,
            ShelfL0M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ShelfL0M0R1Rule,
            ShelfL0M0R2Rule,
            ShelfL0M0R3Rule,
            ShelfL0M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(SHELF_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ShelfL0M0StaticBoundaryParams,
        runtime_params: ShelfL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ShelfL0M0B1Base(self)
        self.b2 = ShelfL0M0B2Base(self)
        self.b3 = ShelfL0M0B3Base(self)
        self.r1 = ShelfL0M0R1Rule(self.b1, self.b2)
        self.r2 = ShelfL0M0R2Rule(self.b1, self.b3)
        self.r3 = ShelfL0M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = ShelfL0M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ShelfL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ShelfL0M0StaticBoundaryParams):
            raise TypeError("ShelfL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ShelfL0M0RuntimeBoundaryParams):
            raise TypeError("ShelfL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

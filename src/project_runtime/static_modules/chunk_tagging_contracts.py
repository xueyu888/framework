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

def _require_boundary_dict(payload: dict[str, dict[str, Any]], boundary_id: str) -> dict[str, Any]:
    boundary = payload.get(boundary_id)
    if not isinstance(boundary, dict):
        raise ValueError(f"missing module boundary context: {boundary_id}")
    value = boundary.get("value")
    if not isinstance(value, dict):
        raise ValueError(f"module boundary value must be a dict: {boundary_id}")
    return dict(value)

class ChunkTaggingBaseContract(BaseContract):
    def __init__(self, module: ModuleContract) -> None:
        self._module = module

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        context = getattr(self._module, "boundary_context", {})
        if not isinstance(context, dict):
            raise ValueError("module boundary context missing")
        return _require_boundary_dict(context, boundary_id)

class ChunkTaggingRuleContract(RuleContract):
    pass

CHUNK_TAGGING_L0_M0_MODULE_ID = 'Chunk_Tagging.L0.M0'
CHUNK_TAGGING_L0_M0_MODULE_KEY = 'Chunk_Tagging__L0__M0'
CHUNK_TAGGING_L0_M0_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6', 'P7': 'p7', 'P8': 'p8', 'P9': 'p9', 'P10': 'p10', 'P11': 'p11', 'P12': 'p12', 'P13': 'p13', 'P14': 'p14', 'P15': 'p15'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL0M0StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None
    p7: object = None
    p8: object = None
    p9: object = None
    p10: object = None
    p11: object = None
    p12: object = None
    p13: object = None
    p14: object = None
    p15: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L0_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL0M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET
    p7: object = UNSET
    p8: object = UNSET
    p9: object = UNSET
    p10: object = UNSET
    p11: object = UNSET
    p12: object = UNSET
    p13: object = UNSET
    p14: object = UNSET
    p15: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L0_M0_BOUNDARY_FIELD_MAP)

class ChunkTaggingL0M0B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0B4Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B4'
    framework_base_short_id: ClassVar[str] = 'B4'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0B5Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B5'
    framework_base_short_id: ClassVar[str] = 'B5'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0B6Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B6'
    framework_base_short_id: ClassVar[str] = 'B6'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0B7Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.B7'
    framework_base_short_id: ClassVar[str] = 'B7'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL0M0R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L0.M0.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L0.M0.B1', 'Chunk_Tagging.L0.M0.B2', 'Chunk_Tagging.L0.M0.B3', 'Chunk_Tagging.L0.M0.B4', 'Chunk_Tagging.L0.M0.B5', 'Chunk_Tagging.L0.M0.B6', 'Chunk_Tagging.L0.M0.B7')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15')

    def __init__(self, base_b1: ChunkTaggingL0M0B1Base, base_b2: ChunkTaggingL0M0B2Base, base_b3: ChunkTaggingL0M0B3Base, base_b4: ChunkTaggingL0M0B4Base, base_b5: ChunkTaggingL0M0B5Base, base_b6: ChunkTaggingL0M0B6Base, base_b7: ChunkTaggingL0M0B7Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4
        self._base_b5 = base_b5
        self._base_b6 = base_b6
        self._base_b7 = base_b7

class ChunkTaggingL0M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L0_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL0M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL0M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL0M0B1Base,
            ChunkTaggingL0M0B2Base,
            ChunkTaggingL0M0B3Base,
            ChunkTaggingL0M0B4Base,
            ChunkTaggingL0M0B5Base,
            ChunkTaggingL0M0B6Base,
            ChunkTaggingL0M0B7Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL0M0R1Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L0_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL0M0StaticBoundaryParams,
        runtime_params: ChunkTaggingL0M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL0M0B1Base(self)
        self.b2 = ChunkTaggingL0M0B2Base(self)
        self.b3 = ChunkTaggingL0M0B3Base(self)
        self.b4 = ChunkTaggingL0M0B4Base(self)
        self.b5 = ChunkTaggingL0M0B5Base(self)
        self.b6 = ChunkTaggingL0M0B6Base(self)
        self.b7 = ChunkTaggingL0M0B7Base(self)
        self.r1 = ChunkTaggingL0M0R1Rule(self.b1, self.b2, self.b3, self.b4, self.b5, self.b6, self.b7)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL0M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL0M0StaticBoundaryParams):
            raise TypeError("ChunkTaggingL0M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL0M0RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL0M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L1_M0_MODULE_ID = 'Chunk_Tagging.L1.M0'
CHUNK_TAGGING_L1_M0_MODULE_KEY = 'Chunk_Tagging__L1__M0'
CHUNK_TAGGING_L1_M0_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6', 'P7': 'p7'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL1M0StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None
    p7: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL1M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET
    p7: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M0_BOUNDARY_FIELD_MAP)

class ChunkTaggingL1M0B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M0.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')

class ChunkTaggingL1M0B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M0.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')

class ChunkTaggingL1M0B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M0.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')

class ChunkTaggingL1M0R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M0.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M0.B1', 'Chunk_Tagging.L1.M0.B2', 'Chunk_Tagging.L1.M0.B3')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')

    def __init__(self, base_b1: ChunkTaggingL1M0B1Base, base_b2: ChunkTaggingL1M0B2Base, base_b3: ChunkTaggingL1M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ChunkTaggingL1M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL1M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL1M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL1M0B1Base,
            ChunkTaggingL1M0B2Base,
            ChunkTaggingL1M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL1M0R1Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL1M0StaticBoundaryParams,
        runtime_params: ChunkTaggingL1M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL1M0B1Base(self)
        self.b2 = ChunkTaggingL1M0B2Base(self)
        self.b3 = ChunkTaggingL1M0B3Base(self)
        self.r1 = ChunkTaggingL1M0R1Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL1M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL1M0StaticBoundaryParams):
            raise TypeError("ChunkTaggingL1M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL1M0RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL1M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L1_M1_MODULE_ID = 'Chunk_Tagging.L1.M1'
CHUNK_TAGGING_L1_M1_MODULE_KEY = 'Chunk_Tagging__L1__M1'
CHUNK_TAGGING_L1_M1_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6', 'P7': 'p7', 'P8': 'p8', 'P9': 'p9', 'P10': 'p10', 'P11': 'p11', 'P12': 'p12', 'P13': 'p13', 'P14': 'p14', 'P15': 'p15'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL1M1StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None
    p7: object = None
    p8: object = None
    p9: object = None
    p10: object = None
    p11: object = None
    p12: object = None
    p13: object = None
    p14: object = None
    p15: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL1M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET
    p7: object = UNSET
    p8: object = UNSET
    p9: object = UNSET
    p10: object = UNSET
    p11: object = UNSET
    p12: object = UNSET
    p13: object = UNSET
    p14: object = UNSET
    p15: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M1_BOUNDARY_FIELD_MAP)

class ChunkTaggingL1M1B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M1B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P7', 'P8')

class ChunkTaggingL1M1B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P7', 'P8')

class ChunkTaggingL1M1B4Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.B4'
    framework_base_short_id: ClassVar[str] = 'B4'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P5', 'P6', 'P9')

class ChunkTaggingL1M1B5Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.B5'
    framework_base_short_id: ClassVar[str] = 'B5'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P7', 'P8')

class ChunkTaggingL1M1B6Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.B6'
    framework_base_short_id: ClassVar[str] = 'B6'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P11', 'P12', 'P13', 'P14')

class ChunkTaggingL1M1R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M1.B1', 'Chunk_Tagging.L1.M1.B2', 'Chunk_Tagging.L1.M1.B3')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4')

    def __init__(self, base_b1: ChunkTaggingL1M1B1Base, base_b2: ChunkTaggingL1M1B2Base, base_b3: ChunkTaggingL1M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ChunkTaggingL1M1R2Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.R2'
    framework_rule_short_id: ClassVar[str] = 'R2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M1.B1', 'Chunk_Tagging.L1.M1.B2', 'Chunk_Tagging.L1.M1.B3', 'Chunk_Tagging.L1.M1.B5')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P7', 'P8')

    def __init__(self, base_b1: ChunkTaggingL1M1B1Base, base_b2: ChunkTaggingL1M1B2Base, base_b3: ChunkTaggingL1M1B3Base, base_b5: ChunkTaggingL1M1B5Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b5 = base_b5

class ChunkTaggingL1M1R3Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.R3'
    framework_rule_short_id: ClassVar[str] = 'R3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M1.B4',)
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P5', 'P6')

    def __init__(self, base_b4: ChunkTaggingL1M1B4Base) -> None:
        self._base_b4 = base_b4

class ChunkTaggingL1M1R4Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.R4'
    framework_rule_short_id: ClassVar[str] = 'R4'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M1.B1', 'Chunk_Tagging.L1.M1.B4')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P5', 'P6', 'P9', 'P10')

    def __init__(self, base_b1: ChunkTaggingL1M1B1Base, base_b4: ChunkTaggingL1M1B4Base) -> None:
        self._base_b1 = base_b1
        self._base_b4 = base_b4

class ChunkTaggingL1M1R5Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M1.R5'
    framework_rule_short_id: ClassVar[str] = 'R5'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M1.B6',)
    boundary_ids: ClassVar[tuple[str, ...]] = ('P11', 'P12', 'P13', 'P14')

    def __init__(self, base_b6: ChunkTaggingL1M1B6Base) -> None:
        self._base_b6 = base_b6

class ChunkTaggingL1M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL1M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL1M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL1M1B1Base,
            ChunkTaggingL1M1B2Base,
            ChunkTaggingL1M1B3Base,
            ChunkTaggingL1M1B4Base,
            ChunkTaggingL1M1B5Base,
            ChunkTaggingL1M1B6Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL1M1R1Rule,
            ChunkTaggingL1M1R2Rule,
            ChunkTaggingL1M1R3Rule,
            ChunkTaggingL1M1R4Rule,
            ChunkTaggingL1M1R5Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL1M1StaticBoundaryParams,
        runtime_params: ChunkTaggingL1M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL1M1B1Base(self)
        self.b2 = ChunkTaggingL1M1B2Base(self)
        self.b3 = ChunkTaggingL1M1B3Base(self)
        self.b4 = ChunkTaggingL1M1B4Base(self)
        self.b5 = ChunkTaggingL1M1B5Base(self)
        self.b6 = ChunkTaggingL1M1B6Base(self)
        self.r1 = ChunkTaggingL1M1R1Rule(self.b1, self.b2, self.b3)
        self.r2 = ChunkTaggingL1M1R2Rule(self.b1, self.b2, self.b3, self.b5)
        self.r3 = ChunkTaggingL1M1R3Rule(self.b4)
        self.r4 = ChunkTaggingL1M1R4Rule(self.b1, self.b4)
        self.r5 = ChunkTaggingL1M1R5Rule(self.b6)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL1M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL1M1StaticBoundaryParams):
            raise TypeError("ChunkTaggingL1M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL1M1RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL1M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L1_M2_MODULE_ID = 'Chunk_Tagging.L1.M2'
CHUNK_TAGGING_L1_M2_MODULE_KEY = 'Chunk_Tagging__L1__M2'
CHUNK_TAGGING_L1_M2_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6', 'P7': 'p7', 'P8': 'p8', 'P9': 'p9', 'P10': 'p10', 'P11': 'p11', 'P12': 'p12', 'P13': 'p13'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL1M2StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None
    p7: object = None
    p8: object = None
    p9: object = None
    p10: object = None
    p11: object = None
    p12: object = None
    p13: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL1M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET
    p7: object = UNSET
    p8: object = UNSET
    p9: object = UNSET
    p10: object = UNSET
    p11: object = UNSET
    p12: object = UNSET
    p13: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M2_BOUNDARY_FIELD_MAP)

class ChunkTaggingL1M2B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2B4Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B4'
    framework_base_short_id: ClassVar[str] = 'B4'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2B5Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B5'
    framework_base_short_id: ClassVar[str] = 'B5'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2B6Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B6'
    framework_base_short_id: ClassVar[str] = 'B6'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2B7Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.B7'
    framework_base_short_id: ClassVar[str] = 'B7'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P11', 'P12', 'P13', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL1M2R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L1.M2.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L1.M2.B1', 'Chunk_Tagging.L1.M2.B2', 'Chunk_Tagging.L1.M2.B3', 'Chunk_Tagging.L1.M2.B4', 'Chunk_Tagging.L1.M2.B5', 'Chunk_Tagging.L1.M2.B6', 'Chunk_Tagging.L1.M2.B7')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13')

    def __init__(self, base_b1: ChunkTaggingL1M2B1Base, base_b2: ChunkTaggingL1M2B2Base, base_b3: ChunkTaggingL1M2B3Base, base_b4: ChunkTaggingL1M2B4Base, base_b5: ChunkTaggingL1M2B5Base, base_b6: ChunkTaggingL1M2B6Base, base_b7: ChunkTaggingL1M2B7Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4
        self._base_b5 = base_b5
        self._base_b6 = base_b6
        self._base_b7 = base_b7

class ChunkTaggingL1M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L1_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL1M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL1M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL1M2B1Base,
            ChunkTaggingL1M2B2Base,
            ChunkTaggingL1M2B3Base,
            ChunkTaggingL1M2B4Base,
            ChunkTaggingL1M2B5Base,
            ChunkTaggingL1M2B6Base,
            ChunkTaggingL1M2B7Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL1M2R1Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L1_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL1M2StaticBoundaryParams,
        runtime_params: ChunkTaggingL1M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL1M2B1Base(self)
        self.b2 = ChunkTaggingL1M2B2Base(self)
        self.b3 = ChunkTaggingL1M2B3Base(self)
        self.b4 = ChunkTaggingL1M2B4Base(self)
        self.b5 = ChunkTaggingL1M2B5Base(self)
        self.b6 = ChunkTaggingL1M2B6Base(self)
        self.b7 = ChunkTaggingL1M2B7Base(self)
        self.r1 = ChunkTaggingL1M2R1Rule(self.b1, self.b2, self.b3, self.b4, self.b5, self.b6, self.b7)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL1M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL1M2StaticBoundaryParams):
            raise TypeError("ChunkTaggingL1M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL1M2RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL1M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L2_M0_MODULE_ID = 'Chunk_Tagging.L2.M0'
CHUNK_TAGGING_L2_M0_MODULE_KEY = 'Chunk_Tagging__L2__M0'
CHUNK_TAGGING_L2_M0_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6', 'P7': 'p7', 'P8': 'p8', 'P9': 'p9', 'P10': 'p10'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None
    p7: object = None
    p8: object = None
    p9: object = None
    p10: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL2M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET
    p7: object = UNSET
    p8: object = UNSET
    p9: object = UNSET
    p10: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M0_BOUNDARY_FIELD_MAP)

class ChunkTaggingL2M0B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL2M0B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL2M0B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL2M0B4Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.B4'
    framework_base_short_id: ClassVar[str] = 'B4'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL2M0B5Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.B5'
    framework_base_short_id: ClassVar[str] = 'B5'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL2M0B6Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.B6'
    framework_base_short_id: ClassVar[str] = 'B6'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P10', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9')

class ChunkTaggingL2M0R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L2.M0.B1', 'Chunk_Tagging.L2.M0.B2', 'Chunk_Tagging.L2.M0.B3', 'Chunk_Tagging.L2.M0.B4')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')

    def __init__(self, base_b1: ChunkTaggingL2M0B1Base, base_b2: ChunkTaggingL2M0B2Base, base_b3: ChunkTaggingL2M0B3Base, base_b4: ChunkTaggingL2M0B4Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4

class ChunkTaggingL2M0R2Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.R2'
    framework_rule_short_id: ClassVar[str] = 'R2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L2.M0.B1', 'Chunk_Tagging.L2.M0.B2', 'Chunk_Tagging.L2.M0.B3', 'Chunk_Tagging.L2.M0.B4', 'Chunk_Tagging.L2.M0.B5')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8')

    def __init__(self, base_b1: ChunkTaggingL2M0B1Base, base_b2: ChunkTaggingL2M0B2Base, base_b3: ChunkTaggingL2M0B3Base, base_b4: ChunkTaggingL2M0B4Base, base_b5: ChunkTaggingL2M0B5Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4
        self._base_b5 = base_b5

class ChunkTaggingL2M0R3Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L2.M0.R3'
    framework_rule_short_id: ClassVar[str] = 'R3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L2.M0.B1', 'Chunk_Tagging.L2.M0.B2', 'Chunk_Tagging.L2.M0.B3', 'Chunk_Tagging.L2.M0.B4', 'Chunk_Tagging.L2.M0.B5', 'Chunk_Tagging.L2.M0.B6')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10')

    def __init__(self, base_b1: ChunkTaggingL2M0B1Base, base_b2: ChunkTaggingL2M0B2Base, base_b3: ChunkTaggingL2M0B3Base, base_b4: ChunkTaggingL2M0B4Base, base_b5: ChunkTaggingL2M0B5Base, base_b6: ChunkTaggingL2M0B6Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4
        self._base_b5 = base_b5
        self._base_b6 = base_b6

class ChunkTaggingL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL2M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL2M0B1Base,
            ChunkTaggingL2M0B2Base,
            ChunkTaggingL2M0B3Base,
            ChunkTaggingL2M0B4Base,
            ChunkTaggingL2M0B5Base,
            ChunkTaggingL2M0B6Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL2M0R1Rule,
            ChunkTaggingL2M0R2Rule,
            ChunkTaggingL2M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL2M0StaticBoundaryParams,
        runtime_params: ChunkTaggingL2M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL2M0B1Base(self)
        self.b2 = ChunkTaggingL2M0B2Base(self)
        self.b3 = ChunkTaggingL2M0B3Base(self)
        self.b4 = ChunkTaggingL2M0B4Base(self)
        self.b5 = ChunkTaggingL2M0B5Base(self)
        self.b6 = ChunkTaggingL2M0B6Base(self)
        self.r1 = ChunkTaggingL2M0R1Rule(self.b1, self.b2, self.b3, self.b4)
        self.r2 = ChunkTaggingL2M0R2Rule(self.b1, self.b2, self.b3, self.b4, self.b5)
        self.r3 = ChunkTaggingL2M0R3Rule(self.b1, self.b2, self.b3, self.b4, self.b5, self.b6)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL2M0StaticBoundaryParams):
            raise TypeError("ChunkTaggingL2M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL2M0RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL2M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L2_M1_MODULE_ID = 'Chunk_Tagging.L2.M1'
CHUNK_TAGGING_L2_M1_MODULE_KEY = 'Chunk_Tagging__L2__M1'
CHUNK_TAGGING_L2_M1_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL2M1StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL2M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M1_BOUNDARY_FIELD_MAP)

class ChunkTaggingL2M1B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M1.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL2M1B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M1.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL2M1B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M1.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL2M1B4Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M1.B4'
    framework_base_short_id: ClassVar[str] = 'B4'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL2M1R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L2.M1.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L2.M1.B1', 'Chunk_Tagging.L2.M1.B2', 'Chunk_Tagging.L2.M1.B3', 'Chunk_Tagging.L2.M1.B4')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

    def __init__(self, base_b1: ChunkTaggingL2M1B1Base, base_b2: ChunkTaggingL2M1B2Base, base_b3: ChunkTaggingL2M1B3Base, base_b4: ChunkTaggingL2M1B4Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4

class ChunkTaggingL2M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL2M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL2M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL2M1B1Base,
            ChunkTaggingL2M1B2Base,
            ChunkTaggingL2M1B3Base,
            ChunkTaggingL2M1B4Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL2M1R1Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL2M1StaticBoundaryParams,
        runtime_params: ChunkTaggingL2M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL2M1B1Base(self)
        self.b2 = ChunkTaggingL2M1B2Base(self)
        self.b3 = ChunkTaggingL2M1B3Base(self)
        self.b4 = ChunkTaggingL2M1B4Base(self)
        self.r1 = ChunkTaggingL2M1R1Rule(self.b1, self.b2, self.b3, self.b4)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL2M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL2M1StaticBoundaryParams):
            raise TypeError("ChunkTaggingL2M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL2M1RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL2M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L2_M2_MODULE_ID = 'Chunk_Tagging.L2.M2'
CHUNK_TAGGING_L2_M2_MODULE_KEY = 'Chunk_Tagging__L2__M2'
CHUNK_TAGGING_L2_M2_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6', 'P7': 'p7', 'P8': 'p8'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL2M2StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None
    p7: object = None
    p8: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL2M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET
    p7: object = UNSET
    p8: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M2_BOUNDARY_FIELD_MAP)

class ChunkTaggingL2M2B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M2.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8')

class ChunkTaggingL2M2B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L2.M2.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8')

class ChunkTaggingL2M2R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L2.M2.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L2.M2.B1', 'Chunk_Tagging.L2.M2.B2')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5')

    def __init__(self, base_b1: ChunkTaggingL2M2B1Base, base_b2: ChunkTaggingL2M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class ChunkTaggingL2M2R2Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L2.M2.R2'
    framework_rule_short_id: ClassVar[str] = 'R2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L2.M2.B1', 'Chunk_Tagging.L2.M2.B2')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P6', 'P7', 'P8')

    def __init__(self, base_b1: ChunkTaggingL2M2B1Base, base_b2: ChunkTaggingL2M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class ChunkTaggingL2M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L2_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL2M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL2M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL2M2B1Base,
            ChunkTaggingL2M2B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL2M2R1Rule,
            ChunkTaggingL2M2R2Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L2_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL2M2StaticBoundaryParams,
        runtime_params: ChunkTaggingL2M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL2M2B1Base(self)
        self.b2 = ChunkTaggingL2M2B2Base(self)
        self.r1 = ChunkTaggingL2M2R1Rule(self.b1, self.b2)
        self.r2 = ChunkTaggingL2M2R2Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL2M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL2M2StaticBoundaryParams):
            raise TypeError("ChunkTaggingL2M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL2M2RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL2M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

CHUNK_TAGGING_L3_M0_MODULE_ID = 'Chunk_Tagging.L3.M0'
CHUNK_TAGGING_L3_M0_MODULE_KEY = 'Chunk_Tagging__L3__M0'
CHUNK_TAGGING_L3_M0_BOUNDARY_FIELD_MAP = {'P1': 'p1', 'P2': 'p2', 'P3': 'p3', 'P4': 'p4', 'P5': 'p5', 'P6': 'p6'}

@dataclass(frozen=True, slots=True)
class ChunkTaggingL3M0StaticBoundaryParams(StaticBoundaryParamsContract):
    p1: object = None
    p2: object = None
    p3: object = None
    p4: object = None
    p5: object = None
    p6: object = None

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L3_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class ChunkTaggingL3M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    p1: object = UNSET
    p2: object = UNSET
    p3: object = UNSET
    p4: object = UNSET
    p5: object = UNSET
    p6: object = UNSET

    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L3_M0_BOUNDARY_FIELD_MAP)

class ChunkTaggingL3M0B1Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L3.M0.B1'
    framework_base_short_id: ClassVar[str] = 'B1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL3M0B2Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L3.M0.B2'
    framework_base_short_id: ClassVar[str] = 'B2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL3M0B3Base(ChunkTaggingBaseContract):
    framework_base_id: ClassVar[str] = 'Chunk_Tagging.L3.M0.B3'
    framework_base_short_id: ClassVar[str] = 'B3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

class ChunkTaggingL3M0R1Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L3.M0.R1'
    framework_rule_short_id: ClassVar[str] = 'R1'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L3.M0.B1', 'Chunk_Tagging.L3.M0.B2', 'Chunk_Tagging.L3.M0.B3')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4')

    def __init__(self, base_b1: ChunkTaggingL3M0B1Base, base_b2: ChunkTaggingL3M0B2Base, base_b3: ChunkTaggingL3M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ChunkTaggingL3M0R2Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L3.M0.R2'
    framework_rule_short_id: ClassVar[str] = 'R2'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L3.M0.B2', 'Chunk_Tagging.L3.M0.B3')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P3', 'P4', 'P5', 'P6')

    def __init__(self, base_b2: ChunkTaggingL3M0B2Base, base_b3: ChunkTaggingL3M0B3Base) -> None:
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ChunkTaggingL3M0R3Rule(ChunkTaggingRuleContract):
    framework_rule_id: ClassVar[str] = 'Chunk_Tagging.L3.M0.R3'
    framework_rule_short_id: ClassVar[str] = 'R3'
    owner_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ('Chunk_Tagging.L3.M0.B1', 'Chunk_Tagging.L3.M0.B2', 'Chunk_Tagging.L3.M0.B3')
    boundary_ids: ClassVar[tuple[str, ...]] = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6')

    def __init__(self, base_b1: ChunkTaggingL3M0B1Base, base_b2: ChunkTaggingL3M0B2Base, base_b3: ChunkTaggingL3M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class ChunkTaggingL3M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_ID
    module_key: ClassVar[str] = CHUNK_TAGGING_L3_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        ChunkTaggingL3M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        ChunkTaggingL3M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            ChunkTaggingL3M0B1Base,
            ChunkTaggingL3M0B2Base,
            ChunkTaggingL3M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            ChunkTaggingL3M0R1Rule,
            ChunkTaggingL3M0R2Rule,
            ChunkTaggingL3M0R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(CHUNK_TAGGING_L3_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: ChunkTaggingL3M0StaticBoundaryParams,
        runtime_params: ChunkTaggingL3M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = ChunkTaggingL3M0B1Base(self)
        self.b2 = ChunkTaggingL3M0B2Base(self)
        self.b3 = ChunkTaggingL3M0B3Base(self)
        self.r1 = ChunkTaggingL3M0R1Rule(self.b1, self.b2, self.b3)
        self.r2 = ChunkTaggingL3M0R2Rule(self.b2, self.b3)
        self.r3 = ChunkTaggingL3M0R3Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> ChunkTaggingL3M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, ChunkTaggingL3M0StaticBoundaryParams):
            raise TypeError("ChunkTaggingL3M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, ChunkTaggingL3M0RuntimeBoundaryParams):
            raise TypeError("ChunkTaggingL3M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

__all__ = [
    "ChunkTaggingBaseContract",
    "ChunkTaggingRuleContract",
    'CHUNK_TAGGING_L0_M0_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L0_M0_MODULE_ID',
    'CHUNK_TAGGING_L0_M0_MODULE_KEY',
    'ChunkTaggingL0M0Module',
    'ChunkTaggingL0M0RuntimeBoundaryParams',
    'ChunkTaggingL0M0StaticBoundaryParams',
    'ChunkTaggingL0M0B1Base',
    'ChunkTaggingL0M0B2Base',
    'ChunkTaggingL0M0B3Base',
    'ChunkTaggingL0M0B4Base',
    'ChunkTaggingL0M0B5Base',
    'ChunkTaggingL0M0B6Base',
    'ChunkTaggingL0M0B7Base',
    'ChunkTaggingL0M0R1Rule',
    'CHUNK_TAGGING_L1_M0_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L1_M0_MODULE_ID',
    'CHUNK_TAGGING_L1_M0_MODULE_KEY',
    'ChunkTaggingL1M0Module',
    'ChunkTaggingL1M0RuntimeBoundaryParams',
    'ChunkTaggingL1M0StaticBoundaryParams',
    'ChunkTaggingL1M0B1Base',
    'ChunkTaggingL1M0B2Base',
    'ChunkTaggingL1M0B3Base',
    'ChunkTaggingL1M0R1Rule',
    'CHUNK_TAGGING_L1_M1_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L1_M1_MODULE_ID',
    'CHUNK_TAGGING_L1_M1_MODULE_KEY',
    'ChunkTaggingL1M1Module',
    'ChunkTaggingL1M1RuntimeBoundaryParams',
    'ChunkTaggingL1M1StaticBoundaryParams',
    'ChunkTaggingL1M1B1Base',
    'ChunkTaggingL1M1B2Base',
    'ChunkTaggingL1M1B3Base',
    'ChunkTaggingL1M1B4Base',
    'ChunkTaggingL1M1B5Base',
    'ChunkTaggingL1M1B6Base',
    'ChunkTaggingL1M1R1Rule',
    'ChunkTaggingL1M1R2Rule',
    'ChunkTaggingL1M1R3Rule',
    'ChunkTaggingL1M1R4Rule',
    'ChunkTaggingL1M1R5Rule',
    'CHUNK_TAGGING_L1_M2_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L1_M2_MODULE_ID',
    'CHUNK_TAGGING_L1_M2_MODULE_KEY',
    'ChunkTaggingL1M2Module',
    'ChunkTaggingL1M2RuntimeBoundaryParams',
    'ChunkTaggingL1M2StaticBoundaryParams',
    'ChunkTaggingL1M2B1Base',
    'ChunkTaggingL1M2B2Base',
    'ChunkTaggingL1M2B3Base',
    'ChunkTaggingL1M2B4Base',
    'ChunkTaggingL1M2B5Base',
    'ChunkTaggingL1M2B6Base',
    'ChunkTaggingL1M2B7Base',
    'ChunkTaggingL1M2R1Rule',
    'CHUNK_TAGGING_L2_M0_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L2_M0_MODULE_ID',
    'CHUNK_TAGGING_L2_M0_MODULE_KEY',
    'ChunkTaggingL2M0Module',
    'ChunkTaggingL2M0RuntimeBoundaryParams',
    'ChunkTaggingL2M0StaticBoundaryParams',
    'ChunkTaggingL2M0B1Base',
    'ChunkTaggingL2M0B2Base',
    'ChunkTaggingL2M0B3Base',
    'ChunkTaggingL2M0B4Base',
    'ChunkTaggingL2M0B5Base',
    'ChunkTaggingL2M0B6Base',
    'ChunkTaggingL2M0R1Rule',
    'ChunkTaggingL2M0R2Rule',
    'ChunkTaggingL2M0R3Rule',
    'CHUNK_TAGGING_L2_M1_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L2_M1_MODULE_ID',
    'CHUNK_TAGGING_L2_M1_MODULE_KEY',
    'ChunkTaggingL2M1Module',
    'ChunkTaggingL2M1RuntimeBoundaryParams',
    'ChunkTaggingL2M1StaticBoundaryParams',
    'ChunkTaggingL2M1B1Base',
    'ChunkTaggingL2M1B2Base',
    'ChunkTaggingL2M1B3Base',
    'ChunkTaggingL2M1B4Base',
    'ChunkTaggingL2M1R1Rule',
    'CHUNK_TAGGING_L2_M2_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L2_M2_MODULE_ID',
    'CHUNK_TAGGING_L2_M2_MODULE_KEY',
    'ChunkTaggingL2M2Module',
    'ChunkTaggingL2M2RuntimeBoundaryParams',
    'ChunkTaggingL2M2StaticBoundaryParams',
    'ChunkTaggingL2M2B1Base',
    'ChunkTaggingL2M2B2Base',
    'ChunkTaggingL2M2R1Rule',
    'ChunkTaggingL2M2R2Rule',
    'CHUNK_TAGGING_L3_M0_BOUNDARY_FIELD_MAP',
    'CHUNK_TAGGING_L3_M0_MODULE_ID',
    'CHUNK_TAGGING_L3_M0_MODULE_KEY',
    'ChunkTaggingL3M0Module',
    'ChunkTaggingL3M0RuntimeBoundaryParams',
    'ChunkTaggingL3M0StaticBoundaryParams',
    'ChunkTaggingL3M0B1Base',
    'ChunkTaggingL3M0B2Base',
    'ChunkTaggingL3M0B3Base',
    'ChunkTaggingL3M0R1Rule',
    'ChunkTaggingL3M0R2Rule',
    'ChunkTaggingL3M0R3Rule',
]

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

BACKEND_L0_M5_MODULE_ID = "backend.L0.M5"
BACKEND_L0_M5_MODULE_KEY = "backend__L0__M5"
BACKEND_L0_M5_BOUNDARY_FIELD_MAP = {
    "query_text_in": "query_text_in",
    "candidate_text_out": "candidate_text_out",
    "candidate_hit_count": "candidate_hit_count",
    "score_out": "score_out",
    "top_k": "top_k",
    "score_order": "score_order",
    "min_score": "min_score",
    "vector_dimension": "vector_dimension",
    "vector_norm": "vector_norm",
    "retrieval_scope": "retrieval_scope",
    "comparator_kind": "comparator_kind",
    "text_vector_index_traceability": "text_vector_index_traceability",
}

@dataclass(frozen=True, slots=True)
class BackendL0M5StaticBoundaryParams(StaticBoundaryParamsContract):
    query_text_in: object = None
    candidate_text_out: object = None
    candidate_hit_count: object = None
    score_out: object = None
    top_k: object = None
    score_order: object = None
    min_score: object = None
    vector_dimension: object = None
    vector_norm: object = None
    retrieval_scope: object = None
    comparator_kind: object = None
    text_vector_index_traceability: object = None

    framework_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M5_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M5_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class BackendL0M5RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    query_text_in: object = UNSET
    candidate_text_out: object = UNSET
    candidate_hit_count: object = UNSET
    score_out: object = UNSET
    top_k: object = UNSET
    score_order: object = UNSET
    min_score: object = UNSET
    vector_dimension: object = UNSET
    vector_norm: object = UNSET
    retrieval_scope: object = UNSET
    comparator_kind: object = UNSET
    text_vector_index_traceability: object = UNSET

    framework_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M5_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M5_BOUNDARY_FIELD_MAP)

class BackendL0M5B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M5.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
        "candidate_text_out",
        "candidate_hit_count",
        "score_out",
        "top_k",
        "score_order",
        "min_score",
)

    def query_input_payload(self) -> dict[str, Any]:
        return self.boundary_value("query_text_in")

    def traceability_payload(self) -> dict[str, Any]:
        return self.boundary_value("text_vector_index_traceability")

    def candidate_output_payload(self) -> dict[str, Any]:
        return self.boundary_value("candidate_text_out")

class BackendL0M5B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M5.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
)

    def query_vector_payload(self) -> dict[str, Any]:
        return {
            "vector_dimension": self.boundary_value("vector_dimension"),
            "vector_norm": self.boundary_value("vector_norm"),
        }

class BackendL0M5B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M5.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
        "candidate_text_out",
        "candidate_hit_count",
        "score_out",
        "top_k",
        "score_order",
        "min_score",
)

    def candidate_vector_payload(self) -> dict[str, Any]:
        return {
            "retrieval_scope": self.boundary_value("retrieval_scope"),
            "vector_dimension": self.boundary_value("vector_dimension"),
            "vector_norm": self.boundary_value("vector_norm"),
        }

class BackendL0M5B4Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M5.B4"
    framework_base_short_id: ClassVar[str] = "B4"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
)

    def comparator_payload(self) -> dict[str, Any]:
        return self.boundary_value("comparator_kind")

class BackendL0M5B5Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M5.B5"
    framework_base_short_id: ClassVar[str] = "B5"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
        "candidate_text_out",
        "candidate_hit_count",
        "score_out",
        "top_k",
        "score_order",
        "min_score",
)

    def score_payload(self) -> dict[str, Any]:
        return {
            "candidate_hit_count": self.boundary_value("candidate_hit_count"),
            "score_out": self.boundary_value("score_out"),
            "top_k": self.boundary_value("top_k"),
            "score_order": self.boundary_value("score_order"),
            "min_score": self.boundary_value("min_score"),
        }

class BackendL0M5R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M5.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = (
        "backend.L0.M5.B1",
        "backend.L0.M5.B2",
        "backend.L0.M5.B3",
        "backend.L0.M5.B4",
        "backend.L0.M5.B5",
)
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
)

    def __init__(self, base_b1: BackendL0M5B1Base, base_b2: BackendL0M5B2Base, base_b3: BackendL0M5B3Base, base_b4: BackendL0M5B4Base, base_b5: BackendL0M5B5Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4
        self._base_b5 = base_b5

    def comparison_contract(self) -> dict[str, Any]:
        return {
            "participant_bases": ["B1", "B2", "B3", "B4", "B5"],
            "output_capabilities": ["C2"],
            "query_text_in": self._base_b1.query_input_payload(),
            "query_vector": self._base_b2.query_vector_payload(),
            "candidate_vectors": self._base_b3.candidate_vector_payload(),
            "comparator_kind": self._base_b4.comparator_payload(),
            "text_vector_index_traceability": self._base_b1.traceability_payload(),
        }

class BackendL0M5R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M5.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = (
        "backend.L0.M5.B1",
        "backend.L0.M5.B3",
        "backend.L0.M5.B5",
)
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "candidate_text_out",
        "candidate_hit_count",
        "score_out",
        "top_k",
        "score_order",
        "min_score",
        "text_vector_index_traceability",
)

    def __init__(self, base_b1: BackendL0M5B1Base, base_b3: BackendL0M5B3Base, base_b5: BackendL0M5B5Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3
        self._base_b5 = base_b5

    def export_contract(self) -> dict[str, Any]:
        return {
            "participant_bases": ["B1", "B3", "B5"],
            "output_capabilities": ["C1", "C2"],
            "candidate_text_out": self._base_b1.candidate_output_payload(),
            "candidate_vectors": self._base_b3.candidate_vector_payload(),
            "score_policy": self._base_b5.score_payload(),
            "text_vector_index_traceability": self._base_b1.traceability_payload(),
        }

class BackendL0M5R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M5.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = (
        "backend.L0.M5.B1",
        "backend.L0.M5.B2",
        "backend.L0.M5.B3",
        "backend.L0.M5.B4",
        "backend.L0.M5.B5",
    )
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_text_in",
        "candidate_text_out",
        "candidate_hit_count",
        "score_out",
        "top_k",
        "score_order",
        "min_score",
        "vector_dimension",
        "vector_norm",
        "retrieval_scope",
        "comparator_kind",
        "text_vector_index_traceability",
    )

    def __init__(
        self,
        base_b1: BackendL0M5B1Base,
        base_b2: BackendL0M5B2Base,
        base_b3: BackendL0M5B3Base,
        base_b4: BackendL0M5B4Base,
        base_b5: BackendL0M5B5Base,
    ) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3
        self._base_b4 = base_b4
        self._base_b5 = base_b5

    def invalid_conditions(self) -> list[str]:
        return [
            f"query_text_in cannot be mapped to deterministic query vector: {self._base_b1.query_input_payload()}",
            f"retrieval_scope cannot produce comparable candidate vectors: {self._base_b3.candidate_vector_payload()}",
            f"comparator_kind invalid: {self._base_b4.comparator_payload()}",
            f"score_policy cannot deterministically apply sort/threshold/top_k: {self._base_b5.score_payload()}",
            "candidate vectors must map back to unique candidate_text_out via text_vector_index_traceability",
        ]

class BackendL0M5Module(ModuleContract):
    framework_module_id: ClassVar[str] = BACKEND_L0_M5_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M5_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        BackendL0M5StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        BackendL0M5RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            BackendL0M5B1Base,
            BackendL0M5B2Base,
            BackendL0M5B3Base,
            BackendL0M5B4Base,
            BackendL0M5B5Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            BackendL0M5R1Rule,
            BackendL0M5R2Rule,
            BackendL0M5R3Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M5_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: BackendL0M5StaticBoundaryParams,
        runtime_params: BackendL0M5RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = BackendL0M5B1Base(self)
        self.b2 = BackendL0M5B2Base(self)
        self.b3 = BackendL0M5B3Base(self)
        self.b4 = BackendL0M5B4Base(self)
        self.b5 = BackendL0M5B5Base(self)
        self.r1 = BackendL0M5R1Rule(self.b1, self.b2, self.b3, self.b4, self.b5)
        self.r2 = BackendL0M5R2Rule(self.b1, self.b3, self.b5)
        self.r3 = BackendL0M5R3Rule(self.b1, self.b2, self.b3, self.b4, self.b5)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> BackendL0M5Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, BackendL0M5StaticBoundaryParams):
            raise TypeError("BackendL0M5Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, BackendL0M5RuntimeBoundaryParams):
            raise TypeError("BackendL0M5Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

    def export_module_spec(self, *, exact_export: Mapping[str, Any] | None = None) -> dict[str, Any]:
        _ = exact_export
        return {
            "retrieval_unit_spec": {
                "module_id": self.framework_module_id,
                "comparison_contract": self.r1.comparison_contract(),
                "export_contract": self.r2.export_contract(),
                "invalid_conditions": self.r3.invalid_conditions(),
            }
        }

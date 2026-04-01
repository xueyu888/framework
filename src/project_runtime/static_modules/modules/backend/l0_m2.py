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

BACKEND_L0_M2_MODULE_ID = "backend.L0.M2"
BACKEND_L0_M2_MODULE_KEY = "backend__L0__M2"
BACKEND_L0_M2_BOUNDARY_FIELD_MAP = {
    "query_binding_key_uniqueness": "query_binding_key_uniqueness",
    "query_text_length": "query_text_length",
    "query_text_lang": "query_text_lang",
}

@dataclass(frozen=True, slots=True)
class BackendL0M2StaticBoundaryParams(StaticBoundaryParamsContract):
    query_binding_key_uniqueness: object = None
    query_text_length: object = None
    query_text_lang: object = None

    framework_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M2_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class BackendL0M2RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    query_binding_key_uniqueness: object = UNSET
    query_text_length: object = UNSET
    query_text_lang: object = UNSET

    framework_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M2_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M2_BOUNDARY_FIELD_MAP)

class BackendL0M2B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M2.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_binding_key_uniqueness",
        "query_text_length",
        "query_text_lang",
)

    def text_constraints(self) -> dict[str, Any]:
        return {
            "query_text_length": self.boundary_value("query_text_length"),
            "query_text_lang": self.boundary_value("query_text_lang"),
        }

class BackendL0M2B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "backend.L0.M2.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_binding_key_uniqueness",
        "query_text_length",
        "query_text_lang",
)

    def binding_constraints(self) -> dict[str, Any]:
        return {
            "query_binding_key_uniqueness": self.boundary_value("query_binding_key_uniqueness"),
        }

class BackendL0M2R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M2.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = (
        "backend.L0.M2.B1",
        "backend.L0.M2.B2",
)
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_binding_key_uniqueness",
        "query_text_length",
        "query_text_lang",
)

    def __init__(self, base_b1: BackendL0M2B1Base, base_b2: BackendL0M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

    def valid_unit_contract(self) -> dict[str, Any]:
        return {
            "participant_bases": ["B1", "B2"],
            "output_capabilities": ["C1", "C2"],
            **self._base_b1.text_constraints(),
            **self._base_b2.binding_constraints(),
        }

class BackendL0M2R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "backend.L0.M2.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = (
        "backend.L0.M2.B1",
        "backend.L0.M2.B2",
    )
    boundary_ids: ClassVar[tuple[str, ...]] = (
        "query_binding_key_uniqueness",
        "query_text_length",
        "query_text_lang",
    )

    def __init__(self, base_b1: BackendL0M2B1Base, base_b2: BackendL0M2B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

    def invalid_conditions(self) -> list[str]:
        length_contract = self._base_b1.text_constraints()["query_text_length"]
        lang_contract = self._base_b1.text_constraints()["query_text_lang"]
        binding_contract = self._base_b2.binding_constraints()["query_binding_key_uniqueness"]
        return [
            f"query_text_length invalid: {length_contract}",
            f"query_text_lang invalid: {lang_contract}",
            f"query_binding_key_uniqueness invalid: {binding_contract}",
        ]

class BackendL0M2Module(ModuleContract):
    framework_module_id: ClassVar[str] = BACKEND_L0_M2_MODULE_ID
    module_key: ClassVar[str] = BACKEND_L0_M2_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        BackendL0M2StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        BackendL0M2RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            BackendL0M2B1Base,
            BackendL0M2B2Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            BackendL0M2R1Rule,
            BackendL0M2R2Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(BACKEND_L0_M2_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: BackendL0M2StaticBoundaryParams,
        runtime_params: BackendL0M2RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = BackendL0M2B1Base(self)
        self.b2 = BackendL0M2B2Base(self)
        self.r1 = BackendL0M2R1Rule(self.b1, self.b2)
        self.r2 = BackendL0M2R2Rule(self.b1, self.b2)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> BackendL0M2Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, BackendL0M2StaticBoundaryParams):
            raise TypeError("BackendL0M2Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, BackendL0M2RuntimeBoundaryParams):
            raise TypeError("BackendL0M2Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

    def export_module_spec(self, *, exact_export: Mapping[str, Any] | None = None) -> dict[str, Any]:
        _ = exact_export
        return {
            "query_text_unit_spec": {
                "module_id": self.framework_module_id,
                "rule_valid_contract": self.r1.valid_unit_contract(),
                "rule_invalid_conditions": self.r2.invalid_conditions(),
            }
        }

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

KNOWLEDGE_BASE_L2_M0_MODULE_ID = "knowledge_base.L2.M0"
KNOWLEDGE_BASE_L2_M0_MODULE_KEY = "knowledge_base__L2__M0"
KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP = {
    "SURFACE": "surface",
    "LIBRARY": "library",
    "PREVIEW": "preview",
    "CHAT": "chat",
    "CONTEXT": "context",
    "RETURN": "return_value",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL2M0StaticBoundaryParams(StaticBoundaryParamsContract):
    surface: object = None
    library: object = None
    preview: object = None
    chat: object = None
    context: object = None
    return_value: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL2M0RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    surface: object = UNSET
    library: object = UNSET
    preview: object = UNSET
    chat: object = UNSET
    context: object = UNSET
    return_value: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL2M0B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L2.M0.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW")

class KnowledgeBaseL2M0B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L2.M0.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "CONTEXT", "RETURN")

class KnowledgeBaseL2M0B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L2.M0.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "CONTEXT", "RETURN")

class KnowledgeBaseL2M0R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1",)
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base) -> None:
        self._base_b1 = base_b1

class KnowledgeBaseL2M0R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1", "knowledge_base.L2.M0.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("CHAT", "CONTEXT", "RETURN", "LIBRARY", "PREVIEW")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base, base_b2: KnowledgeBaseL2M0B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL2M0R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1", "knowledge_base.L2.M0.B2", "knowledge_base.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW", "CHAT", "CONTEXT", "RETURN")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base, base_b2: KnowledgeBaseL2M0B2Base, base_b3: KnowledgeBaseL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL2M0R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L2.M0.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L2.M0.B1", "knowledge_base.L2.M0.B2", "knowledge_base.L2.M0.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("SURFACE", "LIBRARY", "PREVIEW", "CHAT", "CONTEXT", "RETURN")

    def __init__(self, base_b1: KnowledgeBaseL2M0B1Base, base_b2: KnowledgeBaseL2M0B2Base, base_b3: KnowledgeBaseL2M0B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL2M0Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L2_M0_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL2M0StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL2M0RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL2M0B1Base,
            KnowledgeBaseL2M0B2Base,
            KnowledgeBaseL2M0B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL2M0R1Rule,
            KnowledgeBaseL2M0R2Rule,
            KnowledgeBaseL2M0R3Rule,
            KnowledgeBaseL2M0R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L2_M0_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL2M0StaticBoundaryParams,
        runtime_params: KnowledgeBaseL2M0RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL2M0B1Base(self)
        self.b2 = KnowledgeBaseL2M0B2Base(self)
        self.b3 = KnowledgeBaseL2M0B3Base(self)
        self.r1 = KnowledgeBaseL2M0R1Rule(self.b1)
        self.r2 = KnowledgeBaseL2M0R2Rule(self.b1, self.b2)
        self.r3 = KnowledgeBaseL2M0R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL2M0R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL2M0Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL2M0StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL2M0Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL2M0RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL2M0Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

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

KNOWLEDGE_BASE_L0_M1_MODULE_ID = "knowledge_base.L0.M1"
KNOWLEDGE_BASE_L0_M1_MODULE_KEY = "knowledge_base__L0__M1"
KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP = {
    "DOCVIEW": "docview",
    "TOC": "toc",
    "META": "meta",
    "FOCUS": "focus",
    "EMPTY": "empty",
    "A11Y": "a11y",
}

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M1StaticBoundaryParams(StaticBoundaryParamsContract):
    docview: object = None
    toc: object = None
    meta: object = None
    focus: object = None
    empty: object = None
    a11y: object = None

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP)

@dataclass(frozen=True, slots=True)
class KnowledgeBaseL0M1RuntimeBoundaryParams(RuntimeBoundaryParamsContract):
    docview: object = UNSET
    toc: object = UNSET
    meta: object = UNSET
    focus: object = UNSET
    empty: object = UNSET
    a11y: object = UNSET

    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_KEY
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP)

class KnowledgeBaseL0M1B1Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M1.B1"
    framework_base_short_id: ClassVar[str] = "B1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "META", "A11Y")

class KnowledgeBaseL0M1B2Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M1.B2"
    framework_base_short_id: ClassVar[str] = "B2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("TOC", "FOCUS", "A11Y")

class KnowledgeBaseL0M1B3Base(StaticBaseContract):
    framework_base_id: ClassVar[str] = "knowledge_base.L0.M1.B3"
    framework_base_short_id: ClassVar[str] = "B3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    boundary_ids: ClassVar[tuple[str, ...]] = ("FOCUS", "EMPTY", "A11Y")

class KnowledgeBaseL0M1R1Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R1"
    framework_rule_short_id: ClassVar[str] = "R1"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B2")
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "TOC", "META", "FOCUS")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b2: KnowledgeBaseL0M1B2Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2

class KnowledgeBaseL0M1R2Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R2"
    framework_rule_short_id: ClassVar[str] = "R2"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("FOCUS", "EMPTY", "A11Y", "DOCVIEW")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b3: KnowledgeBaseL0M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b3 = base_b3

class KnowledgeBaseL0M1R3Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R3"
    framework_rule_short_id: ClassVar[str] = "R3"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B2", "knowledge_base.L0.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "TOC", "META", "FOCUS", "EMPTY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b2: KnowledgeBaseL0M1B2Base, base_b3: KnowledgeBaseL0M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M1R4Rule(StaticRuleContract):
    framework_rule_id: ClassVar[str] = "knowledge_base.L0.M1.R4"
    framework_rule_short_id: ClassVar[str] = "R4"
    owner_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    base_ids: ClassVar[tuple[str, ...]] = ("knowledge_base.L0.M1.B1", "knowledge_base.L0.M1.B2", "knowledge_base.L0.M1.B3")
    boundary_ids: ClassVar[tuple[str, ...]] = ("DOCVIEW", "TOC", "META", "FOCUS", "EMPTY", "A11Y")

    def __init__(self, base_b1: KnowledgeBaseL0M1B1Base, base_b2: KnowledgeBaseL0M1B2Base, base_b3: KnowledgeBaseL0M1B3Base) -> None:
        self._base_b1 = base_b1
        self._base_b2 = base_b2
        self._base_b3 = base_b3

class KnowledgeBaseL0M1Module(ModuleContract):
    framework_module_id: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_ID
    module_key: ClassVar[str] = KNOWLEDGE_BASE_L0_M1_MODULE_KEY
    StaticBoundaryParams: ClassVar[type[StaticBoundaryParamsContract]] = cast(
        type[StaticBoundaryParamsContract],
        KnowledgeBaseL0M1StaticBoundaryParams,
    )
    RuntimeBoundaryParams: ClassVar[type[RuntimeBoundaryParamsContract]] = cast(
        type[RuntimeBoundaryParamsContract],
        KnowledgeBaseL0M1RuntimeBoundaryParams,
    )
    BaseTypes: ClassVar[tuple[type[BaseContract], ...]] = cast(
        tuple[type[BaseContract], ...],
        (
            KnowledgeBaseL0M1B1Base,
            KnowledgeBaseL0M1B2Base,
            KnowledgeBaseL0M1B3Base,
        ),
    )
    RuleTypes: ClassVar[tuple[type[RuleContract], ...]] = cast(
        tuple[type[RuleContract], ...],
        (
            KnowledgeBaseL0M1R1Rule,
            KnowledgeBaseL0M1R2Rule,
            KnowledgeBaseL0M1R3Rule,
            KnowledgeBaseL0M1R4Rule,
        ),
    )
    boundary_field_map: ClassVar[dict[str, str]] = dict(KNOWLEDGE_BASE_L0_M1_BOUNDARY_FIELD_MAP)
    merge_policy: ClassVar[str] = "runtime_override_else_static"

    def __init__(
        self,
        static_params: KnowledgeBaseL0M1StaticBoundaryParams,
        runtime_params: KnowledgeBaseL0M1RuntimeBoundaryParams | None = None,
    ) -> None:
        self.static_params = static_params
        self.runtime_params = runtime_params or self.runtime_params_default()
        self.boundary_context = self.build_boundary_context(self.static_params, self.runtime_params)
        self.b1 = KnowledgeBaseL0M1B1Base(self)
        self.b2 = KnowledgeBaseL0M1B2Base(self)
        self.b3 = KnowledgeBaseL0M1B3Base(self)
        self.r1 = KnowledgeBaseL0M1R1Rule(self.b1, self.b2)
        self.r2 = KnowledgeBaseL0M1R2Rule(self.b1, self.b3)
        self.r3 = KnowledgeBaseL0M1R3Rule(self.b1, self.b2, self.b3)
        self.r4 = KnowledgeBaseL0M1R4Rule(self.b1, self.b2, self.b3)

    @classmethod
    def from_payload(
        cls,
        static_payload: Mapping[str, Any],
        runtime_payload: Mapping[str, Any] | None = None,
    ) -> KnowledgeBaseL0M1Module:
        static_params = cls.static_params_from_mapping(dict(static_payload))
        if not isinstance(static_params, KnowledgeBaseL0M1StaticBoundaryParams):
            raise TypeError("KnowledgeBaseL0M1Module static params type mismatch")
        if runtime_payload is None:
            runtime_params = cls.runtime_params_default()
        else:
            runtime_params = cls.RuntimeBoundaryParams(**dict(runtime_payload))
        if not isinstance(runtime_params, KnowledgeBaseL0M1RuntimeBoundaryParams):
            raise TypeError("KnowledgeBaseL0M1Module runtime params type mismatch")
        return cls(static_params, runtime_params)

    def boundary_value(self, boundary_id: str) -> dict[str, Any]:
        return _require_boundary_dict(self.boundary_context, boundary_id)

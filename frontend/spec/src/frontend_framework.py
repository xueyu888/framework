from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Goal:
    statement: str


@dataclass(frozen=True)
class BoundaryDefinition:
    device: str
    browser: str
    network: str
    data_scale: str
    latency_budget_ms: int


class Module(str, Enum):
    OVERVIEW = "overview"
    PAGE = "page"
    BUSINESS_COMPONENT = "business_component"
    BASE_COMPONENT = "base_component"


MODULE_ROLE = {
    Module.OVERVIEW: "App shell, router and global state boundary",
    Module.PAGE: "Page orchestration and flow state",
    Module.BUSINESS_COMPONENT: "Business semantic components",
    Module.BASE_COMPONENT: "Reusable domain-agnostic UI primitives",
}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str


@dataclass(frozen=True)
class CombinationRules:
    rules: tuple[Rule, ...]

    @staticmethod
    def default() -> "CombinationRules":
        return CombinationRules(
            rules=(
                Rule("R1", "page must compose page/business/base layers"),
                Rule("R2", "business component must not directly depend on route object"),
                Rule("R3", "base component must be domain-agnostic"),
                Rule("R4", "async state must include loading/success/error/empty"),
                Rule("R5", "critical interactions must be keyboard accessible"),
                Rule("R6", "use design token for core styles"),
                Rule("R7", "key user journey must have analytics events"),
                Rule("R8", "errors must provide recoverable actions"),
                Rule("R9", "list/chart must enforce data boundary"),
                Rule("R10", "all rules must be decidable with failure reasons"),
            )
        )


@dataclass(frozen=True)
class VerificationInput:
    performance_baseline: float
    performance_target: float
    success_rate_baseline: float
    success_rate_target: float
    error_rate_baseline: float
    error_rate_target: float


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    reasons: list[str]


def verify(input_data: VerificationInput) -> VerificationResult:
    reasons: list[str] = []
    if not (input_data.performance_target > input_data.performance_baseline):
        reasons.append("performance target must be greater than baseline")
    if not (input_data.success_rate_target > input_data.success_rate_baseline):
        reasons.append("success rate target must be greater than baseline")
    if not (input_data.error_rate_target < input_data.error_rate_baseline):
        reasons.append("error rate target must be lower than baseline")
    return VerificationResult(passed=len(reasons) == 0, reasons=reasons)

from __future__ import annotations

import json
from pathlib import Path

from frontend_framework import (
    BoundaryDefinition,
    CombinationRules,
    Goal,
    VerificationInput,
    verify,
)


def main() -> None:
    goal = Goal("Improve frontend experience and conversion efficiency")
    boundary = BoundaryDefinition(
        device="desktop+mobile",
        browser="last 2 major versions",
        network="3G and above",
        data_scale="table<=2000 rows; chart<=5000 points",
        latency_budget_ms=300,
    )
    rules = CombinationRules.default()
    verification_input = VerificationInput(
        performance_baseline=1.0,
        performance_target=1.2,
        success_rate_baseline=0.90,
        success_rate_target=0.95,
        error_rate_baseline=0.05,
        error_rate_target=0.02,
    )
    verification_result = verify(verification_input)

    out = {
        "goal": goal.statement,
        "boundary": boundary.__dict__,
        "rules": [{"id": r.rule_id, "desc": r.description} for r in rules.rules],
        "verification": {
            "passed": verification_result.passed,
            "reasons": verification_result.reasons,
        },
    }

    docs = Path("docs")
    docs.mkdir(parents=True, exist_ok=True)
    logic_path = docs / "logic_record.json"
    logic_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime


def _default_project_file_arg() -> str | None:
    if DEFAULT_PROJECT_FILE is None:
        return None
    try:
        return str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT))
    except ValueError:
        return str(DEFAULT_PROJECT_FILE)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize the project under the new Framework -> Config -> Code -> Evidence architecture."
    )
    parser.add_argument(
        "--project-file",
        default=_default_project_file_arg(),
        help="path to the project.toml file",
    )
    parser.add_argument(
        "--allow-framework-only-fallback",
        action="store_true",
        help=(
            "when full materialization fails, still refresh canonical.framework snapshot "
            "for selected framework modules"
        ),
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    assembly = materialize_project_runtime(
        args.project_file,
        allow_framework_only_fallback=bool(args.allow_framework_only_fallback),
    )
    artifacts = assembly.generated_artifacts
    if artifacts is None:
        raise ValueError("generated artifact paths are required after materialization")
    materialization_mode = ""
    materialization_layer = assembly.canonical.get("materialization")
    if isinstance(materialization_layer, dict):
        materialization_mode = str(materialization_layer.get("mode") or "").strip()
    if not materialization_mode:
        materialization_mode = "unknown"
    print(f"[materialize] project={assembly.metadata.project_id}")
    print(f"[materialize] canonical={artifacts.canonical_json}")
    print(f"[materialize] mode={materialization_mode}")
    print(
        "[materialize] validation="
        f"passed={assembly.validation_reports.passed} "
        f"rules={assembly.validation_reports.rule_count}"
    )
    return 0 if assembly.validation_reports.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

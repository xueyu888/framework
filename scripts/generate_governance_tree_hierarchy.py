from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from generate_module_hierarchy_html import load_hierarchy, render_html
from workspace_governance import (
    DEFAULT_WORKSPACE_GOVERNANCE_HTML,
    DEFAULT_WORKSPACE_GOVERNANCE_JSON,
    build_workspace_governance_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate repository-wide governance tree JSON and HTML."
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_WORKSPACE_GOVERNANCE_JSON,
        help="Output governance tree JSON path.",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=DEFAULT_WORKSPACE_GOVERNANCE_HTML,
        help="Output governance tree HTML path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_workspace_governance_payload()
    output_json = args.output_json.resolve()
    output_html = args.output_html.resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    graph = load_hierarchy(output_json)
    render_html(graph, output_html, width=1680, height=1080)
    print(f"[OK] governance tree JSON generated: {output_json}")
    print(f"[OK] governance tree HTML generated: {output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

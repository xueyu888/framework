from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from standards_tree import build_standards_tree


REGISTRY_PATH = REPO_ROOT / "mapping" / "mapping_registry.json"


def main() -> int:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("mapping_registry.json must decode into an object")
    payload["tree"] = build_standards_tree()
    REGISTRY_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("[OK] synchronized standards tree ->", REGISTRY_PATH.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

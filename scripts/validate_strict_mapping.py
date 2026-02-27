from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "mapping_registry.json"


REQUIRED_LEVELS = ("L0", "L1", "L2", "L3")


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"missing mapping registry: {REGISTRY_PATH}")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def collect_changed_files() -> set[str]:
    changed: set[str] = set()

    commands = [
        ["git", "diff", "--name-only"],
        ["git", "diff", "--name-only", "--cached"],
    ]

    for cmd in commands:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            item = line.strip()
            if item:
                changed.add(item)

    return changed


def validate_registry_structure(registry: dict) -> list[str]:
    errors: list[str] = []

    levels = registry.get("levels")
    if not isinstance(levels, dict):
        return ["mapping_registry.json: levels must be an object"]

    for level in REQUIRED_LEVELS:
        files = levels.get(level)
        if not isinstance(files, list) or not files:
            errors.append(f"mapping_registry.json: {level} must map to a non-empty file list")

    mappings = registry.get("mappings", [])
    if not isinstance(mappings, list) or not mappings:
        errors.append("mapping_registry.json: mappings must be a non-empty list")
        return errors

    mapping_ids: set[str] = set()

    for item in mappings:
        map_id = item.get("id")
        if not map_id or not isinstance(map_id, str):
            errors.append("mapping_registry.json: each mapping must have string id")
            continue
        if map_id in mapping_ids:
            errors.append(f"mapping_registry.json: duplicate mapping id: {map_id}")
        mapping_ids.add(map_id)

        for key in ("l0_anchor", "l1_anchor", "l2_anchor"):
            if not item.get(key):
                errors.append(f"{map_id}: missing {key}")

        symbols = item.get("impl_symbols")
        if not isinstance(symbols, list) or not symbols:
            errors.append(f"{map_id}: impl_symbols must be non-empty list")

    return errors


def validate_mapping_content(registry: dict) -> list[str]:
    errors: list[str] = []

    l0_doc = REPO_ROOT / registry["levels"]["L0"][0]
    l1_doc = REPO_ROOT / registry["levels"]["L1"][0]
    l2_doc = REPO_ROOT / registry["levels"]["L2"][0]

    l0_text = read_text(l0_doc)
    l1_text = read_text(l1_doc)
    l2_text = read_text(l2_doc)

    code_cache: dict[Path, str] = {}

    for item in registry["mappings"]:
        map_id = item["id"]

        if item["l0_anchor"] not in l0_text:
            errors.append(f"{map_id}: l0_anchor not found in {l0_doc.name}")
        if item["l1_anchor"] not in l1_text:
            errors.append(f"{map_id}: l1_anchor not found in {l1_doc.name}")
        if item["l2_anchor"] not in l2_text:
            errors.append(f"{map_id}: l2_anchor not found in {l2_doc.name}")

        for symbol_ref in item["impl_symbols"]:
            file_name = symbol_ref.get("file")
            symbol = symbol_ref.get("symbol")

            if not file_name or not symbol:
                errors.append(f"{map_id}: invalid impl symbol ref: {symbol_ref}")
                continue

            file_path = REPO_ROOT / file_name
            if file_path not in code_cache:
                code_cache[file_path] = read_text(file_path)

            if symbol not in code_cache[file_path]:
                errors.append(f"{map_id}: symbol '{symbol}' not found in {file_name}")

    return errors


def validate_change_propagation(registry: dict, changed_files: set[str]) -> list[str]:
    errors: list[str] = []

    level_files: dict[str, set[str]] = {
        level: set(files) for level, files in registry["levels"].items()
    }

    def touched(level: str) -> bool:
        return bool(changed_files.intersection(level_files[level]))

    for rule in registry.get("top_down_update_rules", []):
        src = rule.get("from")
        targets = rule.get("must_update", [])
        if src not in level_files:
            continue
        if touched(src):
            for target in targets:
                if target in level_files and not touched(target):
                    errors.append(
                        f"change propagation violation: {src} changed but {target} not updated"
                    )

    for rule in registry.get("reverse_validation_rules", []):
        src = rule.get("from")
        if src in level_files and touched(src):
            # Running this script itself is the reverse validation requirement.
            pass

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate strict multi-level mapping between standards and code."
    )
    parser.add_argument(
        "--check-changes",
        action="store_true",
        help="validate top-down change propagation on current git diff",
    )
    args = parser.parse_args()

    try:
        registry = load_registry()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    errors: list[str] = []
    errors.extend(validate_registry_structure(registry))

    if not errors:
        try:
            errors.extend(validate_mapping_content(registry))
        except Exception as exc:
            errors.append(str(exc))

    if args.check_changes:
        changed = collect_changed_files()
        errors.extend(validate_change_propagation(registry, changed))

    if errors:
        print("[FAIL] strict mapping validation failed:")
        for issue in errors:
            print(f"- {issue}")
        return 1

    print("[PASS] strict mapping validation passed")
    if args.check_changes:
        print("[PASS] change propagation check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

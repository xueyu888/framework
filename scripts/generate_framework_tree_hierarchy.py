from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from generate_module_hierarchy_html import render_html
from hierarchy_models import HierarchyEdge, HierarchyFrameworkGroup, HierarchyGraph, HierarchyNode
from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime

MODULE_ID_PATTERN = re.compile(
    r"^(?P<framework>[A-Za-z][A-Za-z0-9_]*)\.L(?P<level>\d+)\.M(?P<module>\d+)$"
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate framework tree views derived from canonical.json.")
    parser.add_argument(
        "--project-file",
        default=str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT)),
        help="path to the project.toml file",
    )
    parser.add_argument("--output-json", required=True, help="path to generated framework tree JSON")
    parser.add_argument("--output-html", required=True, help="path to generated framework tree HTML")
    return parser


def _parse_module_id(module_id: str) -> tuple[str, int, int]:
    match = MODULE_ID_PATTERN.fullmatch(module_id)
    if match is None:
        raise ValueError(f"invalid framework module id: {module_id}")
    return (
        match.group("framework"),
        int(match.group("level")),
        int(match.group("module")),
    )


def _find_first_h1_line(relative_file: str) -> int:
    file_path = REPO_ROOT / relative_file
    if not file_path.exists():
        return 1
    for index, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("# "):
            return index
    return 1


def _format_hover_items(
    entries: list[dict[str, object]],
    *,
    token_key: str,
    text_builder: Callable[[dict[str, object]], str],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for entry in entries:
        token = str(entry.get(token_key, "")).strip()
        if not token:
            continue
        text = text_builder(entry).strip()
        items.append({"token": token, "text": text or token})
    return items


def _framework_graph(canonical: dict[str, object]) -> HierarchyGraph:
    framework = canonical["framework"]
    if not isinstance(framework, dict):
        raise ValueError("canonical.framework must be an object")
    modules = framework["modules"]
    if not isinstance(modules, list):
        raise ValueError("canonical.framework.modules must be a list")

    ordered_modules: list[tuple[str, int, int, dict[str, object]]] = []
    for item in modules:
        if not isinstance(item, dict):
            continue
        module_id = str(item["module_id"])
        framework_name, level_num, module_num = _parse_module_id(module_id)
        ordered_modules.append((framework_name, level_num, module_num, item))
    ordered_modules.sort(key=lambda item: (item[0], item[1], item[2]))

    nodes: list[HierarchyNode] = []
    edges: list[HierarchyEdge] = []
    framework_level_counts: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    for framework_name, level_num, module_num, item in ordered_modules:
        module_id = str(item["module_id"])
        framework_file = str(item["framework_file"])
        doc_line = _find_first_h1_line(framework_file)
        title_cn = str(item.get("title_cn") or "")
        title_en = str(item.get("title_en") or "")
        capabilities = item.get("capabilities")
        bases = item.get("bases")

        capability_items = _format_hover_items(
            [entry for entry in capabilities if isinstance(entry, dict)] if isinstance(capabilities, list) else [],
            token_key="capability_id",
            text_builder=lambda entry: "：".join(
                part for part in [str(entry.get("name") or "").strip(), str(entry.get("statement") or "").strip()] if part
            ),
        )
        base_items = _format_hover_items(
            [entry for entry in bases if isinstance(entry, dict)] if isinstance(bases, list) else [],
            token_key="base_id",
            text_builder=lambda entry: "：".join(
                part for part in [str(entry.get("name") or "").strip(), str(entry.get("statement") or "").strip()] if part
            ),
        )

        title_text = title_cn or title_en or module_id
        description_parts = [
            f"module={framework_name}",
            f"level=L{level_num}",
            f"node=L{level_num}.M{module_num}",
            f"file={framework_file}",
            f"title={title_text}",
        ]
        nodes.append(
            HierarchyNode(
                node_id=module_id,
                label=f"L{level_num}.{framework_name}.M{module_num}",
                level=level_num,
                order=module_num,
                description=" | ".join(description_parts),
                metadata={
                    "doc_line": doc_line,
                    "source_file": framework_file,
                    "source_line": doc_line,
                    "node_kind": "framework_module",
                    "module_name": framework_name,
                    "module_ref": f"L{level_num}.M{module_num}",
                    "module_title": title_text,
                    "capability_items": capability_items,
                    "base_items": base_items,
                    "hover_kicker": "Framework Module",
                },
            )
        )
        framework_level_counts[framework_name][level_num] += 1

        export_surface = item.get("export_surface", {})
        if not isinstance(export_surface, dict):
            continue
        for upstream in export_surface.get("upstream_module_ids", []):
            upstream_id = str(upstream)
            upstream_framework, upstream_level, upstream_module = _parse_module_id(upstream_id)
            edges.append(
                HierarchyEdge(
                    source=upstream_id,
                    target=module_id,
                    relation="framework_module_growth",
                    metadata={
                        "module": framework_name,
                        "from_level": f"L{upstream_level}",
                        "to_level": f"L{level_num}",
                        "source_ref": f"{upstream_framework}.L{upstream_level}.M{upstream_module}",
                        "target_ref": f"{framework_name}.L{level_num}.M{module_num}",
                        "terms": upstream_id,
                        "source_file": framework_file,
                        "source_line": doc_line,
                    },
                )
            )

    framework_names = sorted(framework_level_counts)
    framework_groups = [
        HierarchyFrameworkGroup(
            name=framework_name,
            order=index,
            local_levels=sorted(framework_level_counts[framework_name]),
            level_node_counts=dict(sorted(framework_level_counts[framework_name].items())),
        )
        for index, framework_name in enumerate(framework_names)
    ]

    level_labels = {
        level: f"L{level} 标准层"
        for level in sorted({node.level for node in nodes})
    }
    return HierarchyGraph(
        title="Shelf Framework Tree",
        description=(
            "从 canonical.framework.modules 派生，沿用旧框架树的交互式画布，仅恢复图形层；"
            "每个节点对应一个 framework markdown 模块，边表示显式上游模块引用。"
        ),
        foot_text="图中按 framework 分组展示模块关系；每个分组内部保留自己的本地 Lx 层。",
        level_labels=level_labels,
        nodes=nodes,
        edges=edges,
        layout_mode="framework_columns",
        framework_groups=framework_groups,
        storage_key_stem="frameworkTree",
    )


def main() -> int:
    args = _build_parser().parse_args()
    assembly = materialize_project_runtime(args.project_file)
    graph = _framework_graph(assembly.canonical)
    payload = graph.to_payload_dict()
    output_json = Path(args.output_json)
    output_html = Path(args.output_html)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_html(graph, output_html, width=1680, height=1080)
    print(f"[OK] framework tree JSON generated: {output_json}")
    print(f"[OK] framework tree HTML generated: {output_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

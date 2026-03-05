from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODULE = "frontend"
DEFAULT_FRAMEWORK_ROOT = REPO_ROOT / "framework"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/hierarchy/shelf_spec_frontend_hierarchy.json"
DEFAULT_OUTPUT_HTML = REPO_ROOT / "docs/hierarchy/shelf_spec_frontend_hierarchy.html"

FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN = re.compile(r"^L(\d+)-[^/]+\.md$")
BASE_TAG_PATTERN = re.compile(r"<!--\s*@base\s+([^>]*)-->", re.IGNORECASE)
COMPOSE_TAG_PATTERN = re.compile(r"<!--\s*@compose\s+([^>]*)-->", re.IGNORECASE)
BASE_ID_PATTERN = re.compile(r"^B(\d+)$")
NODE_ID_PATTERN = re.compile(r"^L(\d+)\.M([A-Za-z0-9_-]+)\.B(\d+)$")


@dataclass(frozen=True)
class LayerFile:
    module: str
    level: int
    path: Path


@dataclass(frozen=True)
class BaseNode:
    module: str
    level: int
    base_index: int
    file: Path
    line: int

    @property
    def node_id(self) -> str:
        return f"L{self.level}.M{self.module}.B{self.base_index}"


@dataclass(frozen=True)
class ComposeEdge:
    source: str
    target: str
    file: Path
    line: int
    rule: str
    principle: str
    constraint: str


def parse_tag_attributes(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for part in raw.split(";"):
        token = part.strip()
        if not token or "=" not in token:
            continue
        key, value = token.split("=", 1)
        attrs[key.strip()] = value.strip().strip('"').strip("'")
    return attrs


def line_from_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def discover_layer_files(framework_root: Path, module: str) -> list[LayerFile]:
    module_root = framework_root / module
    if not module_root.exists():
        raise FileNotFoundError(f"module root not found: {module_root}")

    layer_files: list[LayerFile] = []
    for markdown in sorted(module_root.glob("*.md")):
        match = FRAMEWORK_FILE_LEVEL_PREFIX_PATTERN.fullmatch(markdown.name)
        if match is None:
            continue
        level_num = int(match.group(1))
        layer_files.append(LayerFile(module=module, level=level_num, path=markdown))

    if not layer_files:
        raise ValueError(f"no markdown layer files found under {module_root}")

    return layer_files


def extract_nodes_and_edges(layer_files: list[LayerFile], module: str) -> tuple[list[BaseNode], list[ComposeEdge]]:
    bases: dict[str, BaseNode] = {}
    edges: list[ComposeEdge] = []

    for layer_file in layer_files:
        text = layer_file.path.read_text(encoding="utf-8")
        for base_match in BASE_TAG_PATTERN.finditer(text):
            attrs = parse_tag_attributes(base_match.group(1))
            base_id = attrs.get("id")
            base_match_obj = BASE_ID_PATTERN.fullmatch(base_id or "")
            if not base_id or base_match_obj is None:
                raise ValueError(
                    f"invalid @base id in {layer_file.path.relative_to(REPO_ROOT)} "
                    f"at line {line_from_offset(text, base_match.start())}: {base_id}"
                )
            base_index = int(base_match_obj.group(1))
            node = BaseNode(
                module=module,
                level=layer_file.level,
                base_index=base_index,
                file=layer_file.path,
                line=line_from_offset(text, base_match.start()),
            )
            if node.node_id in bases:
                raise ValueError(f"duplicate base node id: {node.node_id}")
            bases[node.node_id] = node

        for compose_match in COMPOSE_TAG_PATTERN.finditer(text):
            attrs = parse_tag_attributes(compose_match.group(1))
            src = attrs.get("from")
            dst = attrs.get("to")
            if not src or not dst:
                raise ValueError(
                    f"@compose missing from/to in {layer_file.path.relative_to(REPO_ROOT)} "
                    f"at line {line_from_offset(text, compose_match.start())}"
                )
            edges.append(
                ComposeEdge(
                    source=src,
                    target=dst,
                    file=layer_file.path,
                    line=line_from_offset(text, compose_match.start()),
                    rule=attrs.get("rule", ""),
                    principle=attrs.get("principle", ""),
                    constraint=attrs.get("constraint", ""),
                )
            )

    for edge in edges:
        src_match = NODE_ID_PATTERN.fullmatch(edge.source)
        dst_match = NODE_ID_PATTERN.fullmatch(edge.target)
        if src_match is None or dst_match is None:
            raise ValueError(
                f"invalid compose node id in {edge.file.relative_to(REPO_ROOT)}:{edge.line}: "
                f"{edge.source} -> {edge.target}"
            )

        src_level, src_module = int(src_match.group(1)), src_match.group(2)
        dst_level, dst_module = int(dst_match.group(1)), dst_match.group(2)

        if src_module != module or dst_module != module:
            raise ValueError(
                f"cross-module compose edge is not allowed: {edge.source} -> {edge.target}"
            )
        if dst_level != src_level + 1:
            raise ValueError(
                f"compose edge must be adjacent level (Lx->L(x+1)): {edge.source} -> {edge.target}"
            )
        if edge.source not in bases:
            raise ValueError(f"compose source base missing: {edge.source}")
        if edge.target not in bases:
            raise ValueError(f"compose target base missing: {edge.target}")

    return sorted(bases.values(), key=lambda item: (item.level, item.base_index, item.node_id)), edges


def build_hierarchy_payload(module: str, layer_files: list[LayerFile], base_nodes: list[BaseNode], compose_edges: list[ComposeEdge]) -> dict[str, Any]:
    levels = sorted({item.level for item in layer_files})
    max_level = max(levels)

    level_to_files: dict[int, list[LayerFile]] = {}
    for layer_file in layer_files:
        level_to_files.setdefault(layer_file.level, []).append(layer_file)

    level_to_bases: dict[int, list[BaseNode]] = {}
    for base_node in base_nodes:
        level_to_bases.setdefault(base_node.level, []).append(base_node)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for level in sorted(level_to_bases.keys(), reverse=True):
        graph_level = max_level - level
        sorted_bases = sorted(level_to_bases[level], key=lambda item: item.base_index)
        level_files = " | ".join(
            layer_file.path.relative_to(REPO_ROOT).as_posix()
            for layer_file in level_to_files.get(level, [])
        )
        for idx, base in enumerate(sorted_bases, start=1):
            nodes.append(
                {
                    "id": f"BASE::{base.node_id}",
                    "label": f"L{base.level}.B{base.base_index}",
                    "level": graph_level,
                    "order": idx,
                    "description": (
                        f"node={base.node_id} | {base.file.relative_to(REPO_ROOT).as_posix()}:{base.line}"
                        + (f" | layer_file={level_files}" if level_files else "")
                    ),
                }
            )

    for compose in compose_edges:
        edges.append(
            {
                "from": f"BASE::{compose.source}",
                "to": f"BASE::{compose.target}",
                "relation": "compose",
                "rule": compose.rule,
                "principle": compose.principle,
                "constraint": compose.constraint,
                "source_file": compose.file.relative_to(REPO_ROOT).as_posix(),
                "source_line": compose.line,
            }
        )

    level_labels = {
        str(max_level - level): f"L{level} 模块层" for level in sorted(level_to_files.keys(), reverse=True)
    }

    root = {
        "title": f"{module} 模块基组合图（基于 framework 自动抽取）",
        "description": (
            "从 framework/<module>/Lx 目录自动抽取层级，"
            "仅展示基节点 L{X}.M{module}.B{n} 及跨层 compose 关系；"
            "不展示同层 contains/layer_next 辅助边。"
        ),
        "level_labels": level_labels,
        "nodes": nodes,
        "edges": edges,
    }
    return {"root": root}


def render_html_from_json(input_json: Path, output_html: Path, width: int, height: int) -> None:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/generate_module_hierarchy_html.py"),
        "--input",
        str(input_json),
        "--output",
        str(output_html),
        "--width",
        str(width),
        "--height",
        str(height),
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-extract module hierarchy from framework/<module>/Lx and render graph.",
    )
    parser.add_argument("--module", type=str, default=DEFAULT_MODULE, help="Module name under framework/")
    parser.add_argument(
        "--framework-root",
        type=Path,
        default=DEFAULT_FRAMEWORK_ROOT,
        help="Framework root directory",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Output JSON path in hierarchy schema",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="Output HTML graph path",
    )
    parser.add_argument("--width", type=int, default=1680, help="SVG width for rendered HTML")
    parser.add_argument("--height", type=int, default=1180, help="SVG height for rendered HTML")
    parser.add_argument("--skip-html", action="store_true", help="Only generate JSON, skip HTML rendering")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = args.module.strip()
    if not module:
        raise ValueError("module must be non-empty")

    framework_root = args.framework_root
    if not framework_root.is_absolute():
        framework_root = (REPO_ROOT / framework_root).resolve()

    output_json = args.output_json
    if not output_json.is_absolute():
        output_json = (REPO_ROOT / output_json).resolve()

    output_html = args.output_html
    if not output_html.is_absolute():
        output_html = (REPO_ROOT / output_html).resolve()

    layer_files = discover_layer_files(framework_root, module)
    base_nodes, compose_edges = extract_nodes_and_edges(layer_files, module)
    payload = build_hierarchy_payload(module, layer_files, base_nodes, compose_edges)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] hierarchy JSON generated: {output_json}")

    if not args.skip_html:
        render_html_from_json(
            input_json=output_json,
            output_html=output_html,
            width=args.width,
            height=args.height,
        )
        print(f"[OK] hierarchy HTML generated: {output_html}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
LEVEL_PATTERN = re.compile(r"^L(\d+)$")
TAG_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


@dataclass(frozen=True)
class BaseDefinition:
    title: str
    name: str
    capability: str


def normalize_module(module: str) -> str:
    module_clean = module.strip()
    if MODULE_PATTERN.fullmatch(module_clean) is None:
        raise ValueError(
            "module must match [A-Za-z0-9_-], for example: frontend or shelf"
        )
    return module_clean


def parse_level(level: str) -> int:
    level_clean = level.strip().upper()
    match = LEVEL_PATTERN.fullmatch(level_clean)
    if match is None:
        raise ValueError("level must be in form L<number>, for example: L4")
    return int(match.group(1))


def normalize_level(level: str) -> str:
    return f"L{parse_level(level)}"


def parse_tag_token(raw: str, field_name: str) -> str:
    value = raw.strip()
    if TAG_TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must match [A-Za-z0-9_], got: {raw}")
    return value


def parse_base_definition(raw: str) -> BaseDefinition:
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError(
            "each --base must be '中文标题|TAG_NAME|capability', "
            f"got: {raw}"
        )
    title, tag_name, capability = parts
    return BaseDefinition(
        title=title,
        name=parse_tag_token(tag_name, "base tag name"),
        capability=parse_tag_token(capability, "base capability"),
    )


def default_base_definitions(base_count: int) -> list[BaseDefinition]:
    if base_count < 1:
        raise ValueError("base-count must be >= 1")
    return [
        BaseDefinition(
            title=f"待定义能力基{i}",
            name=f"BASE_{i}",
            capability=f"todo_capability_{i}",
        )
        for i in range(1, base_count + 1)
    ]


def resolve_upstream_level(level_num: int, upstream_level: str | None) -> str | None:
    if upstream_level is None:
        if level_num >= 7:
            return None
        return f"L{level_num + 1}"

    upstream_num = parse_level(upstream_level)
    expected = level_num + 1
    if upstream_num != expected:
        raise ValueError(
            f"upstream-level must be adjacent to source level: expected L{expected}, got L{upstream_num}"
        )
    return f"L{upstream_num}"


def build_framework_scaffold(
    module: str,
    module_display: str,
    level: str,
    title: str,
    subtitle: str,
    bases: Sequence[BaseDefinition],
    upstream_level: str | None = None,
) -> str:
    level_num = parse_level(level)
    normalized_level = f"L{level_num}"
    upstream = resolve_upstream_level(level_num, upstream_level)

    lines: list[str] = [
        f"# {module_display}框架模块标准（{normalized_level}）{title}",
        f"<!--@layer module={module}; level={normalized_level}-->",
        "",
        "## 1. 目标（Goal）",
        "",
        f"- 小标题：{subtitle}",
        "",
        "请补充本层目标正文。",
        "",
        "## 2. 边界定义（Boundary）",
        "",
        "- 小标题：定义该层负责什么、不负责什么。",
        "- `TODO_SCOPE`：待补充边界定义。",
        "",
        "## 3. 最小可行基（Bases）",
        "",
        "- 小标题：列出最小能力基并补全 `@base` 元数据。",
    ]

    for idx, base in enumerate(bases, start=1):
        lines.append(
            f"- `B{idx}` {base.title}  <!--@base id=B{idx}; name={base.name}; capability={base.capability}-->"
        )

    lines.extend(
        [
            "",
            "## 4. 组合原则（Combination Principles）",
            "",
            "- 小标题：描述组合方向、约束和映射示例。",
        ]
    )

    if upstream is None:
        downstream_level = f"L{level_num - 1}" if level_num > 0 else "下游层"
        lines.extend(
            [
                f"`{normalized_level}` 为模块上游根层，仅接收来自 `{downstream_level}` 的组合，不向更高层输出。",
                "",
                "## 5. 验证（Verification）",
                "",
                "- 小标题：给出可执行的验收门禁。",
                f"- 所有进入 `{normalized_level}` 的边必须来自 `{downstream_level}`。",
                f"- `{normalized_level}` 节点数量应少于 `{downstream_level}`（树顶收敛）。",
                "- 验证证据必须能回溯到下游链路。",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            f"仅允许下游向上游组合：`{normalized_level} -> {upstream}`。禁止同层组合与反向组合。",
            "",
            "组合约束集合：",
            "- `C1` 相邻层约束",
            "- `C2` 下游上行约束",
            "- `C3` 能力契约约束",
            "",
            "组合映射（示例）：",
        ]
    )

    if len(bases) >= 2:
        lines.append(f"- `U1 = {{{normalized_level}.B1, {normalized_level}.B2}} --[C1,C2,C3]--> {upstream}.B1`")
    else:
        lines.append(f"- `U1 = {{{normalized_level}.B1}} --[C1,C2,C3]--> {upstream}.B1`")

    lines.extend(
        [
            "",
            (
                f"- 待补充组合关系。  <!--@compose from={normalized_level}.M{module}.B1; "
                f"to={upstream}.M{module}.B1; rule=adjacent_only; "
                "principle=P_DOWNSTREAM_UPSTREAM; constraint=C1_C2_C3-->"
            ),
            "",
            "## 5. 验证（Verification）",
            "",
            "- 小标题：定义可执行验证条件。",
            f"- 每个 `{normalized_level}` 基必须至少指向一个 `{upstream}` 父节点。",
            f"- 每个 `{upstream}` 基必须至少由一个 `{normalized_level}` 子节点支撑。",
            "- 不允许同层或跨层跳级组合。",
        ]
    )
    return "\n".join(lines) + "\n"


def resolve_output_path(output: str | None, module: str, level: str, title: str) -> Path:
    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
        return output_path
    return REPO_ROOT / "framework" / module / f"{level}-{title}.md"


def write_output(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ValueError(
            f"output already exists: {path}. Use --overwrite to replace."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a framework layer markdown scaffold with required section headings, "
            "@layer/@base tags and compose placeholder."
        )
    )
    parser.add_argument("--module", required=True, help="module id used in canonical node id, e.g. frontend")
    parser.add_argument("--module-display", help="display name used in markdown title, defaults to module")
    parser.add_argument("--level", required=True, help="layer level, e.g. L4")
    parser.add_argument("--title", required=True, help="markdown file title suffix")
    parser.add_argument(
        "--subtitle",
        default="一句话描述该层要解决的问题。",
        help="small subtitle used under Goal section",
    )
    parser.add_argument(
        "--base",
        action="append",
        default=[],
        help="custom base definition: 标题|TAG_NAME|capability (repeatable)",
    )
    parser.add_argument(
        "--base-count",
        type=int,
        default=3,
        help="placeholder base count when --base is not provided",
    )
    parser.add_argument(
        "--upstream-level",
        help="optional explicit upstream level. Must be adjacent, e.g. L5 for source L4.",
    )
    parser.add_argument(
        "--output",
        help="output markdown path. Defaults to framework/<module>/<level>-<title>.md",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite output file if it already exists",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print scaffold to stdout and skip file write",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        module = normalize_module(args.module)
        level = normalize_level(args.level)
        bases = (
            [parse_base_definition(raw) for raw in args.base]
            if args.base
            else default_base_definitions(args.base_count)
        )
        module_display = args.module_display.strip() if args.module_display else module
        scaffold = build_framework_scaffold(
            module=module,
            module_display=module_display,
            level=level,
            title=args.title.strip(),
            subtitle=args.subtitle.strip(),
            bases=bases,
            upstream_level=args.upstream_level,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.stdout:
        sys.stdout.write(scaffold)
        return 0

    try:
        output_path = resolve_output_path(args.output, module, level, args.title.strip())
        write_output(output_path, scaffold, overwrite=bool(args.overwrite))
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    try:
        display_path = output_path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        display_path = str(output_path)
    print(f"[OK] generated scaffold: {display_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

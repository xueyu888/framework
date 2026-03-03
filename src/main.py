from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
import json
from pathlib import Path
from typing import Any

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
    modules_to_list,
    strict_mapping_meta,
    verify,
)


FOOTPRINT_AREA = 4
MAX_LAYERS = 2
GRID_WIDTH = 2
GRID_DEPTH = 2
CORNER_GRID_WIDTH = GRID_WIDTH + 1
CORNER_GRID_DEPTH = GRID_DEPTH + 1
PANEL_CELL_COUNT = GRID_WIDTH * GRID_DEPTH
CORNER_COUNT = CORNER_GRID_WIDTH * CORNER_GRID_DEPTH
BASELINE_EFFICIENCY = 1.0

REPORT_PATH = Path("docs/shelf_visualization_report.md")
DASHBOARD_PATH = Path("docs/shelf_visualization_dashboard.html")
DATA_PATH = Path("docs/shelf_visualization_data.json")
PLOTLY_BUNDLE_PATH = Path("docs/vendor/plotly.min.js")

MODULE_VALUE_TO_CN = {
    Module.ROD.value: "杆",
    Module.PANEL.value: "隔板",
    Module.CONNECTOR.value: "连接件",
}


def modules_label_cn(modules: list[str]) -> str:
    if not modules:
        return "空组合"
    return "+".join(MODULE_VALUE_TO_CN.get(item, item) for item in modules)


@dataclass(frozen=True)
class InstanceState:
    state_id: str
    panel_masks: tuple[int, int]
    rod_masks: tuple[int, int]
    connectors_per_layer: tuple[int, int]
    cells_per_layer: tuple[int, int]
    rods_per_layer: tuple[int, int]
    active_layers: int
    total_cells: int
    total_rods: int
    total_connectors: int
    overlap_cells: int
    projection_ratio: float
    group_key: str
    r3_rod_grounded: bool
    r3_panel_supported: bool
    unsupported_cells_per_layer: tuple[tuple[int, ...], tuple[int, ...]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "type_id": self.state_id,
            "panel_masks": list(self.panel_masks),
            "rod_masks": list(self.rod_masks),
            "connectors_per_layer": list(self.connectors_per_layer),
            "cells_per_layer": list(self.cells_per_layer),
            "rods_per_layer": list(self.rods_per_layer),
            "active_layers": self.active_layers,
            "total_cells": self.total_cells,
            "total_rods": self.total_rods,
            "total_connectors": self.total_connectors,
            "overlap_cells": self.overlap_cells,
            "projection_ratio": self.projection_ratio,
            "group_key": self.group_key,
            "r3_rod_grounded": self.r3_rod_grounded,
            "r3_panel_supported": self.r3_panel_supported,
            "unsupported_cells_per_layer": [
                list(self.unsupported_cells_per_layer[0]),
                list(self.unsupported_cells_per_layer[1]),
            ],
            # Deprecated compatibility fields retained for existing consumers.
            "layer_masks": list(self.panel_masks),
        }


@dataclass(frozen=True)
class ComboOption:
    combo_id: str
    combo: set[Module]
    modules: list[str]
    label: str
    label_cn: str
    rule_valid: bool
    rule_fail_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "combo_id": self.combo_id,
            "modules": self.modules,
            "label": self.label,
            "label_cn": self.label_cn,
            "rule_valid": self.rule_valid,
            "rule_fail_reasons": self.rule_fail_reasons,
        }


def build_logic_record(goal: Goal, boundary: BoundaryDefinition, result_ok: bool) -> LogicRecord:
    """构建可追溯逻辑记录，用于输出 L3 证据文件。"""
    steps = [
        LogicStep("G", "目标", evidence=goal.to_dict()),
        LogicStep("B1", "层数", ["G"], {"N": boundary.layers_n}),
        LogicStep("B2", "载荷", ["G"], {"P": boundary.payload_p_per_layer}),
        LogicStep("B3", "空间", ["G"], {"S": boundary.space_s_per_layer.__dict__}),
        LogicStep("B4", "开口", ["G"], {"O": boundary.opening_o.__dict__}),
        LogicStep("B5", "占地", ["G"], {"A": boundary.footprint_a.__dict__}),
        LogicStep("M1", "杆", ["B1", "B2"]),
        LogicStep("M2", "连接件", ["M1"]),
        LogicStep("M3", "隔板", ["B2", "B3"]),
        LogicStep("R1", "模块集合不应孤立", ["M1", "M2", "M3"]),
        LogicStep("R2", "连接件由杆与隔板接触自动派生", ["M1", "M3"]),
        LogicStep("R3", "杆不可悬浮且隔板需要四角支撑", ["M1", "M3"]),
        LogicStep("R5", "顶层至少包含一个隔板单元", ["M3"]),
        LogicStep("H1", "在有效约束下效率应提升", ["R1", "R2", "R3", "R5"]),
        LogicStep("V1", "验证假设", ["H1"], {"passed": result_ok}),
        LogicStep("C", "结论", ["V1"], {"adopt_now": result_ok}),
    ]
    return LogicRecord.build(steps)


def bit_count(mask: int) -> int:
    return int(mask).bit_count()


def panel_cell_indices(mask: int) -> list[int]:
    return [idx for idx in range(PANEL_CELL_COUNT) if mask & (1 << idx)]


def corner_index(x: int, y: int) -> int:
    return y * CORNER_GRID_WIDTH + x


def corner_xy(index: int) -> tuple[int, int]:
    return index % CORNER_GRID_WIDTH, index // CORNER_GRID_WIDTH


def panel_cell_to_corner_indices(cell_idx: int) -> tuple[int, int, int, int]:
    x = cell_idx % GRID_WIDTH
    y = cell_idx // GRID_WIDTH
    return (
        corner_index(x, y),
        corner_index(x + 1, y),
        corner_index(x, y + 1),
        corner_index(x + 1, y + 1),
    )


def corners_mask_for_panel_mask(panel_mask: int) -> int:
    mask = 0
    for cell_idx in panel_cell_indices(panel_mask):
        for idx in panel_cell_to_corner_indices(cell_idx):
            mask |= 1 << idx
    return mask


def unsupported_cells(panel_mask: int, rod_mask: int) -> list[int]:
    unsupported: list[int] = []
    for cell_idx in panel_cell_indices(panel_mask):
        corners = panel_cell_to_corner_indices(cell_idx)
        if any((rod_mask & (1 << idx)) == 0 for idx in corners):
            unsupported.append(cell_idx)
    return unsupported


def connector_contacts(panel_mask: int, rod_mask: int) -> int:
    count = 0
    for cell_idx in panel_cell_indices(panel_mask):
        for idx in panel_cell_to_corner_indices(cell_idx):
            if rod_mask & (1 << idx):
                count += 1
    return count


def enumerate_instance_states(footprint_area: int, max_layers: int) -> list[InstanceState]:
    if footprint_area != GRID_WIDTH * GRID_DEPTH:
        raise ValueError("当前可视化仅支持 2x2 占地网格（面积必须为 4）。")
    if max_layers != 2:
        raise ValueError("当前可视化仅支持 max_layers == 2。")

    states: list[InstanceState] = []
    state_index = 0

    for panel_l1_mask, panel_l2_mask in product(range(1 << PANEL_CELL_COUNT), repeat=max_layers):
        if panel_l1_mask == 0 and panel_l2_mask == 0:
            continue

        # Immediate pruning of physically impossible rod states by construction:
        # layer-2 rods are only generated when the corresponding layer-1 rods exist.
        rod_l2_mask = corners_mask_for_panel_mask(panel_l2_mask)
        rod_l1_mask = corners_mask_for_panel_mask(panel_l1_mask) | rod_l2_mask

        unsupported_l1 = unsupported_cells(panel_l1_mask, rod_l1_mask)
        unsupported_l2 = unsupported_cells(panel_l2_mask, rod_l2_mask)
        r3_rod_grounded = (rod_l2_mask & ~rod_l1_mask) == 0
        r3_panel_supported = len(unsupported_l1) == 0 and len(unsupported_l2) == 0

        connectors_l1 = connector_contacts(panel_l1_mask, rod_l1_mask)
        connectors_l2 = connector_contacts(panel_l2_mask, rod_l2_mask)

        cells_per_layer = (bit_count(panel_l1_mask), bit_count(panel_l2_mask))
        rods_per_layer = (bit_count(rod_l1_mask), bit_count(rod_l2_mask))
        active_layers = sum(1 for cells in cells_per_layer if cells > 0)
        total_cells = sum(cells_per_layer)
        total_rods = sum(rods_per_layer)
        total_connectors = connectors_l1 + connectors_l2
        overlap_cells = bit_count(panel_l1_mask & panel_l2_mask)
        projection_ratio = total_cells / float(FOOTPRINT_AREA)
        group_key = f"cells/layer={cells_per_layer}"

        states.append(
            InstanceState(
                state_id=f"T{state_index:03d}",
                panel_masks=(panel_l1_mask, panel_l2_mask),
                rod_masks=(rod_l1_mask, rod_l2_mask),
                connectors_per_layer=(connectors_l1, connectors_l2),
                cells_per_layer=cells_per_layer,
                rods_per_layer=rods_per_layer,
                active_layers=active_layers,
                total_cells=total_cells,
                total_rods=total_rods,
                total_connectors=total_connectors,
                overlap_cells=overlap_cells,
                projection_ratio=projection_ratio,
                group_key=group_key,
                r3_rod_grounded=r3_rod_grounded,
                r3_panel_supported=r3_panel_supported,
                unsupported_cells_per_layer=(tuple(unsupported_l1), tuple(unsupported_l2)),
            )
        )
        state_index += 1

    return states


def validate_boundary_target(
    boundary: BoundaryDefinition, required_area: float, max_layers: int
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    area = boundary.footprint_a.width * boundary.footprint_a.depth

    if abs(area - required_area) > 1e-9:
        errors.append(f"占地面积必须等于 {required_area}，当前为 {area}")
    if boundary.layers_n > max_layers:
        errors.append(f"层数必须 <= {max_layers}，当前为 {boundary.layers_n}")

    return (len(errors) == 0, errors)


def to_combo_options(
    combos: list[set[Module]], rules: CombinationRules, prefix: str = "C"
) -> list[ComboOption]:
    ordered = sorted(combos, key=lambda combo: (len(combo), modules_to_list(combo)))
    options: list[ComboOption] = []
    for idx, combo in enumerate(ordered):
        modules = modules_to_list(combo)
        rule_valid, rule_fail_reasons = rules.evaluate(combo)
        options.append(
            ComboOption(
                combo_id=f"{prefix}{idx:02d}",
                combo=combo,
                modules=modules,
                label="+".join(modules),
                label_cn=modules_label_cn(modules),
                rule_valid=rule_valid,
                rule_fail_reasons=rule_fail_reasons,
            )
        )
    return options


def derived_combo_from_state(state: InstanceState) -> set[Module]:
    combo: set[Module] = set()
    if state.total_rods > 0:
        combo.add(Module.ROD)
    if state.total_cells > 0:
        combo.add(Module.PANEL)
    if state.total_connectors > 0:
        combo.add(Module.CONNECTOR)
    return combo


def append_unique(items: list[str], message: str) -> None:
    if message not in items:
        items.append(message)


def baseline_single_layer_efficiency(state: InstanceState) -> float:
    return max(state.cells_per_layer) / float(FOOTPRINT_AREA)


def evaluate_state(
    state: InstanceState,
    boundary: BoundaryDefinition,
    valid_combinations: list[set[Module]],
    rules: CombinationRules,
    boundary_target_ok: bool,
    boundary_target_errors: list[str],
) -> dict[str, Any]:
    combo = derived_combo_from_state(state)
    combo_modules = modules_to_list(combo)
    combo_label = "+".join(combo_modules)
    combo_label_cn = modules_label_cn(combo_modules)
    baseline_efficiency = baseline_single_layer_efficiency(state)
    target_efficiency = state.projection_ratio
    rule_valid, rule_fail_reasons = rules.evaluate(combo)

    verification_input = VerificationInput(
        boundary=boundary,
        combo=combo,
        valid_combinations=valid_combinations,
        baseline_efficiency=baseline_efficiency,
        target_efficiency=target_efficiency,
    )
    verification_result = verify(verification_input)

    r3_ok = state.r3_rod_grounded and state.r3_panel_supported
    r4_projection = target_efficiency > baseline_efficiency
    r5_top_closed = state.panel_masks[1] != 0

    reasons = list(boundary_target_errors)
    for reason in rule_fail_reasons:
        append_unique(reasons, reason)
    for reason in verification_result.reasons:
        append_unique(reasons, reason)
    if not state.r3_rod_grounded:
        append_unique(reasons, "R3 失败：上层杆必须由下层同坐标杆承接，不能悬浮")
    if not state.r3_panel_supported:
        append_unique(
            reasons,
            "R3 失败：每个隔板单元必须由同层 4 个杆角点完整支撑",
        )
    if not r4_projection:
        append_unique(
            reasons,
            f"R4 失败：总投影效率({target_efficiency:.2f}) 必须大于单层基准({baseline_efficiency:.2f})",
        )
    if not r5_top_closed:
        append_unique(reasons, "R5 失败：顶层（L2）必须至少包含 1 个隔板单元")

    passed = boundary_target_ok and verification_result.passed and r3_ok and r4_projection and r5_top_closed

    return {
        "combo_modules": combo_modules,
        "combo_label": combo_label,
        "combo_label_cn": combo_label_cn,
        "combo_valid": verification_result.combination_valid,
        "boundary_valid": verification_result.boundary_valid,
        "efficiency_improved": verification_result.efficiency_improved,
        "baseline_efficiency": baseline_efficiency,
        "target_efficiency": target_efficiency,
        "r3_rod_grounded": state.r3_rod_grounded,
        "r3_panel_supported": state.r3_panel_supported,
        "r3_unsupported_upper_cells": len(state.unsupported_cells_per_layer[1]),
        "r3_ok": r3_ok,
        "r4_projection": r4_projection,
        "r5_top_closed": r5_top_closed,
        "rule_valid": rule_valid,
        "rule_fail_reasons": rule_fail_reasons,
        "boundary_target_ok": boundary_target_ok,
        "passed": passed,
        "reasons": reasons,
    }


def parse_group_key(key: str) -> tuple[int, int]:
    raw = key.replace("cells/layer=", "").strip()
    left, right = raw.strip("()").split(",")
    return int(left.strip()), int(right.strip())


def enrich_states(
    states: list[InstanceState],
    boundary: BoundaryDefinition,
    rules: CombinationRules,
    valid_combinations: list[set[Module]],
    boundary_target_ok: bool,
    boundary_target_errors: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    state_records: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, Any]] = {}
    combo_distribution: dict[str, int] = {}

    for state in states:
        eval_data = evaluate_state(
            state=state,
            boundary=boundary,
            valid_combinations=valid_combinations,
            rules=rules,
            boundary_target_ok=boundary_target_ok,
            boundary_target_errors=boundary_target_errors,
        )

        record = state.to_dict()
        record.update(eval_data)
        record["canonical_passed"] = eval_data["passed"]
        record["canonical_reasons"] = eval_data["reasons"]
        state_records.append(record)

        combo_distribution[record["combo_label_cn"] or "空组合"] = (
            combo_distribution.get(record["combo_label_cn"] or "空组合", 0) + 1
        )

        group = grouped.setdefault(
            state.group_key,
            {
                "group_key": state.group_key,
                "state_ids": [],
                "type_ids": [],
                "total": 0,
                "passed": 0,
                "failed": 0,
            },
        )
        group["state_ids"].append(state.state_id)
        group["type_ids"].append(state.state_id)
        group["total"] += 1
        if eval_data["passed"]:
            group["passed"] += 1
        else:
            group["failed"] += 1

    groups = sorted(grouped.values(), key=lambda item: parse_group_key(item["group_key"]))
    state_to_group: dict[str, str] = {}
    for idx, group in enumerate(groups):
        group["group_id"] = f"G{idx:02d}"
        for state_id in group["state_ids"]:
            state_to_group[state_id] = group["group_id"]

    for record in state_records:
        record["group_id"] = state_to_group[record["state_id"]]

    passed_states = sum(1 for record in state_records if record["passed"])
    summary = {
        "total_states": len(state_records),
        "passed_states": passed_states,
        "failed_states": len(state_records) - passed_states,
        "pass_ratio": passed_states / len(state_records) if state_records else 0.0,
        "threshold_ratio": BASELINE_EFFICIENCY,
        "threshold_rule": "总投影比 > 单层投影比",
        # Compatibility aliases
        "total_types": len(state_records),
        "passed_types": passed_states,
        "failed_types": len(state_records) - passed_states,
        "canonical_combo_id": "DERIVED",
    }

    combo_rows = [
        {"combo_label": label, "count": count}
        for label, count in sorted(combo_distribution.items(), key=lambda item: (-item[1], item[0]))
    ]

    return state_records, groups, summary, combo_rows


def ensure_local_plotly_bundle(out_path: Path) -> None:
    import plotly

    source = Path(plotly.__file__).resolve().parent / "package_data" / "plotly.min.js"
    if not source.exists():
        raise FileNotFoundError(f"plotly bundle not found: {source}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = source.read_bytes()
    if not out_path.exists() or out_path.read_bytes() != source_bytes:
        out_path.write_bytes(source_bytes)


def build_dashboard_html(payload: dict[str, Any]) -> str:
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>置物架可视化报告</title>
  <script src="./vendor/plotly.min.js"></script>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap");
    :root {
      --bg-0: #f7f4ee;
      --bg-1: #ffffff;
      --ink-0: #1f2a36;
      --ink-1: #4f6172;
      --accent-a: #007f5f;
      --accent-b: #e76f51;
      --accent-c: #2a9d8f;
      --accent-d: #f4a261;
      --line: #d6dde5;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", sans-serif;
      color: var(--ink-0);
      background:
        radial-gradient(circle at 0% 0%, rgba(42,157,143,0.16), transparent 35%),
        radial-gradient(circle at 100% 0%, rgba(244,162,97,0.18), transparent 36%),
        linear-gradient(180deg, #fdfcf9 0%, #f6f3ed 100%);
    }
    main {
      width: min(1220px, 96vw);
      margin: 0 auto;
      padding: 22px 0 40px;
      animation: fade-up 520ms ease-out both;
    }
    @keyframes fade-up {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .hero {
      background: linear-gradient(140deg, rgba(0,127,95,0.1), rgba(244,162,97,0.18));
      border: 1px solid rgba(42,157,143,0.26);
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 16px;
    }
    h1, h2, h3 { margin: 0; }
    h1 { font-size: 1.4rem; letter-spacing: 0.01em; }
    .mono {
      font-family: "Space Mono", monospace;
      color: var(--ink-1);
      font-size: 0.9rem;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin: 16px 0;
    }
    .card {
      background: var(--bg-1);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      box-shadow: 0 5px 12px rgba(17, 24, 39, 0.04);
    }
    .card-title {
      font-size: 0.78rem;
      color: var(--ink-1);
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }
    .card-value {
      font-weight: 700;
      font-size: 1.4rem;
      margin-top: 4px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 12px;
    }
    .panel {
      background: var(--bg-1);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px;
      min-height: 320px;
    }
    .index-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }
    @media (max-width: 1000px) {
      .index-grid { grid-template-columns: 1fr; }
    }
    .group-list {
      border: 1px solid var(--line);
      border-radius: 10px;
      max-height: 320px;
      overflow: auto;
      background: #fff;
    }
    .group-row {
      display: grid;
      grid-template-columns: 58px 1fr 54px 54px;
      gap: 8px;
      align-items: center;
      padding: 8px 10px;
      border-bottom: 1px solid #eef2f5;
      cursor: pointer;
      font-size: 0.84rem;
    }
    .group-row:hover { background: #f8fbfe; }
    .group-row.active {
      background: #ebf6ff;
      outline: 1px solid #9cc8ef;
    }
    .state-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(186px, 1fr));
      gap: 8px;
      max-height: 320px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px;
      background: #fff;
    }
    .state-card {
      border: 1px solid #dce4eb;
      border-radius: 8px;
      background: #fbfdff;
      padding: 8px;
      cursor: pointer;
    }
    .state-card.active {
      outline: 2px solid #8fbbe6;
      background: #edf6ff;
    }
    .state-card h4 {
      margin: 0 0 6px 0;
      font-size: 0.84rem;
    }
    .state-card .meta {
      color: var(--ink-1);
      font-size: 0.74rem;
      margin-bottom: 6px;
      font-family: "Space Mono", monospace;
    }
    .mini-stack {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px;
    }
    .mini-layer {
      border: 1px solid #d5dce4;
      border-radius: 5px;
      padding: 4px;
    }
    .mini-label {
      font-size: 0.68rem;
      color: var(--ink-1);
      margin-bottom: 3px;
    }
    .mini-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 2px;
    }
    .mini-cell {
      height: 10px;
      border-radius: 2px;
      border: 1px solid #d9dce1;
      background: #f1f4f8;
    }
    .mini-cell.active {
      background: #f0aa63;
      border-color: #c58c55;
    }
    .detail {
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 12px;
    }
    @media (max-width: 900px) {
      .detail { grid-template-columns: 1fr; }
    }
    .stats-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(140px, 1fr));
      gap: 8px;
      margin-top: 8px;
    }
    .stat-item {
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #fcfcfc;
    }
    .stat-item small {
      display: block;
      color: var(--ink-1);
      font-size: 0.75rem;
      margin-bottom: 3px;
    }
    .stat-item strong {
      font-family: "Space Mono", monospace;
      font-size: 0.96rem;
    }
    .validation {
      border-radius: 10px;
      border: 1px solid var(--line);
      padding: 10px;
      min-height: 160px;
      background: #fffefb;
    }
    .status-pass { color: var(--accent-a); font-weight: 700; }
    .status-fail { color: var(--accent-b); font-weight: 700; }
    .reason-list {
      margin: 8px 0 0 0;
      padding-left: 18px;
      color: var(--ink-1);
      font-size: 0.88rem;
    }
    .layer-previews {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }
    .layer-box {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #f9fbfd;
    }
    .layer-box h4 {
      margin: 0 0 6px 0;
      font-size: 0.8rem;
      color: var(--ink-1);
    }
    .cell-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px;
    }
    .cell {
      height: 26px;
      border-radius: 4px;
      border: 1px solid #d8dbe0;
      background: #f1f4f8;
    }
    .cell.active {
      background: linear-gradient(135deg, rgba(244,162,97,0.9), rgba(231,111,81,0.78));
      border-color: rgba(204,109,80,0.9);
    }
    .rod-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 4px;
    }
    .rod-dot {
      height: 18px;
      border-radius: 50%;
      border: 1px solid #ccd4dc;
      background: #eef2f6;
    }
    .rod-dot.active {
      background: #1f67bb;
      border-color: #165091;
    }
    #structure3d {
      width: 100%;
      height: 520px;
    }
    .state-status-list {
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      max-height: 320px;
      overflow: auto;
      background: #fff;
    }
    .state-row {
      padding: 9px 10px;
      border-bottom: 1px solid #eef2f5;
      cursor: pointer;
      display: grid;
      grid-template-columns: 70px 120px 1fr 90px;
      gap: 8px;
      align-items: center;
      font-size: 0.84rem;
    }
    .state-row:hover { background: #f8fbfe; }
    .state-row.active {
      background: #ebf6ff;
      outline: 1px solid #9cc8ef;
    }
    .state-row small {
      color: var(--ink-1);
      font-family: "Space Mono", monospace;
    }
    .badge {
      border-radius: 999px;
      padding: 2px 8px;
      display: inline-block;
      text-align: center;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .badge-pass {
      color: #086e53;
      background: #d8f3ea;
      border: 1px solid #8fd5bd;
    }
    .badge-fail {
      color: #9f2d21;
      background: #fce1dc;
      border: 1px solid #efb4a8;
    }
  </style>
</head>
<body>
<main>
  <section class="hero">
    <h1>置物架分型可视化 | A=4, max_layers=2</h1>
    <p class="mono" id="heroMeta"></p>
  </section>

  <section class="cards">
    <article class="card"><div class="card-title">状态总数</div><div class="card-value" id="totalStates"></div></article>
    <article class="card"><div class="card-title">通过数</div><div class="card-value" id="passedStates"></div></article>
    <article class="card"><div class="card-title">失败数</div><div class="card-value" id="failedStates"></div></article>
    <article class="card"><div class="card-title">通过率</div><div class="card-value" id="passRatio"></div></article>
    <article class="card"><div class="card-title">分组数</div><div class="card-value" id="groupCount"></div></article>
    <article class="card"><div class="card-title">阈值</div><div class="card-value mono" id="threshold"></div></article>
  </section>

  <section class="grid">
    <article class="panel"><div id="passFailChart"></div></article>
    <article class="panel"><div id="ratioHistChart"></div></article>
    <article class="panel"><div id="groupChart"></div></article>
    <article class="panel"><div id="scatterChart"></div></article>
  </section>

  <section class="panel" style="margin-top: 12px;">
    <h2 style="font-size: 1rem;">3D 交互结构</h2>
    <p class="mono">可旋转 / 缩放查看当前状态的杆、连接件与隔板。</p>
    <div id="structure3d"></div>
  </section>

  <section class="panel" style="margin-top: 12px;">
    <h2 style="font-size: 1rem; margin-bottom: 10px;">类型浏览</h2>
    <div class="index-grid">
      <div>
        <h3 style="font-size: 0.95rem; margin-bottom: 8px;">类型子页（全部分组）</h3>
        <div class="group-list" id="groupList"></div>
      </div>
      <div>
        <h3 style="font-size: 0.95rem; margin-bottom: 8px;" id="groupDetailTitle"></h3>
        <div class="state-grid" id="stateCardGrid"></div>
      </div>
    </div>
    <div class="detail">
      <div>
        <h3 style="font-size: 0.95rem;">当前状态摘要</h3>
        <div class="stats-list" id="stateStats"></div>
        <div class="layer-previews" id="layerPreview"></div>
      </div>
      <div>
        <h3 style="font-size: 0.95rem;">边界 / 目标校验</h3>
        <div class="validation" id="validationBox"></div>
      </div>
    </div>
    <h3 style="font-size: 0.95rem; margin-top: 12px;">全部状态与结果（点击查看 3D）</h3>
    <div class="state-status-list" id="stateStatusList"></div>
  </section>
</main>

<script>
const DATA = __DATA_PAYLOAD__;
const states = DATA.states;
const stateById = new Map(states.map((state) => [state.state_id, state]));
const groupById = new Map(DATA.groups.map((group) => [group.group_id, group]));

const defaultState = [...states].sort((a, b) => {
  if (b.total_cells !== a.total_cells) return b.total_cells - a.total_cells;
  if (b.projection_ratio !== a.projection_ratio) return b.projection_ratio - a.projection_ratio;
  return a.state_id.localeCompare(b.state_id);
})[0];

let selectedGroupId = defaultState ? defaultState.group_id : (DATA.groups.length > 0 ? DATA.groups[0].group_id : "");
let selectedStateId = defaultState ? defaultState.state_id : "";

function toPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function initSummary() {
  document.getElementById("heroMeta").textContent =
    `目标=${DATA.goal.statement} | 边界有效=${DATA.boundary_check.boundary_valid} | 目标边界有效=${DATA.boundary_check.boundary_target_ok}`;

  document.getElementById("totalStates").textContent = DATA.summary.total_states;
  document.getElementById("passedStates").textContent = DATA.summary.passed_states;
  document.getElementById("failedStates").textContent = DATA.summary.failed_states;
  document.getElementById("passRatio").textContent = toPercent(DATA.summary.pass_ratio);
  document.getElementById("groupCount").textContent = DATA.groups.length;
  document.getElementById("threshold").textContent = DATA.summary.threshold_rule || "总投影比 > 单层投影比";
}

function drawOverviewCharts() {
  Plotly.newPlot(
    "passFailChart",
    [
      {
        type: "bar",
        x: ["passed", "failed"],
        y: [DATA.summary.passed_states, DATA.summary.failed_states],
        marker: { color: ["#007f5f", "#e76f51"] },
      },
    ],
    {
      margin: { t: 40, b: 40, l: 40, r: 10 },
      title: "总体通过/失败",
      yaxis: { title: "状态数" },
    },
    { responsive: true, displaylogo: false }
  );

  const passedRatios = states.filter((item) => item.passed).map((item) => item.projection_ratio);
  const failedRatios = states.filter((item) => !item.passed).map((item) => item.projection_ratio);

  Plotly.newPlot(
    "ratioHistChart",
    [
      {
        type: "histogram",
        name: "passed",
        x: passedRatios,
        marker: { color: "#2a9d8f" },
        opacity: 0.72,
      },
      {
        type: "histogram",
        name: "failed",
        x: failedRatios,
        marker: { color: "#e76f51" },
        opacity: 0.64,
      },
    ],
    {
      barmode: "overlay",
      margin: { t: 40, b: 40, l: 40, r: 10 },
      title: "投影比率分布",
      xaxis: { title: "投影比率" },
      yaxis: { title: "数量" },
      shapes: [],
    },
    { responsive: true, displaylogo: false }
  );

  Plotly.newPlot(
    "groupChart",
    [
      {
        type: "bar",
        name: "passed",
        x: DATA.groups.map((group) => group.group_id),
        y: DATA.groups.map((group) => group.passed),
        marker: { color: "#007f5f" },
      },
      {
        type: "bar",
        name: "failed",
        x: DATA.groups.map((group) => group.group_id),
        y: DATA.groups.map((group) => group.failed),
        marker: { color: "#e76f51" },
      },
    ],
    {
      barmode: "stack",
      margin: { t: 40, b: 40, l: 40, r: 10 },
      title: "分组通过/失败",
      xaxis: { title: "分组编号" },
      yaxis: { title: "状态数" },
    },
    { responsive: true, displaylogo: false }
  );

  Plotly.newPlot(
    "scatterChart",
    [
      {
        type: "scatter",
        mode: "markers",
        x: states.map((_, idx) => idx + 1),
        y: states.map((item) => item.projection_ratio),
        text: states.map((item) => `${item.state_id} ${item.group_id}`),
        marker: {
          size: 8,
          color: states.map((item) => (item.passed ? "#007f5f" : "#e76f51")),
        },
      },
    ],
    {
      margin: { t: 40, b: 40, l: 40, r: 10 },
      title: "状态级投影比率散点",
      xaxis: { title: "状态索引" },
      yaxis: { title: "投影比率" },
      shapes: [],
    },
    { responsive: true, displaylogo: false }
  );
}

function ensureSelection() {
  if (!selectedGroupId && DATA.groups.length > 0) {
    selectedGroupId = DATA.groups[0].group_id;
  }

  const group = groupById.get(selectedGroupId);
  if (!group || group.state_ids.length === 0) {
    selectedStateId = "";
    return;
  }

  if (!selectedStateId || !group.state_ids.includes(selectedStateId)) {
    selectedStateId = group.state_ids[0];
  }
}

function bits(mask, totalBits) {
  let count = 0;
  for (let idx = 0; idx < totalBits; idx += 1) {
    if ((mask & (1 << idx)) !== 0) count += 1;
  }
  return count;
}

function miniGridHtml(mask) {
  let html = "<div class='mini-grid'>";
  for (let y = 0; y < 2; y += 1) {
    for (let x = 0; x < 2; x += 1) {
      const index = y * 2 + x;
      const active = (mask & (1 << index)) !== 0;
      html += `<span class='mini-cell ${active ? "active" : ""}'></span>`;
    }
  }
  html += "</div>";
  return html;
}

function badge(ok) {
  return ok ? "<span class='badge badge-pass'>通过</span>" : "<span class='badge badge-fail'>失败</span>";
}

function groupLabel(groupKey) {
  return String(groupKey).replace("cells/layer=", "每层隔板数=");
}

function renderGroupList() {
  const root = document.getElementById("groupList");
  root.innerHTML = "";
  DATA.groups.forEach((group) => {
    const row = document.createElement("div");
    row.className = group.group_id === selectedGroupId ? "group-row active" : "group-row";
    row.innerHTML = `
      <small>${group.group_id}</small>
      <div>
        <div>${groupLabel(group.group_key)}</div>
        <small>状态=${group.total}</small>
      </div>
      <div>${group.passed}</div>
      <div>${group.failed}</div>
    `;
    row.addEventListener("click", () => {
      selectedGroupId = group.group_id;
      selectedStateId = group.state_ids[0] || "";
      renderGroupList();
      renderStateCards();
      renderSelection();
    });
    root.appendChild(row);
  });
}

function renderStateCards() {
  const root = document.getElementById("stateCardGrid");
  root.innerHTML = "";
  const group = groupById.get(selectedGroupId);
  if (!group) return;

  document.getElementById("groupDetailTitle").textContent =
    `${group.group_id} 类型组 | ${groupLabel(group.group_key)} | 总数=${group.total} | 通过=${group.passed}`;

  group.state_ids.forEach((stateId) => {
    const state = stateById.get(stateId);
    if (!state) return;

    const card = document.createElement("article");
    card.className = stateId === selectedStateId ? "state-card active" : "state-card";
    card.innerHTML = `
      <h4>${state.state_id}</h4>
      <div class="meta">投影=${state.projection_ratio.toFixed(2)} | 杆=${state.total_rods} | 连接=${state.total_connectors}</div>
      <div class="mini-stack">
        <div class="mini-layer">
          <div class="mini-label">L1 隔板=${bits(state.panel_masks[0], 4)}</div>
          ${miniGridHtml(state.panel_masks[0])}
        </div>
        <div class="mini-layer">
          <div class="mini-label">L2 隔板=${bits(state.panel_masks[1], 4)}</div>
          ${miniGridHtml(state.panel_masks[1])}
        </div>
      </div>
    `;
    card.addEventListener("click", () => {
      selectedStateId = stateId;
      renderStateCards();
      renderSelection();
    });
    root.appendChild(card);
  });
}

function initExplorer() {
  ensureSelection();
  renderGroupList();
  renderStateCards();
  renderSelection();
}

function renderPanelCells(mask, layerLabel) {
  const wrapper = document.createElement("div");
  wrapper.className = "layer-box";

  const title = document.createElement("h4");
  title.textContent = layerLabel;
  wrapper.appendChild(title);

  const grid = document.createElement("div");
  grid.className = "cell-grid";
  for (let y = 0; y < 2; y += 1) {
    for (let x = 0; x < 2; x += 1) {
      const index = y * 2 + x;
      const active = (mask & (1 << index)) !== 0;
      const cell = document.createElement("div");
      cell.className = active ? "cell active" : "cell";
      grid.appendChild(cell);
    }
  }
  wrapper.appendChild(grid);
  return wrapper;
}

function renderRodCorners(mask, layerLabel) {
  const wrapper = document.createElement("div");
  wrapper.className = "layer-box";

  const title = document.createElement("h4");
  title.textContent = layerLabel;
  wrapper.appendChild(title);

  const grid = document.createElement("div");
  grid.className = "rod-grid";
  for (let y = 0; y < 3; y += 1) {
    for (let x = 0; x < 3; x += 1) {
      const index = y * 3 + x;
      const active = (mask & (1 << index)) !== 0;
      const dot = document.createElement("div");
      dot.className = active ? "rod-dot active" : "rod-dot";
      grid.appendChild(dot);
    }
  }
  wrapper.appendChild(grid);
  return wrapper;
}

function renderSelection() {
  ensureSelection();
  const state = stateById.get(selectedStateId);
  if (!state) return;

  const stats = [
    ["状态编号", state.state_id],
    ["分组", `${state.group_id} | ${groupLabel(state.group_key)}`],
    ["隔板掩码", state.panel_masks.join(", ")],
    ["杆掩码", state.rod_masks.join(", ")],
    ["每层隔板数", state.cells_per_layer.join(", ")],
    ["每层杆数", state.rods_per_layer.join(", ")],
    ["每层连接数", state.connectors_per_layer.join(", ")],
    ["活跃层数", state.active_layers],
    ["隔板总数", state.total_cells],
    ["杆总数", state.total_rods],
    ["投影比率", state.projection_ratio.toFixed(2)],
    ["组合", state.combo_label_cn || state.combo_label || "空组合"],
  ];

  const statsRoot = document.getElementById("stateStats");
  statsRoot.innerHTML = "";
  stats.forEach(([label, value]) => {
    const block = document.createElement("div");
    block.className = "stat-item";
    block.innerHTML = `<small>${label}</small><strong>${value}</strong>`;
    statsRoot.appendChild(block);
  });

  const preview = document.getElementById("layerPreview");
  preview.innerHTML = "";
  preview.appendChild(renderPanelCells(state.panel_masks[0], "第 1 层隔板"));
  preview.appendChild(renderPanelCells(state.panel_masks[1], "第 2 层隔板"));
  preview.appendChild(renderRodCorners(state.rod_masks[0], "第 1 层杆"));
  preview.appendChild(renderRodCorners(state.rod_masks[1], "第 2 层杆"));

  const validation = document.getElementById("validationBox");
  const statusClass = state.passed ? "status-pass" : "status-fail";
  const statusText = state.passed ? "通过" : "失败";
  const reasons = state.reasons.length
    ? `<ul class="reason-list">${state.reasons.map((reason) => `<li>${reason}</li>`).join("")}</ul>`
    : "<div class='mono'>无失败原因</div>";

  validation.innerHTML = `
    <div class="${statusClass}">状态：${statusText}</div>
    <div class="mono">组合=${state.combo_label_cn || state.combo_label || "空组合"}</div>
    <div class="mono">边界有效=${state.boundary_valid} | 目标边界有效=${state.boundary_target_ok}</div>
    <div class="mono">组合有效=${state.combo_valid} | R3杆落地=${state.r3_rod_grounded} | R3隔板支撑=${state.r3_panel_supported} | R3整体=${state.r3_ok} | R4投影达标=${state.r4_projection} | R4基线=${state.baseline_efficiency.toFixed(2)} | R4目标=${state.target_efficiency.toFixed(2)} | R5顶层满足=${state.r5_top_closed} | 规则有效=${state.rule_valid}</div>
    ${reasons}
  `;

  renderAllStateStatus();
  render3D(state);
}

function renderAllStateStatus() {
  const root = document.getElementById("stateStatusList");
  root.innerHTML = "";

  states.forEach((state) => {
    const row = document.createElement("div");
    row.className = state.state_id === selectedStateId ? "state-row active" : "state-row";
    const briefReason = state.reasons.length > 0 ? state.reasons[0] : "通过";
    row.innerHTML = `
      <small>${state.state_id}</small>
      <small>${state.group_id}</small>
      <div>
        <div>${state.combo_label_cn || state.combo_label || "空组合"}</div>
        <small>${briefReason}</small>
      </div>
      <div>${badge(state.passed)}</div>
    `;
    row.addEventListener("click", () => {
      selectedGroupId = state.group_id;
      selectedStateId = state.state_id;
      renderGroupList();
      renderStateCards();
      renderSelection();
    });
    root.appendChild(row);
  });
}

function panelCellsFromMask(mask) {
  const cells = [];
  for (let y = 0; y < 2; y += 1) {
    for (let x = 0; x < 2; x += 1) {
      const index = y * 2 + x;
      if ((mask & (1 << index)) !== 0) {
        cells.push({ x, y });
      }
    }
  }
  return cells;
}

function rodCornersFromMask(mask) {
  const corners = [];
  for (let y = 0; y < 3; y += 1) {
    for (let x = 0; x < 3; x += 1) {
      const index = y * 3 + x;
      if ((mask & (1 << index)) !== 0) {
        corners.push({ x, y });
      }
    }
  }
  return corners;
}

function connectorPoints(panelMask, rodMask, z) {
  const points = [];
  const seen = new Set();
  panelCellsFromMask(panelMask).forEach((cell) => {
    const corners = [
      [cell.x, cell.y],
      [cell.x + 1, cell.y],
      [cell.x, cell.y + 1],
      [cell.x + 1, cell.y + 1],
    ];
    corners.forEach(([cx, cy]) => {
      const idx = cy * 3 + cx;
      if ((rodMask & (1 << idx)) !== 0) {
        const key = `${cx},${cy},${z}`;
        if (!seen.has(key)) {
          seen.add(key);
          points.push({ x: cx, y: cy, z });
        }
      }
    });
  });
  return points;
}

function unsupportedCellsFromIndices(indices) {
  return indices.map((idx) => ({ x: idx % 2, y: Math.floor(idx / 2) }));
}

function render3D(state) {
  const traces = [];

  traces.push({
    type: "scatter3d",
    mode: "lines",
    x: [0, 2, 2, 0, 0],
    y: [0, 0, 2, 2, 0],
    z: [0, 0, 0, 0, 0],
    line: { color: "#8191a1", width: 6 },
    name: "占地框架",
    hoverinfo: "skip",
  });

  let panelLegend = true;
  let connectorLegend = true;
  let rodLegend = true;
  let unsupportedLegend = true;

  [
    { layer: 0, zBottom: 0, zTop: 1 },
    { layer: 1, zBottom: 1, zTop: 2 },
  ].forEach(({ layer, zBottom, zTop }) => {
    const panelMask = state.panel_masks[layer];
    const rodMask = state.rod_masks[layer];

    const rodCorners = rodCornersFromMask(rodMask);
    rodCorners.forEach((corner) => {
      traces.push({
        type: "scatter3d",
        mode: "lines",
        x: [corner.x, corner.x],
        y: [corner.y, corner.y],
        z: [zBottom, zTop],
        line: { color: "#1456a5", width: 7 },
        name: "杆",
        hovertemplate: `杆 L${layer + 1} (${corner.x},${corner.y})<extra></extra>`,
        showlegend: rodLegend,
      });
      rodLegend = false;
    });

    panelCellsFromMask(panelMask).forEach((cell) => {
      traces.push({
        type: "mesh3d",
        x: [cell.x, cell.x + 1, cell.x + 1, cell.x],
        y: [cell.y, cell.y, cell.y + 1, cell.y + 1],
        z: [zTop, zTop, zTop, zTop],
        i: [0, 0],
        j: [1, 2],
        k: [2, 3],
        color: "#ef8a17",
        opacity: 0.62,
        name: "隔板",
        hovertemplate: `隔板 L${layer + 1}<extra></extra>`,
        showlegend: panelLegend,
      });
      panelLegend = false;
    });

    const connectors = connectorPoints(panelMask, rodMask, zTop + 0.02);
    if (connectors.length > 0) {
      traces.push({
        type: "scatter3d",
        mode: "markers",
        x: connectors.map((item) => item.x),
        y: connectors.map((item) => item.y),
        z: connectors.map((item) => item.z),
        marker: { color: "#2a9d8f", size: 5 },
        name: "连接件",
        hovertemplate: `连接件 L${layer + 1}<extra></extra>`,
        showlegend: connectorLegend,
      });
      connectorLegend = false;
    }

    const unsupported = unsupportedCellsFromIndices(state.unsupported_cells_per_layer[layer]);
    if (unsupported.length > 0) {
      traces.push({
        type: "scatter3d",
        mode: "markers",
        x: unsupported.map((cell) => cell.x + 0.5),
        y: unsupported.map((cell) => cell.y + 0.5),
        z: unsupported.map(() => zTop),
        marker: { color: "#d62828", size: 5, symbol: "x" },
        name: "不受支撑单元",
        hovertemplate: `不受支撑 L${layer + 1}<extra></extra>`,
        showlegend: unsupportedLegend,
      });
      unsupportedLegend = false;
    }
  });

  Plotly.react(
    "structure3d",
    traces,
    {
      margin: { l: 0, r: 0, b: 0, t: 6 },
      scene: {
        xaxis: { title: "X", range: [-0.2, 2.2], dtick: 1 },
        yaxis: { title: "Y", range: [-0.2, 2.2], dtick: 1 },
        zaxis: { title: "层级", range: [0, 2.25], dtick: 1 },
        aspectmode: "cube",
        camera: {
          eye: { x: 1.45, y: 1.35, z: 1.25 },
        },
      },
      legend: {
        orientation: "h",
        x: 0,
        y: 1.02,
      },
    },
    { responsive: true, displaylogo: false }
  );
}

initSummary();
drawOverviewCharts();
initExplorer();
</script>
</body>
</html>
"""
    return html.replace("__DATA_PAYLOAD__", json.dumps(payload, ensure_ascii=False))


def write_markdown_report(
    report_path: Path,
    payload: dict[str, Any],
    top_records: list[dict[str, Any]],
) -> None:
    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    combo_dist_text = ", ".join(
        f"{item['combo_label']}:{item['count']}" for item in payload["combo_distribution"]
    )
    lines: list[str] = [
        "# 置物架可视化报告（A=4, layers<=2）",
        "",
        f"- 生成时间(UTC): `{generated_at}`",
        f"- 目标: `{payload['goal']['statement']}`",
        f"- 占地面积约束: `A={payload['meta']['required_footprint_area']}`",
        f"- 层数上限: `N<={payload['meta']['max_layers']}`",
        f"- 基线阈值: `{payload['summary']['threshold_rule']}`",
        "",
        "## 边界与目标验证",
        f"- `boundary.validate()`: `{payload['boundary_check']['boundary_valid']}`",
        f"- `boundary_target_ok`: `{payload['boundary_check']['boundary_target_ok']}`",
    ]
    if payload["boundary_check"]["errors"]:
        lines.append("- 错误:")
        for reason in payload["boundary_check"]["errors"]:
            lines.append(f"  - {reason}")

    lines.extend(
        [
            "",
            "## 分型统计（实例级状态）",
            f"- 总状态数: `{payload['summary']['total_states']}`",
            f"- 通过数: `{payload['summary']['passed_states']}`",
            f"- 失败数: `{payload['summary']['failed_states']}`",
            f"- 通过率: `{payload['summary']['pass_ratio']:.2%}`",
            f"- 状态中的组合分布: `{combo_dist_text}`",
            "",
            "## 模块级组合规则状态（兼容输出）",
            "| 组合ID | 模块 | 规则是否通过 | 失败原因 |",
            "|---|---|---|---|",
        ]
    )
    for combo in payload["all_combos"]:
        lines.append(
            "| {combo_id} | {label} | {ok} | {reasons} |".format(
                combo_id=combo["combo_id"],
                label=combo.get("label_cn") or combo["label"] or "空组合",
                ok=combo["rule_valid"],
                reasons="; ".join(combo["rule_fail_reasons"]) or "无",
            )
        )

    lines.extend(
        [
            "",
            "## 前 10 个高投影比可行状态",
            "| 状态ID | 分组 | 投影比率 | 每层隔板数 | 每层杆数 |",
            "|---|---|---:|---|---|",
        ]
    )
    for record in top_records:
        lines.append(
            "| {state_id} | {group_id} {group_key} | {ratio:.2f} | {panels} | {rods} |".format(
                state_id=record["state_id"],
                group_id=record["group_id"],
                group_key=str(record["group_key"]).replace("cells/layer=", "每层隔板数="),
                ratio=record["projection_ratio"],
                panels=tuple(record["cells_per_layer"]),
                rods=tuple(record["rods_per_layer"]),
            )
        )

    lines.extend(
        [
            "",
            "## 可视化产物",
            f"- 可视化页面: `{DASHBOARD_PATH.as_posix()}`",
            f"- 数据快照: `{DATA_PATH.as_posix()}`",
            "- 使用方式: 在浏览器打开可视化页面，即可查看全状态列表并点击查看 3D 结构。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """运行置物架框架可视化验证并输出报告。"""
    goal = Goal("在单位占地面积下提升置物与取放效率")

    boundary = BoundaryDefinition(
        layers_n=2,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=2.0, depth=2.0, height=1.0),
        opening_o=Opening2D(width=2.0, height=1.0),
        footprint_a=Footprint2D(width=2.0, depth=2.0),
    )

    rules = CombinationRules.default()
    all_combo_options = to_combo_options(rules.all_subsets(), rules, prefix="C")
    valid_combo_options = [option for option in all_combo_options if option.rule_valid]
    valid_combos = [option.combo for option in valid_combo_options]

    states = enumerate_instance_states(FOOTPRINT_AREA, MAX_LAYERS)
    boundary_valid, boundary_errors = boundary.validate()
    boundary_target_ok, boundary_target_errors = validate_boundary_target(
        boundary=boundary,
        required_area=FOOTPRINT_AREA,
        max_layers=MAX_LAYERS,
    )

    state_records, groups, summary, combo_distribution = enrich_states(
        states=states,
        boundary=boundary,
        rules=rules,
        valid_combinations=valid_combos,
        boundary_target_ok=boundary_target_ok,
        boundary_target_errors=boundary_target_errors,
    )

    hypothesis = Hypothesis(
        hypothesis_id="H1",
        statement="在满足边界与组合规则时，访问效率应高于基线",
    )

    representative = next((item for item in state_records if item["passed"]), state_records[0])
    candidate_combo = {Module(name) for name in representative["combo_modules"]}
    verification_input = VerificationInput(
        boundary=boundary,
        combo=candidate_combo,
        valid_combinations=valid_combos,
        baseline_efficiency=float(representative.get("baseline_efficiency", BASELINE_EFFICIENCY)),
        target_efficiency=representative["projection_ratio"],
    )
    verification_result = verify(verification_input)

    logic_passed = summary["passed_states"] > 0 and boundary_valid and boundary_target_ok
    logic_record = build_logic_record(goal, boundary, logic_passed)
    logic_record.export_json("docs/logic_record.json")

    payload = {
        "meta": {
            "family": "shelf",
            "required_footprint_area": FOOTPRINT_AREA,
            "max_layers": MAX_LAYERS,
        },
        "goal": goal.to_dict(),
        "boundary": boundary.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "threshold_ratio": BASELINE_EFFICIENCY,
        "boundary_check": {
            "boundary_valid": boundary_valid,
            "boundary_target_ok": boundary_target_ok,
            "errors": [*boundary_errors, *boundary_target_errors],
        },
        "combos": [option.to_dict() for option in valid_combo_options],
        "all_combos": [option.to_dict() for option in all_combo_options],
        "states": state_records,
        # Compatibility aliases retained for existing data consumers.
        "variants": state_records,
        "groups": groups,
        "summary": summary,
        "combo_distribution": combo_distribution,
            "compatibility": {
                "deprecated_fields": ["layer_masks", "variants", "total_types", "passed_types", "failed_types"],
                "notes": [
                    "layer_masks 作为 panel_masks 的兼容别名保留",
                    "variants 作为 states 的兼容别名保留",
                    "以 type 命名的汇总字段映射到 state 口径",
                ],
            },
        }

    ensure_local_plotly_bundle(PLOTLY_BUNDLE_PATH)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DASHBOARD_PATH.write_text(build_dashboard_html(payload), encoding="utf-8")

    top_passed = sorted(
        (item for item in state_records if item["passed"]),
        key=lambda item: (item["projection_ratio"], item["overlap_cells"], item["total_rods"]),
        reverse=True,
    )[:10]
    write_markdown_report(REPORT_PATH, payload, top_passed)

    snapshot = {
        "goal": goal.to_dict(),
        "boundary": boundary.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "candidate_combo": modules_to_list(candidate_combo),
        "valid_combinations": [modules_to_list(item) for item in valid_combos],
        "verification": verification_result.to_dict(),
        "logic_record_path": "docs/logic_record.json",
        "visualization_dashboard_path": DASHBOARD_PATH.as_posix(),
        "visualization_report_path": REPORT_PATH.as_posix(),
        "visualization_data_path": DATA_PATH.as_posix(),
        "summary": summary,
    }

    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

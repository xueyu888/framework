from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from domain import BoundaryDefinition, DiscreteGrid, EnumerationConfig, Footprint2D, Opening2D, Space3D
from enumeration import enumerate_structure_types
from rules.combination_rules import geometric_type_combinations
from visualization.type_grouping import TypeGroup, build_type_groups


@dataclass(frozen=True)
class MappingCheckResult:
    passed: bool
    checked_changes: bool
    error_count: int
    first_error: str


@dataclass(frozen=True)
class ProjectionMetric:
    weighted_cells: int
    union_cells: int
    effective_area: float
    footprint_area: float
    ratio: float


@dataclass(frozen=True)
class ProjectionValidationSummary:
    generated_at_utc: str
    strict_mapping_passed: bool
    strict_mapping_change_passed: bool
    ratio_threshold: float
    total_types: int
    boundary_valid: bool
    structural_valid_types: int
    structural_invalid_types: int
    projection_improved_types: int
    projection_not_improved_types: int
    passed_types: int
    failed_types: int
    avg_ratio: float
    min_ratio: float
    max_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "strict_mapping_passed": self.strict_mapping_passed,
            "strict_mapping_change_passed": self.strict_mapping_change_passed,
            "ratio_threshold": self.ratio_threshold,
            "total_types": self.total_types,
            "boundary_valid": self.boundary_valid,
            "structural_valid_types": self.structural_valid_types,
            "structural_invalid_types": self.structural_invalid_types,
            "projection_improved_types": self.projection_improved_types,
            "projection_not_improved_types": self.projection_not_improved_types,
            "passed_types": self.passed_types,
            "failed_types": self.failed_types,
            "avg_ratio": self.avg_ratio,
            "min_ratio": self.min_ratio,
            "max_ratio": self.max_ratio,
        }


def _run_mapping_check(check_changes: bool) -> MappingCheckResult:
    cmd = [sys.executable, str(REPO_ROOT / "scripts/validate_strict_mapping.py")]
    if check_changes:
        cmd.append("--check-changes")
    cmd.append("--json")

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    payload: dict[str, Any]
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"passed": False, "errors": [{"message": result.stdout.strip()}]}
    else:
        payload = {
            "passed": False,
            "errors": [
                {
                    "message": result.stderr.strip() or "mapping validation produced no output",
                }
            ],
        }

    errors = payload.get("errors", [])
    first_error = ""
    if errors and isinstance(errors, list) and isinstance(errors[0], dict):
        first_error = str(errors[0].get("message", ""))

    return MappingCheckResult(
        passed=bool(payload.get("passed", False)) and result.returncode == 0,
        checked_changes=check_changes,
        error_count=len(errors) if isinstance(errors, list) else 1,
        first_error=first_error,
    )


def _default_boundary() -> BoundaryDefinition:
    return BoundaryDefinition(
        layers_n=2,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=80.0, depth=35.0, height=30.0),
        opening_o=Opening2D(width=65.0, height=28.0),
        footprint_a=Footprint2D(width=90.0, depth=40.0),
    )


def _build_grid(boundary: BoundaryDefinition, x_cells: int, y_cells: int) -> DiscreteGrid:
    return DiscreteGrid(
        x_cells=x_cells,
        y_cells=y_cells,
        layers_n=boundary.layers_n,
        cell_width=boundary.footprint_a.width / float(x_cells),
        cell_depth=boundary.footprint_a.depth / float(y_cells),
        layer_height=boundary.space_s_per_layer.height,
    )


def _group_lookup(candidates: list[Any], grid: DiscreteGrid) -> tuple[dict[str, str], dict[str, TypeGroup]]:
    groups = build_type_groups(candidates, grid)
    key_to_group: dict[str, str] = {}
    group_meta: dict[str, TypeGroup] = {}

    for idx, group in enumerate(groups):
        gid = f"G{idx:02d}"
        group_meta[gid] = group
        for _, candidate in group.items:
            key_to_group[candidate.canonical_key] = gid

    return key_to_group, group_meta


def _projection_metric(topology: Any, grid: DiscreteGrid, boundary: BoundaryDefinition) -> ProjectionMetric:
    coverage: dict[tuple[int, int], int] = defaultdict(int)
    for cells in topology.occupied_cells_by_layer().values():
        for cell in cells:
            coverage[cell] += 1

    weighted_cells = sum(coverage.values())
    union_cells = len(coverage)
    effective_area = float(weighted_cells) * grid.cell_area
    footprint_area = boundary.footprint_a.width * boundary.footprint_a.depth
    ratio = (effective_area / footprint_area) if footprint_area > 0 else 0.0

    return ProjectionMetric(
        weighted_cells=weighted_cells,
        union_cells=union_cells,
        effective_area=effective_area,
        footprint_area=footprint_area,
        ratio=ratio,
    )


def _collect_rows(
    grid: DiscreteGrid,
    boundary: BoundaryDefinition,
    ratio_threshold: float,
    allow_empty_layer: bool,
    max_type_count: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    enum_result = enumerate_structure_types(
        EnumerationConfig(
            grid=grid,
            allow_empty_layer=allow_empty_layer,
            mirror_equivalent=True,
            axis_permutation_equivalent=True,
            include_shelf_family=True,
            include_frame_family=False,
            max_type_count=max_type_count,
        )
    )

    key_to_group, group_meta = _group_lookup(enum_result.unique_candidates, grid)
    valid_combo_keys = {frozenset(combo) for combo in geometric_type_combinations()}
    boundary_valid, boundary_errors = boundary.validate()

    rows: list[dict[str, Any]] = []
    reason_counter: Counter[str] = Counter()
    for idx, candidate in enumerate(enum_result.unique_candidates, start=1):
        projection = _projection_metric(candidate.topology, grid, boundary)
        group_id = key_to_group.get(candidate.canonical_key, "UNKNOWN")
        group = group_meta.get(group_id)
        combo_valid = frozenset(candidate.topology.module_combo()) in valid_combo_keys
        structural_valid = bool(candidate.structural_valid)
        projection_improved = projection.ratio > ratio_threshold

        reasons: list[str] = []
        if not boundary_valid:
            reasons.extend(boundary_errors)
        if not combo_valid:
            reasons.append("combo is not in valid combinations")
        if not structural_valid:
            reasons.extend(candidate.reasons or ["structural rules failed"])
        if not projection_improved:
            reasons.append(
                f"projection_ratio({projection.ratio:.6f}) <= threshold({ratio_threshold:.6f})"
            )
        if not reasons:
            reasons.append("passed")

        for reason in reasons:
            reason_counter[reason] += 1

        rows.append(
            {
                "index": idx,
                "group_id": group_id,
                "group_counts_per_layer": ",".join(str(x) for x in (group.counts_per_layer if group else ())),
                "canonical_key": candidate.canonical_key,
                "panel_count": candidate.topology.panel_count(),
                "boundary_valid": boundary_valid,
                "combination_valid": combo_valid,
                "structural_valid": structural_valid,
                "projection_improved": projection_improved,
                "passed": boundary_valid and combo_valid and structural_valid and projection_improved,
                "weighted_projected_cells": projection.weighted_cells,
                "union_projected_cells": projection.union_cells,
                "effective_area": round(projection.effective_area, 6),
                "footprint_area": round(projection.footprint_area, 6),
                "projection_ratio": round(projection.ratio, 6),
                "threshold": round(ratio_threshold, 6),
                "reasons": " | ".join(reasons),
            }
        )

    return rows, dict(reason_counter)


def _build_summary(
    rows: list[dict[str, Any]],
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
    ratio_threshold: float,
) -> ProjectionValidationSummary:
    ratios = [float(row["projection_ratio"]) for row in rows]
    passed_rows = [row for row in rows if row["passed"]]
    structural_valid_rows = [row for row in rows if row["structural_valid"]]
    improved_rows = [row for row in rows if row["projection_improved"]]
    boundary_valid = bool(rows[0]["boundary_valid"]) if rows else False

    return ProjectionValidationSummary(
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        strict_mapping_passed=mapping_default.passed,
        strict_mapping_change_passed=mapping_changes.passed,
        ratio_threshold=ratio_threshold,
        total_types=len(rows),
        boundary_valid=boundary_valid,
        structural_valid_types=len(structural_valid_rows),
        structural_invalid_types=len(rows) - len(structural_valid_rows),
        projection_improved_types=len(improved_rows),
        projection_not_improved_types=len(rows) - len(improved_rows),
        passed_types=len(passed_rows),
        failed_types=len(rows) - len(passed_rows),
        avg_ratio=(sum(ratios) / len(ratios)) if ratios else 0.0,
        min_ratio=min(ratios) if ratios else 0.0,
        max_ratio=max(ratios) if ratios else 0.0,
    )


def _write_rows_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "index",
        "group_id",
        "group_counts_per_layer",
        "canonical_key",
        "panel_count",
        "boundary_valid",
        "combination_valid",
        "structural_valid",
        "projection_improved",
        "passed",
        "weighted_projected_cells",
        "union_projected_cells",
        "effective_area",
        "footprint_area",
        "projection_ratio",
        "threshold",
        "reasons",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_group_summary_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    group_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_buckets[str(row["group_id"])].append(row)

    fieldnames = [
        "group_id",
        "counts_per_layer",
        "total_types",
        "passed_types",
        "failed_types",
        "avg_ratio",
        "min_ratio",
        "max_ratio",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for gid in sorted(group_buckets.keys()):
            bucket = group_buckets[gid]
            ratios = [float(row["projection_ratio"]) for row in bucket]
            passed_types = sum(1 for row in bucket if row["passed"])
            writer.writerow(
                {
                    "group_id": gid,
                    "counts_per_layer": bucket[0]["group_counts_per_layer"],
                    "total_types": len(bucket),
                    "passed_types": passed_types,
                    "failed_types": len(bucket) - passed_types,
                    "avg_ratio": round(sum(ratios) / len(ratios), 6) if ratios else 0.0,
                    "min_ratio": min(ratios) if ratios else 0.0,
                    "max_ratio": max(ratios) if ratios else 0.0,
                }
            )


def _write_markdown_summary(
    summary: ProjectionValidationSummary,
    mapping_default: MappingCheckResult,
    mapping_changes: MappingCheckResult,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Shelf Projection Validation Summary",
        "",
        "Metric rule:",
        f"- pass if `projection_ratio > {summary.ratio_threshold:.6f}` and boundary/combination/structural checks all pass.",
        "",
        "## Validation Checks",
        "",
        "| Check | Passed | Error Count | First Error |",
        "|---|---:|---:|---|",
        (
            f"| strict_mapping | {mapping_default.passed} | {mapping_default.error_count} | "
            f"{mapping_default.first_error or '-'} |"
        ),
        (
            f"| strict_mapping_change_propagation | {mapping_changes.passed} | {mapping_changes.error_count} | "
            f"{mapping_changes.first_error or '-'} |"
        ),
        "",
        "## Stats",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| generated_at_utc | {summary.generated_at_utc} |",
        f"| total_types | {summary.total_types} |",
        f"| structural_valid_types | {summary.structural_valid_types} |",
        f"| projection_improved_types | {summary.projection_improved_types} |",
        f"| passed_types | {summary.passed_types} |",
        f"| failed_types | {summary.failed_types} |",
        f"| avg_ratio | {summary.avg_ratio:.6f} |",
        f"| min_ratio | {summary.min_ratio:.6f} |",
        f"| max_ratio | {summary.max_ratio:.6f} |",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_json_summary(summary: ProjectionValidationSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_dashboard(
    rows: list[dict[str, Any]],
    summary: ProjectionValidationSummary,
    reason_counter: dict[str, int],
    output_path: Path,
) -> None:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    output_path.parent.mkdir(parents=True, exist_ok=True)

    passed_rows = [row for row in rows if row["passed"]]
    failed_rows = [row for row in rows if not row["passed"]]

    group_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_buckets[str(row["group_id"])].append(row)
    group_ids = sorted(group_buckets.keys())
    group_pass = [sum(1 for row in group_buckets[gid] if row["passed"]) for gid in group_ids]
    group_fail = [len(group_buckets[gid]) - group_pass[idx] for idx, gid in enumerate(group_ids)]

    reason_items = sorted(reason_counter.items(), key=lambda item: item[1], reverse=True)
    top_reasons = reason_items[:8]
    reason_labels = [item[0] for item in top_reasons] or ["none"]
    reason_values = [item[1] for item in top_reasons] or [0]

    failed_table = failed_rows[:20]
    passed_table = sorted(
        passed_rows,
        key=lambda row: float(row["projection_ratio"]),
        reverse=True,
    )[:20]

    fig = make_subplots(
        rows=3,
        cols=2,
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "table"}, {"type": "table"}],
        ],
        subplot_titles=(
            "Overall Pass/Fail",
            "Projection Ratio Distribution",
            "Pass/Fail by Group",
            "Type-Level Ratio Scatter (hover for canonical key)",
            "Failed Types (Top 20)",
            "Passed Types (Top 20 by ratio)",
        ),
        vertical_spacing=0.1,
        horizontal_spacing=0.08,
    )

    fig.add_trace(
        go.Bar(
            x=["passed", "failed"],
            y=[summary.passed_types, summary.failed_types],
            marker_color=["#1f9d55", "#d64545"],
            showlegend=False,
            name="overall",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=[float(row["projection_ratio"]) for row in passed_rows],
            nbinsx=25,
            opacity=0.75,
            marker_color="#1f9d55",
            name="passed",
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Histogram(
            x=[float(row["projection_ratio"]) for row in failed_rows],
            nbinsx=25,
            opacity=0.75,
            marker_color="#d64545",
            name="failed",
        ),
        row=1,
        col=2,
    )
    fig.add_vline(
        x=summary.ratio_threshold,
        line_width=2,
        line_dash="dash",
        line_color="#1a365d",
        annotation_text=f"threshold={summary.ratio_threshold:.2f}",
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Bar(
            x=group_ids,
            y=group_pass,
            name="passed",
            marker_color="#1f9d55",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=group_ids,
            y=group_fail,
            name="failed",
            marker_color="#d64545",
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=[int(row["index"]) for row in rows],
            y=[float(row["projection_ratio"]) for row in rows],
            mode="markers",
            marker={
                "color": ["#1f9d55" if row["passed"] else "#d64545" for row in rows],
                "size": 8,
                "opacity": 0.85,
            },
            text=[
                (
                    f"group={row['group_id']}<br>"
                    f"canonical={row['canonical_key']}<br>"
                    f"ratio={row['projection_ratio']}<br>"
                    f"passed={row['passed']}<br>"
                    f"reasons={row['reasons']}"
                )
                for row in rows
            ],
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
            name="types",
        ),
        row=2,
        col=2,
    )
    fig.add_hline(
        y=summary.ratio_threshold,
        line_width=2,
        line_dash="dash",
        line_color="#1a365d",
        row=2,
        col=2,
    )

    fig.add_trace(
        go.Table(
            header={
                "values": ["group", "index", "ratio", "canonical_key", "reasons"],
                "fill_color": "#ffe3e3",
                "align": "left",
            },
            cells={
                "values": [
                    [row["group_id"] for row in failed_table],
                    [row["index"] for row in failed_table],
                    [row["projection_ratio"] for row in failed_table],
                    [row["canonical_key"] for row in failed_table],
                    [row["reasons"] for row in failed_table],
                ],
                "fill_color": "#fff5f5",
                "align": "left",
            },
        ),
        row=3,
        col=1,
    )

    fig.add_trace(
        go.Table(
            header={
                "values": ["group", "index", "ratio", "canonical_key"],
                "fill_color": "#e6fffa",
                "align": "left",
            },
            cells={
                "values": [
                    [row["group_id"] for row in passed_table],
                    [row["index"] for row in passed_table],
                    [row["projection_ratio"] for row in passed_table],
                    [row["canonical_key"] for row in passed_table],
                ],
                "fill_color": "#f0fff4",
                "align": "left",
            },
        ),
        row=3,
        col=2,
    )

    fig.update_layout(
        title=(
            "Shelf Top-Projection Validation Dashboard | "
            f"threshold={summary.ratio_threshold:.2f}, "
            f"types={summary.total_types}, passed={summary.passed_types}, failed={summary.failed_types}"
        ),
        barmode="stack",
        template="plotly_white",
        width=1800,
        height=1600,
    )

    fig.update_xaxes(title_text="group id", row=2, col=1)
    fig.update_yaxes(title_text="type count", row=2, col=1)
    fig.update_xaxes(title_text="type index", row=2, col=2)
    fig.update_yaxes(title_text="projection ratio", row=2, col=2)
    fig.update_yaxes(title_text="count", row=1, col=2)

    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate shelf top-projection validation table and dashboard."
    )
    parser.add_argument("--x-cells", type=int, default=2)
    parser.add_argument("--y-cells", type=int, default=2)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--ratio-threshold", type=float, default=1.0)
    parser.add_argument("--allow-empty-layer", dest="allow_empty_layer", action="store_true")
    parser.add_argument("--no-allow-empty-layer", dest="allow_empty_layer", action="store_false")
    parser.set_defaults(allow_empty_layer=True)
    parser.add_argument("--max-type-count", type=int, default=5000)
    parser.add_argument("--output-dir", default="docs/validation")
    args = parser.parse_args()

    boundary = _default_boundary()
    boundary = BoundaryDefinition(
        layers_n=args.layers,
        payload_p_per_layer=boundary.payload_p_per_layer,
        space_s_per_layer=boundary.space_s_per_layer,
        opening_o=boundary.opening_o,
        footprint_a=boundary.footprint_a,
    )
    grid = _build_grid(boundary, x_cells=args.x_cells, y_cells=args.y_cells)

    mapping_default = _run_mapping_check(check_changes=False)
    mapping_changes = _run_mapping_check(check_changes=True)
    rows, reason_counter = _collect_rows(
        grid=grid,
        boundary=boundary,
        ratio_threshold=args.ratio_threshold,
        allow_empty_layer=args.allow_empty_layer,
        max_type_count=args.max_type_count,
    )
    summary = _build_summary(
        rows=rows,
        mapping_default=mapping_default,
        mapping_changes=mapping_changes,
        ratio_threshold=args.ratio_threshold,
    )

    output_dir = Path(args.output_dir)
    row_csv_path = output_dir / "shelf_projection_validation_table.csv"
    group_csv_path = output_dir / "shelf_projection_group_summary.csv"
    md_path = output_dir / "shelf_projection_validation_summary.md"
    html_path = output_dir / "shelf_projection_validation_dashboard.html"
    json_path = output_dir / "shelf_projection_validation_summary.json"

    _write_rows_csv(rows, row_csv_path)
    _write_group_summary_csv(rows, group_csv_path)
    _write_markdown_summary(summary, mapping_default, mapping_changes, md_path)
    _write_dashboard(rows, summary, reason_counter, html_path)
    _write_json_summary(summary, json_path)

    print(
        json.dumps(
            {
                "summary": summary.to_dict(),
                "artifacts": {
                    "row_csv": str(row_csv_path),
                    "group_csv": str(group_csv_path),
                    "summary_markdown": str(md_path),
                    "dashboard_html": str(html_path),
                    "summary_json": str(json_path),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

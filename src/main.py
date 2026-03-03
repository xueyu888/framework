from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from typing import Any

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    GridShelfVariant,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
    derive_structure_from_occupied_cells,
    enumerate_grid_shelf_variants,
    modules_to_list,
    strict_mapping_meta,
    verify,
)


def build_logic_record(goal: Goal, boundary: BoundaryDefinition, result_ok: bool) -> LogicRecord:
    steps = [
        LogicStep("G", "goal", evidence=goal.to_dict()),
        LogicStep("B1", "layers", ["G"], {"N": boundary.layers_n}),
        LogicStep("B2", "payload", ["G"], {"P": boundary.payload_p_per_layer}),
        LogicStep("B3", "space", ["G"], {"S": boundary.space_s_per_layer.__dict__}),
        LogicStep("B4", "opening", ["G"], {"O": boundary.opening_o.__dict__}),
        LogicStep("B5", "footprint", ["G"], {"A": boundary.footprint_a.__dict__}),
        LogicStep("M1", "rod", ["B1", "B2"]),
        LogicStep("M2", "connector", ["B1", "B4"]),
        LogicStep("M3", "panel", ["B2", "B3"]),
        LogicStep("R1", "no isolated module", ["M1", "M2", "M3"]),
        LogicStep("R2", "connector is mandatory", ["M2"]),
        LogicStep("R3", "rod must be vertical", ["M1"]),
        LogicStep("R4", "rod-rod horizontal relation", ["M1"]),
        LogicStep("R5", "rod-panel perpendicular relation", ["M1", "M3"]),
        LogicStep("R6", "rod must link 4 corners of each face", ["M1"]),
        LogicStep("R7", "rod and panel are mandatory", ["M1", "M3"]),
        LogicStep("R8", "panel corners must have connectors", ["M2", "M3"]),
        LogicStep("R9", "top occupied level in each column must have panel", ["M3"]),
        LogicStep("R10", "upper occupied cells must have support below", ["M1", "M3"]),
        LogicStep(
            "R11",
            "connector only on connected rod endpoints; free endpoints must not have connector",
            ["M1", "M2", "M3"],
        ),
        LogicStep(
            "R12",
            "shape dedup uses row/col planar rotation only; level axis must stay fixed",
            ["M1", "M3"],
        ),
        LogicStep(
            "H1",
            "all grid variants under max boundary are valid",
            ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12"],
        ),
        LogicStep("V1", "verify hypothesis", ["H1"], {"passed": result_ok}),
        LogicStep("C", "conclusion", ["V1"], {"adopt_now": result_ok}),
    ]
    return LogicRecord.build(steps)


def projection_parallel_validation(shelf_model: Any) -> dict[str, Any]:
    projection_normal = (0.0, 0.0, 1.0)
    invalid_panels: list[str] = []
    for panel in shelf_model.panels:
        nx, ny, nz = panel.normal_unit()
        dot = abs(nx * projection_normal[0] + ny * projection_normal[1] + nz * projection_normal[2])
        if abs(dot - 1.0) > 1e-6:
            invalid_panels.append(panel.panel_id)
    return {
        "projection_plane": {"normal": {"x": 0.0, "y": 0.0, "z": 1.0}},
        "panel_parallel_projection": len(invalid_panels) == 0,
        "invalid_panels": invalid_panels,
    }


def variant_top_view(variant: GridShelfVariant, max_rows: int = 2, max_cols: int = 2) -> list[list[int]]:
    view = [[0 for _ in range(max_cols)] for _ in range(max_rows)]
    for cell in variant.model.cells:
        if 0 <= cell.row < max_rows and 0 <= cell.col < max_cols:
            view[cell.row][cell.col] = 1
    return view


def variant_top_projection_counts(
    variant: GridShelfVariant, max_rows: int = 2, max_cols: int = 2
) -> list[list[int]]:
    counts = [[0 for _ in range(max_cols)] for _ in range(max_rows)]
    for cell in variant.model.cells:
        if 0 <= cell.row < max_rows and 0 <= cell.col < max_cols:
            counts[cell.row][cell.col] += 1
    return counts


def _real_component_counts(variant: GridShelfVariant) -> dict[str, int]:
    occupied_cells = [(cell.row, cell.col, cell.level) for cell in variant.model.cells]
    derived = derive_structure_from_occupied_cells(occupied_cells)

    return {
        "rod": len(derived["rod_segments"]) if Module.ROD in variant.combo else 0,
        "connector": len(derived["required_connectors"]) if Module.CONNECTOR in variant.combo else 0,
        "panel": len(occupied_cells) if Module.PANEL in variant.combo else 0,
    }


def _storage_efficiency(variant: GridShelfVariant, baseline: float = 1.0) -> dict[str, Any]:
    projection_counts = variant_top_projection_counts(variant)
    footprint_cells = sum(1 for row in projection_counts for cell in row if cell > 0)
    panel_count = len(variant.model.cells) if Module.PANEL in variant.combo else 0
    raw = (panel_count / footprint_cells) if footprint_cells > 0 else 0.0
    score = raw / baseline if baseline > 0 else 0.0
    return {
        "baseline": baseline,
        "score": round(score, 4),
        "raw": round(raw, 4),
        "pass": score > 1.0,
        "panel_count": panel_count,
        "footprint_cells": footprint_cells,
    }


def variant_to_payload(variant: GridShelfVariant) -> dict[str, Any]:
    occupied_cells = [(cell.row, cell.col, cell.level) for cell in variant.model.cells]
    derived = derive_structure_from_occupied_cells(occupied_cells)
    module_counts = _real_component_counts(variant)
    return {
        "variant_id": variant.variant_id,
        "dims": {"rows": variant.rows, "cols": variant.cols, "levels": variant.levels},
        "combo": modules_to_list(variant.combo),
        "module_counts": module_counts,
        "occupied_cells": [
            {"row": cell.row, "col": cell.col, "level": cell.level}
            for cell in variant.model.cells
        ],
        "derived_structure": {
            "rod_segments": [
                {"row_edge": row_edge, "col_edge": col_edge, "level": level}
                for row_edge, col_edge, level in sorted(derived["rod_segments"])
            ],
            "required_connectors": [
                {"row_edge": row_edge, "col_edge": col_edge, "z": z}
                for row_edge, col_edge, z in sorted(derived["required_connectors"])
            ],
        },
        "top_view": variant_top_view(variant),
        "top_view_projection_counts": variant_top_projection_counts(variant),
        "storage_efficiency": _storage_efficiency(variant),
    }


def _group_top_views(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        key = json.dumps(item["top_view"], ensure_ascii=False)
        grouped.setdefault(key, []).append(item)
    return grouped


def build_viewer_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>2x2x2 网格置物架 - 分组列表</title>
  <style>
    :root {
      --bg: #efe8d7;
      --ink: #142127;
      --card: #fcfaf4;
      --line: #c9c0af;
      --accent: #0b6b61;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: radial-gradient(circle at 15% 18%, #e5ddc9 0%, transparent 42%), var(--bg);
      font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
    }
    .wrap {
      max-width: 1380px;
      margin: 0 auto;
      padding: 12px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.04);
      padding: 14px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 20px;
    }
    .meta {
      font-size: 12px;
      color: #35565e;
      margin-bottom: 10px;
    }
    .group-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    .group-table th, .group-table td {
      border: 1px solid var(--line);
      padding: 6px;
      vertical-align: middle;
      text-align: left;
    }
    .group-table thead th {
      background: #f0ebde;
      color: #284852;
      position: sticky;
      top: 0;
      z-index: 1;
    }
    .name-link {
      display: inline-block;
      width: 100%;
      border: 1px solid #c7d4cf;
      border-radius: 6px;
      background: #e9f4f1;
      text-align: left;
      padding: 4px 6px;
      color: #11483f;
      font-size: 12px;
      text-decoration: none;
    }
    .topviews-cell {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(44px, 1fr));
      gap: 4px;
      min-width: 180px;
    }
    .topviews-cell canvas {
      width: 44px;
      height: 44px;
      border: 1px solid #d5ccbc;
      border-radius: 4px;
      background: #f8f6ef;
    }
    .chart-wrap {
      margin-bottom: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8f6ef;
      padding: 8px;
    }
    #efficiency-chart {
      width: 100%;
      height: 320px;
      display: block;
    }
    #rule-pass-fail-chart {
      width: 100%;
      height: 220px;
      display: block;
    }
    @media (max-width: 960px) {
      .group-table { font-size: 11px; }
      .topviews-cell { min-width: 150px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="card">
      <h1>2x2x2 网格置物架 - 分组列表</h1>
      <div class="meta" id="meta"></div>
      <div class="chart-wrap">
        <canvas id="efficiency-chart" width="1200" height="320"></canvas>
      </div>
      <div class="chart-wrap">
        <canvas id="rule-pass-fail-chart" width="1200" height="220"></canvas>
      </div>
      <table class="group-table">
        <thead>
          <tr>
            <th>分组名称</th>
            <th>模块和数量</th>
            <th>分组全部俯视图(2x2)</th>
            <th>结构数</th>
          </tr>
        </thead>
        <tbody id="group-table-body"></tbody>
      </table>
    </section>
  </div>
  <script type="module">
    const data = await fetch("./shelf_2x2x2.json").then(r => r.json());
    const groups = data.grouped_shelves;
    const meta = document.getElementById("meta");
    const maxRows = data.max_boundary.rows;
    const maxCols = data.max_boundary.cols;

    function computeProjectionCountsFromCells(shelf) {
      const counts = Array.from({ length: maxRows }, () => Array(maxCols).fill(0));
      for (const cell of (shelf.occupied_cells || [])) {
        if (cell.row >= 0 && cell.row < maxRows && cell.col >= 0 && cell.col < maxCols) {
          counts[cell.row][cell.col] += 1;
        }
      }
      return counts;
    }
    meta.textContent = `最大边界: ${data.max_boundary.rows}x${data.max_boundary.cols}x${data.max_boundary.levels} | 合规置物架总数: ${data.total_shelves}`;

    const tableBody = document.getElementById("group-table-body");

    function colorByProjectionCount(count, absoluteMaxCount) {
      if (count <= 0) return "#d1d5db";
      const clamped = Math.min(count, absoluteMaxCount);
      const t = absoluteMaxCount <= 1 ? 1 : (clamped - 1) / (absoluteMaxCount - 1);
      const light = 78 - Math.round(t * 42);
      return `hsl(173, 74%, ${light}%)`;
    }

    function drawTopView(canvas, topView, projectionCounts) {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const rows = topView.length;
      const cols = topView[0].length;
      const pad = 8;
      const w = canvas.width;
      const h = canvas.height;
      const cw = (w - pad * 2) / cols;
      const ch = (h - pad * 2) / rows;
      const absoluteMaxCount = Math.max(1, data.max_boundary.levels);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#f8f6ef";
      ctx.fillRect(0, 0, w, h);
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const count = projectionCounts?.[r]?.[c] ?? (topView[r][c] ? 1 : 0);
          ctx.fillStyle = colorByProjectionCount(count, absoluteMaxCount);
          ctx.fillRect(pad + c * cw + 2, pad + r * ch + 2, cw - 4, ch - 4);
          if (count > 0) {
            ctx.strokeStyle = "rgba(20,33,39,0.42)";
            ctx.lineWidth = 1;
            ctx.strokeRect(pad + c * cw + 2.5, pad + r * ch + 2.5, cw - 5, ch - 5);
          }
        }
      }
    }

    function renderGroupRows() {
      tableBody.innerHTML = "";
      groups.forEach((group) => {
        const tr = document.createElement("tr");

        const tdName = document.createElement("td");
        const link = document.createElement("a");
        link.className = "name-link";
        link.textContent = group.group_name;
        link.href = `./shelf_2x2x2_group_detail.html?group_key=${encodeURIComponent(group.group_key)}`;
        tdName.appendChild(link);

        const tdModules = document.createElement("td");
        const m = group.module_counts;
        tdModules.textContent = `杆:${m.rod} 连接接口:${m.connector} 隔板:${m.panel}`;

        const tdTopView = document.createElement("td");
        const topviewsWrap = document.createElement("div");
        topviewsWrap.className = "topviews-cell";
        group.shelves.forEach((shelf) => {
          const mini = document.createElement("canvas");
          mini.width = 44;
          mini.height = 44;
          const counts = shelf.top_view_projection_counts || computeProjectionCountsFromCells(shelf);
          drawTopView(mini, shelf.top_view, counts);
          mini.title = shelf.variant_id;
          topviewsWrap.appendChild(mini);
        });
        tdTopView.appendChild(topviewsWrap);

        const tdCount = document.createElement("td");
        tdCount.textContent = String(group.count);

        tr.appendChild(tdName);
        tr.appendChild(tdModules);
        tr.appendChild(tdTopView);
        tr.appendChild(tdCount);
        tableBody.appendChild(tr);
      });
    }

    function drawEfficiencyChart() {
      const canvas = document.getElementById("efficiency-chart");
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const shelves = groups.flatMap((g) => g.shelves || []);
      const n = shelves.length;
      const w = canvas.width;
      const h = canvas.height;
      const padL = 72;
      const padR = 18;
      const padT = 20;
      const padB = 108;
      const plotW = Math.max(1, w - padL - padR);
      const plotH = Math.max(1, h - padT - padB);
      const maxValue = Math.max(2, ...shelves.map((s) => s.storage_efficiency?.score ?? 0), 1);
      const gap = 4;
      const barW = Math.max(2, Math.floor((plotW - Math.max(0, n - 1) * gap) / Math.max(1, n)));

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#f8f6ef";
      ctx.fillRect(0, 0, w, h);

      // axis
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padL, padT);
      ctx.lineTo(padL, padT + plotH);
      ctx.lineTo(w - padR, padT + plotH);
      ctx.stroke();

      // y ticks + grid
      const tickCount = 5;
      ctx.font = "11px sans-serif";
      for (let i = 0; i <= tickCount; i++) {
        const v = (maxValue / tickCount) * i;
        const y = padT + plotH - (v / maxValue) * plotH;
        ctx.strokeStyle = "rgba(71,85,105,0.22)";
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(w - padR, y);
        ctx.stroke();
        ctx.fillStyle = "#334155";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(v.toFixed(1), padL - 8, y);
      }

      // y axis label
      ctx.save();
      ctx.translate(20, padT + plotH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = "#1f2937";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("效率", 0, 0);
      ctx.restore();

      shelves.forEach((shelf, i) => {
        const score = shelf.storage_efficiency?.score ?? 0;
        const isPass = shelf.storage_efficiency?.pass === true;
        const bh = Math.max(1, (score / maxValue) * plotH);
        const x = padL + i * (barW + gap);
        const y = padT + plotH - bh;
        ctx.fillStyle = isPass ? "#0f766e" : "#b45309";
        ctx.fillRect(x, y, barW, bh);
      });

      // x labels: structure id
      ctx.fillStyle = "#1f2937";
      ctx.font = "10px sans-serif";
      shelves.forEach((shelf, i) => {
        const x = padL + i * (barW + gap) + barW / 2;
        const y = padT + plotH + 8;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(-Math.PI / 4);
        ctx.textAlign = "right";
        ctx.textBaseline = "top";
        ctx.fillText(shelf.variant_id, 0, 0);
        ctx.restore();
      });

      // baseline should be on top of bars and visually clear
      const yBase = padT + plotH - (1 / maxValue) * plotH;
      ctx.strokeStyle = "#dc2626";
      ctx.lineWidth = 2.5;
      ctx.setLineDash([7, 4]);
      ctx.beginPath();
      ctx.moveTo(padL, yBase);
      ctx.lineTo(w - padR, yBase);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#dc2626";
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText("基线 = 1", padL + 6, yBase - 3);
    }

    function drawRulePassFailChart() {
      const canvas = document.getElementById("rule-pass-fail-chart");
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const shelves = groups.flatMap((g) => g.shelves || []);
      const passCount = shelves.filter((s) => s.storage_efficiency?.pass === true).length;
      const failCount = shelves.length - passCount;
      const labels = ["符合规则(>1)", "不符合规则(<=1)"];
      const values = [passCount, failCount];
      const colors = ["#0f766e", "#b45309"];

      const w = canvas.width;
      const h = canvas.height;
      const padL = 68;
      const padR = 22;
      const padT = 18;
      const padB = 48;
      const plotW = Math.max(1, w - padL - padR);
      const plotH = Math.max(1, h - padT - padB);
      const maxValue = Math.max(1, ...values);
      const n = values.length;
      const gap = 48;
      const barW = Math.min(180, Math.max(32, Math.floor((plotW - gap * (n - 1)) / n)));

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#f8f6ef";
      ctx.fillRect(0, 0, w, h);

      // axes
      ctx.strokeStyle = "#475569";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padL, padT);
      ctx.lineTo(padL, padT + plotH);
      ctx.lineTo(w - padR, padT + plotH);
      ctx.stroke();

      // y ticks
      const ticks = Math.min(5, Math.max(1, maxValue));
      ctx.font = "11px sans-serif";
      for (let i = 0; i <= ticks; i++) {
        const v = (maxValue / ticks) * i;
        const y = padT + plotH - (v / maxValue) * plotH;
        ctx.strokeStyle = "rgba(71,85,105,0.22)";
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(w - padR, y);
        ctx.stroke();
        ctx.fillStyle = "#334155";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(String(Math.round(v)), padL - 8, y);
      }

      ctx.fillStyle = "#1f2937";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText("当前展示结构规则统计", padL, 2);

      const totalBarsW = n * barW + (n - 1) * gap;
      const startX = padL + (plotW - totalBarsW) / 2;
      for (let i = 0; i < n; i++) {
        const value = values[i];
        const x = startX + i * (barW + gap);
        const bh = (value / maxValue) * plotH;
        const y = padT + plotH - bh;
        ctx.fillStyle = colors[i];
        ctx.fillRect(x, y, barW, bh);
        ctx.fillStyle = "#1f2937";
        ctx.textAlign = "center";
        ctx.textBaseline = "bottom";
        ctx.fillText(String(value), x + barW / 2, y - 4);
        ctx.textBaseline = "top";
        ctx.fillText(labels[i], x + barW / 2, padT + plotH + 8);
      }
    }

    drawEfficiencyChart();
    drawRulePassFailChart();
    renderGroupRows();
  </script>
</body>
</html>
"""


def build_group_detail_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>2x2x2 网格置物架 - 分组详情</title>
  <style>
    :root {
      --bg: #efe8d7;
      --ink: #142127;
      --card: #fcfaf4;
      --line: #c9c0af;
      --accent: #0b6b61;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: radial-gradient(circle at 15% 18%, #e5ddc9 0%, transparent 42%), var(--bg);
      font-family: "Noto Sans SC", "Microsoft YaHei", sans-serif;
    }
    .layout {
      display: grid;
      grid-template-rows: auto auto auto;
      gap: 12px;
      padding: 12px;
      min-height: 100vh;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.04);
      padding: 12px;
    }
    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .back-link {
      border: 1px solid #c7d4cf;
      border-radius: 6px;
      background: #e9f4f1;
      color: #11483f;
      text-decoration: none;
      padding: 6px 10px;
      font-size: 12px;
    }
    .title {
      font-size: 18px;
      margin: 0;
    }
    .meta {
      font-size: 12px;
      color: #35565e;
      margin-top: 6px;
    }
    .viewer-canvas {
      width: 100%;
      height: clamp(340px, 52vh, 700px);
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #f8f6ef;
      display: block;
    }
    .table-card {
      max-height: 34vh;
      min-height: 220px;
      overflow: auto;
    }
    .variant-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    .variant-table th, .variant-table td {
      border: 1px solid var(--line);
      padding: 6px;
      text-align: left;
      vertical-align: middle;
    }
    .variant-row {
      cursor: pointer;
      transition: background-color 0.15s ease;
    }
    .variant-row:hover {
      background: #eef7f4;
    }
    .variant-row.selected {
      background: #dff0ea;
      outline: 2px solid #58b7a8;
      outline-offset: -2px;
    }
    .variant-table th {
      background: #f0ebde;
      color: #284852;
      position: sticky;
      top: 0;
      z-index: 1;
    }
    .mini-top {
      width: 60px;
      height: 60px;
      border: 1px solid #d5ccbc;
      border-radius: 4px;
      background: #f8f6ef;
    }
    .eff-badge {
      display: inline-block;
      margin-left: 6px;
      padding: 1px 6px;
      border-radius: 10px;
      font-size: 11px;
      border: 1px solid transparent;
      line-height: 1.4;
    }
    .eff-pass {
      background: #e8f7f2;
      color: #0f766e;
      border-color: #99d8cc;
    }
    .eff-fail {
      background: #fff1e8;
      color: #b45309;
      border-color: #f0bd93;
    }
  </style>
</head>
<body>
  <div class="layout">
    <section class="card head">
      <div>
        <h1 class="title" id="title">分组详情</h1>
        <div class="meta" id="meta"></div>
      </div>
      <a class="back-link" href="./shelf_2x2x2_viewer.html">返回分组列表</a>
    </section>
    <section class="card">
      <canvas id="group-scene" class="viewer-canvas"></canvas>
    </section>
    <section class="card table-card">
      <table class="variant-table">
        <thead>
          <tr>
            <th>结构ID</th>
            <th>模块数量</th>
            <th>单位效率</th>
            <th>俯视图(2x2)</th>
          </tr>
        </thead>
        <tbody id="variant-body"></tbody>
      </table>
    </section>
  </div>
  <script type="module">
    const data = await fetch("./shelf_2x2x2.json").then(r => r.json());
    const THREE = await import("./vendor/three.module.js");
    const controlsModule = await import("./vendor/OrbitControls.js");
    const OrbitControls = controlsModule.OrbitControls;

    const params = new URLSearchParams(window.location.search);
    const targetKey = params.get("group_key");
    const groups = data.grouped_shelves;
    const group = groups.find(g => g.group_key === targetKey) || groups[0];
    const maxRows = data.max_boundary.rows;
    const maxCols = data.max_boundary.cols;

    function computeProjectionCountsFromCells(shelf) {
      const counts = Array.from({ length: maxRows }, () => Array(maxCols).fill(0));
      for (const cell of (shelf.occupied_cells || [])) {
        if (cell.row >= 0 && cell.row < maxRows && cell.col >= 0 && cell.col < maxCols) {
          counts[cell.row][cell.col] += 1;
        }
      }
      return counts;
    }

    const title = document.getElementById("title");
    const meta = document.getElementById("meta");
    title.textContent = group ? `分组详情: ${group.group_name}` : "分组详情";
    meta.textContent = group
      ? `结构数: ${group.count} | 杆:${group.module_counts.rod} 连接接口:${group.module_counts.connector} 隔板:${group.module_counts.panel}`
      : "没有可显示的分组";

    function colorByProjectionCount(count, absoluteMaxCount) {
      if (count <= 0) return "#d1d5db";
      const clamped = Math.min(count, absoluteMaxCount);
      const t = absoluteMaxCount <= 1 ? 1 : (clamped - 1) / (absoluteMaxCount - 1);
      const light = 78 - Math.round(t * 42);
      return `hsl(173, 74%, ${light}%)`;
    }

    function drawTopView(canvas, topView, projectionCounts) {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const rows = topView.length;
      const cols = topView[0].length;
      const pad = 8;
      const w = canvas.width;
      const h = canvas.height;
      const cw = (w - pad * 2) / cols;
      const ch = (h - pad * 2) / rows;
      const absoluteMaxCount = Math.max(1, data.max_boundary.levels);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#f8f6ef";
      ctx.fillRect(0, 0, w, h);
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const count = projectionCounts?.[r]?.[c] ?? (topView[r][c] ? 1 : 0);
          ctx.fillStyle = colorByProjectionCount(count, absoluteMaxCount);
          ctx.fillRect(pad + c * cw + 2, pad + r * ch + 2, cw - 4, ch - 4);
          if (count > 0) {
            ctx.strokeStyle = "rgba(20,33,39,0.42)";
            ctx.lineWidth = 1;
            ctx.strokeRect(pad + c * cw + 2.5, pad + r * ch + 2.5, cw - 5, ch - 5);
          }
        }
      }
    }

    const variantBody = document.getElementById("variant-body");
    if (group) {
      group.shelves.forEach((item) => {
        const tr = document.createElement("tr");
        tr.className = "variant-row";
        tr.dataset.variantId = item.variant_id;
        const t1 = document.createElement("td");
        t1.textContent = item.variant_id;
        const t2 = document.createElement("td");
        const mc = item.module_counts;
        const eff = item.storage_efficiency || { score: 0, pass: false };
        t2.textContent = `杆:${mc.rod} 连接接口:${mc.connector} 隔板:${mc.panel}`;
        const tEff = document.createElement("td");
        const effText = document.createElement("span");
        effText.textContent = Number(eff.score).toFixed(2);
        const effBadge = document.createElement("span");
        effBadge.className = `eff-badge ${eff.pass ? "eff-pass" : "eff-fail"}`;
        effBadge.textContent = eff.pass ? "通过" : "不通过";
        tEff.appendChild(effText);
        tEff.appendChild(effBadge);
        const t3 = document.createElement("td");
        const mini = document.createElement("canvas");
        mini.width = 60;
        mini.height = 60;
        mini.className = "mini-top";
        const counts = item.top_view_projection_counts || computeProjectionCountsFromCells(item);
        drawTopView(mini, item.top_view, counts);
        t3.appendChild(mini);
        tr.appendChild(t1);
        tr.appendChild(t2);
        tr.appendChild(tEff);
        tr.appendChild(t3);
        variantBody.appendChild(tr);
      });
    }

    const sceneCanvas = document.getElementById("group-scene");
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf4f2eb);
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 4000);
    // Keep shelf "upright" by treating z-axis as screen-up in the default view.
    camera.up.set(0, 0, 1);
    const renderer = new THREE.WebGLRenderer({ antialias: true, canvas: sceneCanvas });
    renderer.shadowMap.enabled = true;
    const controls = new OrbitControls(camera, sceneCanvas);
    controls.enableDamping = true;
    const stageGroup = new THREE.Group();
    scene.add(stageGroup);

    const hemi = new THREE.HemisphereLight(0xffffff, 0xbcb6ac, 0.85);
    scene.add(hemi);
    const dir = new THREE.DirectionalLight(0xffffff, 0.85);
    dir.position.set(320, -260, 420);
    dir.castShadow = true;
    dir.shadow.mapSize.set(1024, 1024);
    scene.add(dir);

    const rodMat = new THREE.MeshStandardMaterial({ color: 0x8f9ba3, roughness: 0.25, metalness: 0.85 });
    const connectorMat = new THREE.MeshStandardMaterial({ color: 0x49545c, roughness: 0.35, metalness: 0.55 });
    const panelMat = new THREE.MeshStandardMaterial({ color: 0xbd8a5a, roughness: 0.7, metalness: 0.08 });
    const shelfRenderMap = new Map();
    let cameraAnim = null;
    let selectedVariantId = null;
    let focusDistance = 220;

    function fitRendererToCanvas() {
      const width = sceneCanvas.clientWidth;
      const height = sceneCanvas.clientHeight;
      if (width === 0 || height === 0) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }

    function addShelfMeshes(parent, shelf, offsetX, offsetY) {
      const shelfRoot = new THREE.Group();
      parent.add(shelfRoot);
      const cellW = 32;
      const cellD = 32;
      const cellH = 32;
      const maxRows = data.max_boundary.rows;
      const maxCols = data.max_boundary.cols;
      const originX = offsetX - (maxCols * cellD) / 2;
      const originY = offsetY - (maxRows * cellW) / 2;
      const originZ = 0;

      const occupied = shelf.occupied_cells.map((c) => ({ row: c.row, col: c.col, level: c.level }));
      const derived = shelf.derived_structure || { rod_segments: [], required_connectors: [] };
      const hasRod = shelf.combo.includes("rod");
      const hasPanel = shelf.combo.includes("panel");
      const hasConnector = shelf.combo.includes("connector");
      const rodRadius = 1.1;
      const connectorRadius = 1.8;

      function addCylinderBetween(a, b, radius, mat, part) {
        const av = new THREE.Vector3(a.x, a.y, a.z);
        const bv = new THREE.Vector3(b.x, b.y, b.z);
        const len = av.distanceTo(bv);
        if (len < 0.001) return;
        const geom = new THREE.CylinderGeometry(radius, radius, len, 14);
        const mesh = new THREE.Mesh(geom, mat.clone());
        mesh.userData.part = part;
        mesh.position.copy(av.clone().add(bv).multiplyScalar(0.5));
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), bv.clone().sub(av).normalize());
        mesh.castShadow = true;
        shelfRoot.add(mesh);
      }

      if (hasRod) {
        for (const seg of derived.rod_segments) {
          const x = originX + seg.col_edge * cellD;
          const y = originY + seg.row_edge * cellW;
          const z0 = originZ + seg.level * cellH;
          const z1 = originZ + (seg.level + 1) * cellH;
          addCylinderBetween({ x, y, z: z0 }, { x, y, z: z1 }, rodRadius, rodMat, "rod");
        }
      }

      if (hasConnector) {
        for (const p of derived.required_connectors) {
          const joint = new THREE.Mesh(new THREE.SphereGeometry(connectorRadius, 12, 12), connectorMat.clone());
          joint.position.set(
            originX + p.col_edge * cellD,
            originY + p.row_edge * cellW,
            originZ + p.z * cellH
          );
          joint.userData.part = "connector";
          joint.castShadow = true;
          shelfRoot.add(joint);
        }
      }

      for (const cell of occupied) {
        if (hasPanel) {
          const x = originX + cell.col * cellD;
          const y = originY + cell.row * cellW;
          const z = originZ + cell.level * cellH;
          const boardThickness = 2.2;
          const board = new THREE.Mesh(
            new THREE.BoxGeometry(cellD * 0.9, cellW * 0.9, boardThickness),
            panelMat.clone()
          );
          board.userData.part = "panel";
          board.position.set(x + cellD / 2, y + cellW / 2, z + cellH - boardThickness / 2);
          board.castShadow = true;
          board.receiveShadow = true;
          shelfRoot.add(board);
        }
      }

      const bbox = new THREE.Box3().setFromObject(shelfRoot);
      const center = bbox.getCenter(new THREE.Vector3());
      const size = bbox.getSize(new THREE.Vector3());
      return { root: shelfRoot, center, size };
    }

    function setVariantSelection(variantId) {
      selectedVariantId = variantId;
      document.querySelectorAll(".variant-row").forEach((row) => {
        row.classList.toggle("selected", row.dataset.variantId === variantId);
      });
      for (const [id, info] of shelfRenderMap.entries()) {
        const isActive = id === variantId;
        info.root.traverse((obj) => {
          if (!obj.isMesh || !obj.material) return;
          const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
          const part = obj.userData.part || "rod";
          for (const mat of mats) {
            if ("transparent" in mat) mat.transparent = false;
            if ("opacity" in mat) mat.opacity = 1.0;
            if ("depthWrite" in mat) mat.depthWrite = true;
            if ("color" in mat) {
              if (isActive) {
                if (part === "rod") mat.color.set(0x0f172a);
                else if (part === "connector") mat.color.set(0x22c55e);
                else if (part === "panel") mat.color.set(0xf59e0b);
              } else {
                if (part === "rod") mat.color.set(0x9ca3af);
                else if (part === "connector") mat.color.set(0xd1d5db);
                else if (part === "panel") mat.color.set(0xe5e7eb);
              }
            }
            if ("emissive" in mat) {
              mat.emissive.set(isActive ? 0x111827 : 0x000000);
              mat.emissiveIntensity = isActive ? 0.08 : 0.0;
            }
          }
        });
      }
      const hit = shelfRenderMap.get(variantId);
      if (!hit) return;
      const target = hit.center.clone();
      const nextPosition = target.clone().add(new THREE.Vector3(0, -focusDistance, focusDistance * 0.55));
      cameraAnim = {
        start: performance.now(),
        duration: 420,
        fromPos: camera.position.clone(),
        toPos: nextPosition,
        fromTarget: controls.target.clone(),
        toTarget: target,
      };
    }

    function bindVariantListInteraction() {
      document.querySelectorAll(".variant-row").forEach((row) => {
        row.addEventListener("click", () => {
          setVariantSelection(row.dataset.variantId);
        });
      });
    }

    function updateCameraAnimation(nowMs) {
      if (!cameraAnim) return;
      const elapsed = nowMs - cameraAnim.start;
      const t = Math.max(0, Math.min(1, elapsed / cameraAnim.duration));
      const eased = 1 - Math.pow(1 - t, 3);
      camera.position.lerpVectors(cameraAnim.fromPos, cameraAnim.toPos, eased);
      controls.target.lerpVectors(cameraAnim.fromTarget, cameraAnim.toTarget, eased);
      if (t >= 1) {
        cameraAnim = null;
      }
    }

    if (group) {
      const count = group.shelves.length;
      const cols = Math.ceil(Math.sqrt(count));
      const rows = Math.ceil(count / cols);
      const gapX = 150;
      const gapY = 150;
      group.shelves.forEach((shelf, idx) => {
        const r = Math.floor(idx / cols);
        const c = idx % cols;
        const ox = (c - (cols - 1) / 2) * gapX;
        const oy = (r - (rows - 1) / 2) * gapY;
        const renderInfo = addShelfMeshes(stageGroup, shelf, ox, oy);
        shelfRenderMap.set(shelf.variant_id, renderInfo);
      });

      const span = Math.max(cols * gapX, rows * gapY);
      const eye = Math.max(280, span * 1.1);
      focusDistance = Math.max(130, eye * 0.55);
      // Default to a straight, upright front view (not oblique).
      camera.position.set(0, -eye, eye * 0.5);
      controls.target.set(0, 0, 32);
      controls.update();
      bindVariantListInteraction();
      if (group.shelves.length > 0) {
        setVariantSelection(group.shelves[0].variant_id);
      }
    }

    function animate(nowMs) {
      fitRendererToCanvas();
      updateCameraAnimation(nowMs);
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    window.addEventListener("resize", fitRendererToCanvas);
    animate();
  </script>
</body>
</html>
"""


def export_web_artifacts(snapshot: dict[str, Any], out_dir: Path) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    vendor_dir = out_dir / "vendor"
    vendor_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2("src/web_vendor/three.module.js", vendor_dir / "three.module.js")
    shutil.copy2("src/web_vendor/OrbitControls.js", vendor_dir / "OrbitControls.js")

    json_path = out_dir / "shelf_2x2x2.json"
    list_html_path = out_dir / "shelf_2x2x2_viewer.html"
    detail_html_path = out_dir / "shelf_2x2x2_group_detail.html"
    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    list_html_path.write_text(build_viewer_html(), encoding="utf-8")
    detail_html_path.write_text(build_group_detail_html(), encoding="utf-8")
    return json_path, list_html_path, detail_html_path


def serve_directory(directory: Path, port: int) -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Web viewer running: http://127.0.0.1:{port}/shelf_2x2x2_viewer.html")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 2x2x2 grid shelf variants and viewer.")
    parser.add_argument("--serve", action="store_true", help="serve docs folder for web viewing")
    parser.add_argument("--port", type=int, default=8000, help="web server port")
    args = parser.parse_args()

    goal = Goal("Enumerate all valid grid shelves within 2x2x2 max boundary")
    boundary = BoundaryDefinition(
        layers_n=2,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=80.0, depth=35.0, height=30.0),
        opening_o=Opening2D(width=65.0, height=28.0),
        footprint_a=Footprint2D(width=90.0, depth=40.0),
    )

    rules = CombinationRules.default()
    all_combos = CombinationRules.all_subsets()
    valid_combos = rules.valid_subsets()

    variants = enumerate_grid_shelf_variants(2, 2, 2, rules)
    qualified_variants: list[GridShelfVariant] = []
    for variant in variants:
        geometry_ok = variant.model.validate_geometry_rules().passed()
        projection_ok = projection_parallel_validation(variant.model)["panel_parallel_projection"]
        if geometry_ok and projection_ok:
            qualified_variants.append(variant)

    grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for variant in qualified_variants:
        item = variant_to_payload(variant)
        counts = item["module_counts"]
        key = (counts["rod"], counts["connector"], counts["panel"])
        grouped.setdefault(key, []).append(item)

    pass_count = len(qualified_variants)
    fail_count = max(0, len(variants) - pass_count)

    grouped_shelves = [
        {
            "group_key": f"rod={key[0]},connector={key[1]},panel={key[2]}",
            "group_name": f"杆{items[0]['module_counts']['rod']} / 连接接口{items[0]['module_counts']['connector']} / 隔板{items[0]['module_counts']['panel']}",
            "module_counts": items[0]["module_counts"],
            "count": len(items),
            "top_view_groups": [
                {
                    "top_view": json.loads(top_key),
                    "count": len(top_items),
                }
                for top_key, top_items in sorted(
                    _group_top_views(items).items(),
                    key=lambda pair: len(pair[1]),
                    reverse=True,
                )
            ],
            "shelves": items,
        }
        for key, items in sorted(grouped.items(), key=lambda pair: pair[0])
    ]

    sample_variant = next(
        (item for item in qualified_variants if (item.rows, item.cols, item.levels) == (2, 2, 2)),
        qualified_variants[0] if qualified_variants else None,
    )
    two_layer_candidates = [
        item
        for item in qualified_variants
        if item.levels == 2 and variant_top_view(item) == [[1, 1], [1, 1]]
    ]
    two_layer_max_footprint_variant = (
        max(two_layer_candidates, key=lambda item: len(item.model.cells))
        if two_layer_candidates
        else None
    )
    candidate_combo = {Module.ROD, Module.CONNECTOR, Module.PANEL}
    verification_input = VerificationInput(
        boundary=boundary,
        combo=candidate_combo,
        valid_combinations=valid_combos,
        baseline_efficiency=1.0,
        target_efficiency=1.22,
        geometry=sample_variant.model.validate_geometry_rules() if sample_variant is not None else None,
    )
    verification_result = verify(verification_input)
    logic_record = build_logic_record(goal, boundary, verification_result.passed)
    logic_record.export_json("docs/logic_record.json")

    snapshot = {
        "goal": goal.to_dict(),
        "boundary": boundary.to_dict(),
        "max_boundary": {"rows": 2, "cols": 2, "levels": 2},
        "strict_mapping": strict_mapping_meta(),
        "all_combinations": [
            {
                "combo": modules_to_list(item),
                "valid": frozenset(item) in {frozenset(v) for v in valid_combos},
            }
            for item in all_combos
        ],
        "valid_combinations": [modules_to_list(item) for item in valid_combos],
        "instance_2layer_max_4cells": (
            variant_to_payload(two_layer_max_footprint_variant)
            if two_layer_max_footprint_variant is not None
            else None
        ),
        "rule_statistics": {
            "scope": "enumerated_variants_after_shape_dedup",
            "total": len(variants),
            "pass_count": pass_count,
            "fail_count": fail_count,
        },
        "total_shelves": len(qualified_variants),
        "grouped_shelves": grouped_shelves,
        "verification": verification_result.to_dict(),
        "logic_record_path": "docs/logic_record.json",
    }

    json_path, list_html_path, detail_html_path = export_web_artifacts(snapshot, Path("docs"))
    snapshot["web"] = {
        "json": str(json_path).replace("\\", "/"),
        "viewer_list": str(list_html_path).replace("\\", "/"),
        "viewer_detail": str(detail_html_path).replace("\\", "/"),
    }

    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    if args.serve:
        serve_directory(Path("docs"), args.port)


if __name__ == "__main__":
    main()


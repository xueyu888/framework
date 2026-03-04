from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_N = 2
DEFAULT_X = 30.0
DEFAULT_Y = 30.0
DEFAULT_H = 30.0

# Engineering-approx reference capacities (material-agnostic in model):
# values are external properties and can be tuned in interactive viewer.
DEFAULT_EXTERNAL_PROPERTIES = {
    "rod_capacity": 60.0,
    "support_panel_capacity": 90.0,
    "connector_capacity": 45.0,
    "board_capacity": 120.0,
    "board_deflection_capacity": 100.0,
}

CORNERS = ("FL", "FR", "BR", "BL")
SIDES = ("front", "right", "back", "left")
SIDE_CORNERS = {
    "front": ("FL", "FR"),
    "back": ("BL", "BR"),
    "left": ("FL", "BL"),
    "right": ("FR", "BR"),
}

ROTATE_CORNER_90 = {"FL": "FR", "FR": "BR", "BR": "BL", "BL": "FL"}
ROTATE_SIDE_90 = {"front": "right", "right": "back", "back": "left", "left": "front"}


@dataclass(frozen=True)
class LayerPattern:
    rods: tuple[str, ...]
    side_panels: tuple[str, ...]


@dataclass(frozen=True)
class Combo:
    layers: tuple[LayerPattern, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate rotation-dedup shelf combos for arbitrary layer count (N)."
    )
    parser.add_argument("--layers", type=int, default=DEFAULT_N, help="Layer count N")
    parser.add_argument("--x", type=float, default=DEFAULT_X, help="Per-layer span x")
    parser.add_argument("--y", type=float, default=DEFAULT_Y, help="Per-layer span y")
    parser.add_argument("--h", type=float, default=DEFAULT_H, help="Single-layer height h")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="Output directory path (default: docs/diagrams/N{N}_x{X}_y{Y}_h{H}_panelmax{H})",
    )
    args = parser.parse_args()

    if args.layers <= 0:
        parser.error("--layers must be > 0")
    if args.x <= 0 or args.y <= 0 or args.h <= 0:
        parser.error("--x, --y, --h must all be > 0")
    return args


def fmt_num(value: float) -> str:
    return f"{value:g}"


def default_output_dir(n: int, x: float, y: float, h: float) -> Path:
    return ROOT / "docs" / "diagrams" / f"N{n}_x{fmt_num(x)}_y{fmt_num(y)}_h{fmt_num(h)}_panelmax{fmt_num(h)}"


def resolve_output_dir(n: int, x: float, y: float, h: float, output_dir: str) -> Path:
    if not output_dir:
        return default_output_dir(n, x, y, h)
    path = Path(output_dir)
    if not path.is_absolute():
        path = ROOT / path
    return path


def corner_xy(x: float, y: float) -> dict[str, tuple[float, float]]:
    return {
        "FL": (0.0, 0.0),
        "FR": (x, 0.0),
        "BL": (0.0, y),
        "BR": (x, y),
    }


def powerset(items: tuple[str, ...]) -> list[tuple[str, ...]]:
    out: list[tuple[str, ...]] = []
    for mask in range(1 << len(items)):
        out.append(tuple(items[i] for i in range(len(items)) if (mask >> i) & 1))
    return out


def corners_from_side_panels(side_panels: tuple[str, ...]) -> set[str]:
    covered: set[str] = set()
    for side in side_panels:
        c1, c2 = SIDE_CORNERS[side]
        covered.add(c1)
        covered.add(c2)
    return covered


def open_sides(side_panels: tuple[str, ...]) -> list[str]:
    return [side for side in SIDES if side not in side_panels]


def valid_layer_pattern(rods: tuple[str, ...], side_panels: tuple[str, ...]) -> bool:
    # Keep panel support complexity bounded: at most two side support panels per layer.
    if len(side_panels) > 2:
        return False

    # For adjacent panels, shared corner support is counted once (no double counting).
    panel_corner_count: dict[str, int] = {corner: 0 for corner in CORNERS}
    for side in side_panels:
        for corner in SIDE_CORNERS[side]:
            panel_corner_count[corner] += 1
    overlap_correction = sum(max(0, count - 1) for count in panel_corner_count.values())

    # R2: E(rod)=1, E(panel)=2, with overlap correction on shared panel corners.
    equivalent_total = len(rods) + 2 * len(side_panels) - overlap_correction
    if equivalent_total != 4:
        return False

    # R2 strong condition: full 4-corner support coverage is mandatory.
    if (set(rods) | corners_from_side_panels(side_panels)) != set(CORNERS):
        return False

    # R7: at least one side open.
    if len(open_sides(side_panels)) < 1:
        return False

    # Side support panel height <= h is enforced by generation model (one-layer panel).
    return True


def rotate_layer_pattern_90(pattern: LayerPattern) -> LayerPattern:
    rods = tuple(sorted(ROTATE_CORNER_90[item] for item in pattern.rods))
    side_panels = tuple(sorted(ROTATE_SIDE_90[item] for item in pattern.side_panels))
    return LayerPattern(rods=rods, side_panels=side_panels)


def rotate_combo_90(combo: Combo) -> Combo:
    return Combo(layers=tuple(rotate_layer_pattern_90(layer) for layer in combo.layers))


ComboKey = tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]


def combo_key(combo: Combo) -> ComboKey:
    return tuple((layer.rods, layer.side_panels) for layer in combo.layers)


def key_to_combo(key: ComboKey) -> Combo:
    return Combo(
        layers=tuple(
            LayerPattern(rods=item[0], side_panels=item[1])
            for item in key
        )
    )


def canonical_key_under_rotation(combo: Combo) -> ComboKey:
    cands: list[ComboKey] = []
    cur = combo
    for _ in range(4):
        cands.append(combo_key(cur))
        cur = rotate_combo_90(cur)
    return min(cands)


def combo_label(combo: Combo) -> str:
    labels: list[str] = []
    for idx, layer in enumerate(combo.layers, start=1):
        rods = "-".join(layer.rods) if layer.rods else "无"
        panels = "-".join(layer.side_panels) if layer.side_panels else "无"
        labels.append(f"第{idx}层(杆:{rods}|支撑板:{panels})")
    return " ".join(labels)


def build_layer_patterns() -> list[LayerPattern]:
    patterns: list[LayerPattern] = []
    for rods in powerset(CORNERS):
        for side_panels in powerset(SIDES):
            rods_sorted = tuple(sorted(rods))
            side_panels_sorted = tuple(sorted(side_panels))
            if valid_layer_pattern(rods_sorted, side_panels_sorted):
                patterns.append(LayerPattern(rods=rods_sorted, side_panels=side_panels_sorted))
    return sorted(
        set(patterns),
        key=lambda item: (len(item.rods), len(item.side_panels), item.rods, item.side_panels),
    )


def merge_corner_rod_segments(combo: Combo, h: float) -> dict[str, list[tuple[float, float]]]:
    merged: dict[str, list[tuple[float, float]]] = {corner: [] for corner in CORNERS}
    for corner in CORNERS:
        segs: list[tuple[float, float]] = []
        for layer_idx, layer in enumerate(combo.layers):
            if corner in layer.rods:
                segs.append((layer_idx * h, (layer_idx + 1) * h))
        if not segs:
            continue
        segs.sort()
        cur0, cur1 = segs[0]
        for z0, z1 in segs[1:]:
            if abs(z0 - cur1) < 1e-9:
                cur1 = z1
            else:
                merged[corner].append((cur0, cur1))
                cur0, cur1 = z0, z1
        merged[corner].append((cur0, cur1))
    return merged


def side_panel_quads(
    combo: Combo,
    x: float,
    y: float,
    h: float,
) -> list[tuple[list[tuple[float, float, float]], int]]:
    quads: list[tuple[list[tuple[float, float, float]], int]] = []
    xy = corner_xy(x, y)
    for level_idx, layer in enumerate(combo.layers, start=1):
        z0 = (level_idx - 1) * h
        z1 = level_idx * h
        for side in layer.side_panels:
            c1, c2 = SIDE_CORNERS[side]
            x1, y1 = xy[c1]
            x2, y2 = xy[c2]
            quads.append(([(x1, y1, z0), (x2, y2, z0), (x2, y2, z1), (x1, y1, z1)], level_idx))
    return quads


def load_board_quads(n: int, x: float, y: float, h: float) -> list[list[tuple[float, float, float]]]:
    quads: list[list[tuple[float, float, float]]] = []
    for level_idx in range(1, n + 1):
        z = level_idx * h
        quads.append([(0.0, 0.0, z), (x, 0.0, z), (x, y, z), (0.0, y, z)])
    return quads


def project_point(point: tuple[float, float, float]) -> tuple[float, float]:
    ax = math.radians(25)
    ay = math.radians(-36)
    x0, y0, z0 = point
    x1 = x0 * math.cos(ay) + z0 * math.sin(ay)
    y1 = y0
    z1 = -x0 * math.sin(ay) + z0 * math.cos(ay)
    x2 = x1
    y2 = y1 * math.cos(ax) - z1 * math.sin(ax)
    return (x2, -y2)


def draw_preview_png(combo: Combo, out_path: Path, title: str, x: float, y: float, h: float) -> None:
    side_quads = side_panel_quads(combo, x, y, h)
    board_quads = load_board_quads(len(combo.layers), x, y, h)
    rods = merge_corner_rod_segments(combo, h)
    xy = corner_xy(x, y)

    pts: list[tuple[float, float]] = []
    for quad in board_quads:
        pts.extend(project_point(p) for p in quad)
    for quad, _ in side_quads:
        pts.extend(project_point(p) for p in quad)
    for corner in CORNERS:
        x0, y0 = xy[corner]
        for z0, z1 in rods[corner]:
            pts.extend([project_point((x0, y0, z0)), project_point((x0, y0, z1))])

    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)

    width, height, pad = 760, 560, 60
    sx = (width - 2 * pad) / max(maxx - minx, 1e-6)
    sy = (height - 2 * pad) / max(maxy - miny, 1e-6)
    scale = min(sx, sy)

    def to_canvas(point3: tuple[float, float, float]) -> tuple[int, int]:
        xp, yp = project_point(point3)
        return (int((xp - minx) * scale + pad), int((yp - miny) * scale + pad))

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img, "RGBA")

    for quad, level_idx in side_quads:
        _ = level_idx
        draw.polygon([to_canvas(p) for p in quad], fill=(255, 255, 255, 210), outline=(107, 114, 128, 255), width=2)

    for quad in board_quads:
        draw.polygon([to_canvas(p) for p in quad], fill=(255, 255, 255, 220), outline=(107, 114, 128, 255), width=2)

    for corner in CORNERS:
        x0, y0 = xy[corner]
        for z0, z1 in rods[corner]:
            draw.line([to_canvas((x0, y0, z0)), to_canvas((x0, y0, z1))], fill=(75, 85, 99, 255), width=5)

    open_desc = " | ".join(
        f"L{idx} open={open_sides(layer.side_panels)}"
        for idx, layer in enumerate(combo.layers, start=1)
    )
    draw.text((16, 12), title, fill=(0, 0, 0, 255))
    draw.text((16, 34), open_desc, fill=(0, 0, 0, 255))
    img.save(out_path)


def write_obj(combo: Combo, out_path: Path, x: float, y: float, h: float) -> None:
    vertices: list[tuple[float, float, float]] = []
    lines: list[tuple[int, int]] = []
    faces: list[tuple[int, int, int, int]] = []

    rods = merge_corner_rod_segments(combo, h)
    xy = corner_xy(x, y)

    for corner in CORNERS:
        x0, y0 = xy[corner]
        for z0, z1 in rods[corner]:
            i1 = len(vertices) + 1
            vertices.append((x0, y0, z0))
            i2 = len(vertices) + 1
            vertices.append((x0, y0, z1))
            lines.append((i1, i2))

    for quad, _ in side_panel_quads(combo, x, y, h):
        a = len(vertices) + 1
        vertices.append(quad[0])
        b = len(vertices) + 1
        vertices.append(quad[1])
        c = len(vertices) + 1
        vertices.append(quad[2])
        d = len(vertices) + 1
        vertices.append(quad[3])
        faces.append((a, b, c, d))

    for quad in load_board_quads(len(combo.layers), x, y, h):
        a = len(vertices) + 1
        vertices.append(quad[0])
        b = len(vertices) + 1
        vertices.append(quad[1])
        c = len(vertices) + 1
        vertices.append(quad[2])
        d = len(vertices) + 1
        vertices.append(quad[3])
        faces.append((a, b, c, d))

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# generated shelf combo\n")
        for x0, y0, z0 in vertices:
            f.write(f"v {x0:.4f} {y0:.4f} {z0:.4f}\n")
        for a, b in lines:
            f.write(f"l {a} {b}\n")
        for a, b, c, d in faces:
            f.write(f"f {a} {b} {c} {d}\n")


def build_interactive_html(items: list[dict], n: int, x: float, y: float, h: float) -> str:
    combos_json = json.dumps(items, ensure_ascii=False)
    ext_props_json = json.dumps(DEFAULT_EXTERNAL_PROPERTIES, ensure_ascii=False)
    return """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>置物架组合 3D 可视化（承载评估）</title>
  <style>
    :root {
      --bg-a: #eaf0f8;
      --bg-b: #dce6f3;
      --card: rgba(255,255,255,0.92);
      --line: #d8e0ea;
      --text: #1f2937;
      --sub: #4b5563;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --danger: #b91c1c;
    }
    html, body {
      margin: 0;
      height: 100%;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
      background: radial-gradient(circle at 16% 18%, var(--bg-a), var(--bg-b));
      color: var(--text);
    }
    #app {
      display: grid;
      grid-template-columns: 460px 1fr;
      height: 100%;
    }
    #panel {
      padding: 14px 14px 22px;
      background: var(--card);
      border-right: 1px solid var(--line);
      overflow: auto;
      backdrop-filter: blur(3px);
    }
    #viewer {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 290px;
      gap: 0;
      overflow: hidden;
      background: linear-gradient(180deg, #edf2f9 0%, #e7edf7 100%);
    }
    #stage {
      position: relative;
      overflow: hidden;
      min-width: 0;
    }
    #cv {
      width: 100%;
      height: 100%;
      display: block;
      background: linear-gradient(180deg, #eef3fa 0%, #e8eef8 100%);
    }
    #faultPane {
      border-left: 1px solid var(--line);
      background: rgba(248, 250, 252, 0.88);
      padding: 12px;
      overflow: auto;
    }
    #faultBox {
      display: none;
      border: 1px solid #fecaca;
      background: #fef2f2;
      border-radius: 12px;
      padding: 12px;
      color: #7f1d1d;
      font-size: 12px;
      line-height: 1.45;
      box-shadow: 0 6px 20px rgba(153, 27, 27, 0.12);
    }
    #faultBox h4 {
      margin: 0 0 6px 0;
      font-size: 14px;
      color: #991b1b;
    }
    #faultBox ul {
      margin: 6px 0 0 16px;
      padding: 0;
    }
    #faultHint {
      color: #475569;
      font-size: 12px;
      line-height: 1.4;
      background: #ffffff;
      border: 1px dashed #cbd5e1;
      border-radius: 10px;
      padding: 10px;
    }
    .row { margin-bottom: 10px; }
    .row-tight { margin-bottom: 6px; }
    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      white-space: pre-wrap;
    }
    .grid2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }
    .grid3 {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 6px;
    }
    .section {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px;
      background: linear-gradient(180deg, #ffffff, #f8fbff);
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    }
    .label {
      font-size: 12px;
      color: #374151;
      margin-bottom: 4px;
    }
    input, select, button {
      width: 100%;
      box-sizing: border-box;
      padding: 7px 9px;
      border: 1px solid #bfccdd;
      border-radius: 8px;
      background: #fff;
      color: var(--text);
    }
    button {
      cursor: pointer;
      border-color: #9fb5d4;
      background: linear-gradient(180deg, #ffffff, #edf4ff);
      transition: all 0.18s ease;
    }
    button:hover {
      border-color: #7ea1d0;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12);
    }
    .actions {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 6px;
    }
    .legend {
      height: 10px;
      border: 1px solid #c9d4e3;
      border-radius: 6px;
      background: linear-gradient(to right, #ffffff 0%, #ffeb3b 60%, #ff9800 80%, #dc2626 100%);
    }
    .title {
      margin: 0 0 10px 0;
      font-size: 19px;
      letter-spacing: 0.2px;
      color: #0f172a;
    }
    .subline {
      color: var(--sub);
      font-size: 12px;
    }
    .meta {
      font-size: 13px;
      padding: 8px 10px;
      border: 1px solid #d8e2f0;
      border-radius: 10px;
      background: #f7faff;
    }
    @media (max-width: 1200px) {
      #app {
        grid-template-columns: 1fr;
      }
      #viewer {
        grid-template-columns: minmax(0, 1fr);
        min-height: 60vh;
      }
      #faultPane {
        border-left: none;
        border-top: 1px solid var(--line);
      }
    }
  </style>
</head>
<body>
<div id=\"app\">
  <div id=\"panel\">
    <h3 class=\"title\">置物架 3D 承载评估</h3>
    <div class=\"row meta\" id=\"sceneMeta\">N=__N__, x=__X__, y=__Y__, h=__H__</div>
    <div class=\"row meta\">去重后组合数：<b>__COUNT__</b></div>

    <div class=\"row section\">
      <div style=\"font-weight:600; margin-bottom:8px;\">横向拼接参数</div>
      <div class=\"grid2\">
        <div>
          <div class=\"label\">nx（X 方向）</div>
          <input id=\"nxCount\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">ny（Y 方向）</div>
          <input id=\"nyCount\" type=\"number\" />
        </div>
      </div>
      <div class=\"subline\" id=\"tileInfo\" style=\"margin-top:6px;\">总单元数：1</div>
    </div>

    <div class=\"row section\">
      <div class=\"actions\">
        <button id=\"prevBtn\">上一个</button>
        <button id=\"nextBtn\">下一个</button>
        <button id=\"fitBtn\">自适应</button>
      </div>
      <div class=\"row-tight\" style=\"margin-top:8px;\">
        <select id=\"comboSelect\"></select>
      </div>
    </div>

    <div class=\"row section\">
      <div style=\"font-weight:600; margin-bottom:8px;\">载荷方块</div>
      <div class=\"grid3\">
        <div>
          <div class=\"label\">方块数量</div>
          <input id=\"cubeCount\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">当前方块</div>
          <select id=\"cubeIndex\"></select>
        </div>
        <div>
          <div class=\"label\">层号</div>
          <input id=\"cubeLayer\" type=\"number\" />
        </div>
      </div>
      <div class=\"grid3\" style=\"margin-top:6px;\">
        <div>
          <div class=\"label\">重量</div>
          <input id=\"cubeWeight\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">尺寸 z</div>
          <input id=\"cubeSizeZ\" type=\"number\" />
        </div>
      </div>
      <div class=\"grid2\" style=\"margin-top:6px;\">
        <div>
          <div class=\"label\">尺寸 x</div>
          <input id=\"cubeSizeX\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">尺寸 y</div>
          <input id=\"cubeSizeY\" type=\"number\" />
        </div>
      </div>
      <div class=\"grid2\" style=\"margin-top:6px;\">
        <div>
          <div class=\"label\">中心 x</div>
          <input id=\"cubePosX\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">中心 y</div>
          <input id=\"cubePosY\" type=\"number\" />
        </div>
      </div>
    </div>

    <div class=\"row section\">
      <div style=\"font-weight:600; margin-bottom:8px;\">外部基承载参数</div>
      <div class=\"grid2\">
        <div>
          <div class=\"label\">杆容量</div>
          <input id=\"capRod\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">支撑板容量</div>
          <input id=\"capPanel\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">连接件容量</div>
          <input id=\"capConnector\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">层板容量</div>
          <input id=\"capBoard\" type=\"number\" />
        </div>
        <div>
          <div class=\"label\">层板挠度容量</div>
          <input id=\"capBoardDeflect\" type=\"number\" />
        </div>
        <div style=\"display:flex; align-items:end;\">
          <button id=\"resetCapsBtn\">恢复默认容量</button>
        </div>
      </div>
    </div>

    <div class=\"row section\">
      <div class=\"label\" style=\"margin-bottom:6px;\">受力图例（白 -> 红）</div>
      <div class=\"legend\"></div>
      <div style=\"font-size:12px;color:#4b5563;margin-top:4px;\">利用率：0.0 -> 1.0+（越接近极限越红）</div>
    </div>

    <div class=\"row mono\" id=\"status\" style=\"color:#b91c1c;\">正在初始化可视化...</div>
    <div class=\"row mono\" id=\"info\"></div>
    <div class=\"row\" style=\"font-size:12px;color:#4b5563;\">
      左键拖动：旋转 | 左键拖动方块：移动 x/y | 滚轮：缩放 | 右键拖动：平移
    </div>
  </div>
  <div id=\"viewer\">
    <div id=\"stage\"><canvas id=\"cv\"></canvas></div>
    <div id=\"faultPane\">
      <div id=\"faultHint\">当前未检测到超限。可通过增加方块重量、调整位置或降低容量参数触发故障诊断。</div>
      <div id=\"faultBox\"></div>
    </div>
  </div>
</div>

<script id=\"combo-data\" type=\"application/json\">__COMBOS_JSON__</script>
<script>
let combos = [];
const EXTERNAL_DEFAULTS = __EXT_PROPS__;
const statusEl = document.getElementById('status');
function showStatus(msg, isError) {
  if (!statusEl) return;
  statusEl.style.color = isError ? '#b91c1c' : '#065f46';
  statusEl.textContent = msg || '';
}
try {
  const raw = document.getElementById('combo-data').textContent || '[]';
  combos = JSON.parse(raw);
} catch (err) {
  showStatus('组合数据解析失败：' + String(err), true);
}
window.addEventListener('error', function (e) {
  showStatus('页面脚本错误：' + String(e.message) + ' @' + String(e.lineno) + ':' + String(e.colno), true);
});

const N = __N__, X = __X__, Y = __Y__, H = __H__;
const TOTAL_H = N * H;
const CORNERS = ['FL', 'FR', 'BL', 'BR'];
const sideCorners = {
  front: ['FL', 'FR'],
  back: ['BL', 'BR'],
  left: ['FL', 'BL'],
  right: ['FR', 'BR']
};
const cornerXY = {
  FL: [0, 0],
  FR: [X, 0],
  BL: [0, Y],
  BR: [X, Y]
};

const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const viewer = document.getElementById('viewer');
const stage = document.getElementById('stage');
const faultBox = document.getElementById('faultBox');
const faultHint = document.getElementById('faultHint');

const controls = {
  sceneMeta: document.getElementById('sceneMeta'),
  tileInfo: document.getElementById('tileInfo'),
  nxCount: document.getElementById('nxCount'),
  nyCount: document.getElementById('nyCount'),
  cubeCount: document.getElementById('cubeCount'),
  cubeIndex: document.getElementById('cubeIndex'),
  cubeLayer: document.getElementById('cubeLayer'),
  cubeWeight: document.getElementById('cubeWeight'),
  cubeSizeX: document.getElementById('cubeSizeX'),
  cubeSizeY: document.getElementById('cubeSizeY'),
  cubeSizeZ: document.getElementById('cubeSizeZ'),
  cubePosX: document.getElementById('cubePosX'),
  cubePosY: document.getElementById('cubePosY'),
  capRod: document.getElementById('capRod'),
  capPanel: document.getElementById('capPanel'),
  capConnector: document.getElementById('capConnector'),
  capBoard: document.getElementById('capBoard'),
  capBoardDeflect: document.getElementById('capBoardDeflect'),
  resetCapsBtn: document.getElementById('resetCapsBtn'),
};

let yaw = -0.9;
let pitch = 0.55;
let zoom = 8.2;
let panX = 0;
let panY = 0;
let current = 0;
let lastEval = null;
let faultMarkers = [];

function makeDefaultCube() {
  return {
    layer: 1,
    weight: 20.0,
    sizeX: Math.max(4.0, X * 0.35),
    sizeY: Math.max(4.0, Y * 0.35),
    sizeZ: Math.max(4.0, H * 0.45),
    posX: X / 2,
    posY: Y / 2,
  };
}

let loadState = {
  layout: {
    nx: 1,
    ny: 1,
  },
  cubes: [makeDefaultCube()],
  activeCube: 0,
  caps: {
    rod: EXTERNAL_DEFAULTS.rod_capacity,
    panel: EXTERNAL_DEFAULTS.support_panel_capacity,
    connector: EXTERNAL_DEFAULTS.connector_capacity,
    board: EXTERNAL_DEFAULTS.board_capacity,
    boardDeflect: EXTERNAL_DEFAULTS.board_deflection_capacity,
  },
};

function sceneWidth() {
  return X * Math.max(1, Math.round(loadState.layout.nx || 1));
}
function sceneDepth() {
  return Y * Math.max(1, Math.round(loadState.layout.ny || 1));
}
function cellTag(ix, iy) {
  return `C${ix + 1}-${iy + 1}`;
}
function keyInCell(ix, iy, localKey) {
  return `${cellTag(ix, iy)}|${localKey}`;
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function num(v, fallback) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}
function add(map, key, value) {
  map[key] = (map[key] || 0) + value;
}
function lerp(a, b, t) { return a + (b - a) * t; }
function getActiveCube() {
  if (!loadState.cubes.length) loadState.cubes.push(makeDefaultCube());
  loadState.activeCube = clamp(loadState.activeCube, 0, loadState.cubes.length - 1);
  return loadState.cubes[loadState.activeCube];
}

function stressRgb(util) {
  const u = Math.max(0, util);
  let c0 = [255, 255, 255];
  let c1 = [255, 255, 255];
  let t = 0;
  if (u <= 0.6) {
    c0 = [255, 255, 255];
    c1 = [255, 235, 59];
    t = u / 0.6;
  } else if (u <= 0.8) {
    c0 = [255, 235, 59];
    c1 = [245, 158, 11];
    t = (u - 0.6) / 0.2;
  } else if (u <= 1.0) {
    c0 = [245, 158, 11];
    c1 = [220, 38, 38];
    t = (u - 0.8) / 0.2;
  } else {
    c0 = [220, 38, 38];
    c1 = [127, 29, 29];
    t = clamp((u - 1.0) / 0.5, 0, 1);
  }
  return [
    Math.round(lerp(c0[0], c1[0], t)),
    Math.round(lerp(c0[1], c1[1], t)),
    Math.round(lerp(c0[2], c1[2], t)),
  ];
}

function stressColor(util, alpha) {
  const rgb = stressRgb(util);
  return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${alpha})`;
}

function fitView() {
  const w = Math.max(1, stage.clientWidth);
  const h = Math.max(1, stage.clientHeight);
  const modelSize = Math.max(sceneWidth(), sceneDepth(), TOTAL_H, 1);
  zoom = Math.max(2.0, Math.min(40.0, Math.min(w, h) * 0.52 / modelSize));
  panX = 0;
  panY = 0;
}

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  cv.width = Math.max(1, Math.floor(w * dpr));
  cv.height = Math.max(1, Math.floor(h * dpr));
  cv.style.width = w + 'px';
  cv.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  fitView();
  draw();
}

function rotatePoint(p) {
  const x0 = p[0] - sceneWidth() / 2;
  const y0 = p[1] - sceneDepth() / 2;
  const z0 = p[2] - TOTAL_H / 2;

  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const x1 = x0 * cy - y0 * sy;
  const y1 = x0 * sy + y0 * cy;
  const z1 = z0;

  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x2 = x1;
  const y2 = y1 * cp - z1 * sp;
  const z2 = y1 * sp + z1 * cp;
  return [x2, y2, z2];
}

function project(p) {
  const [x, y, z] = rotatePoint(p);
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  const cx = w * 0.5 + panX;
  const cy = h * 0.5 + panY;
  return [cx + x * zoom, cy - y * zoom, z];
}

function segmentRods(combo) {
  const rods = { FL: [], FR: [], BL: [], BR: [] };
  for (const c of CORNERS) {
    const segs = [];
    for (let i = 0; i < combo.layers.length; i++) {
      if (combo.layers[i].rods.includes(c)) segs.push([i * H, (i + 1) * H, i + 1]);
    }
    segs.sort((a, b) => a[0] - b[0]);
    rods[c] = segs;
  }
  return rods;
}

function panelQuad(side, z0, z1, ox, oy) {
  const pair = sideCorners[side];
  const p0 = cornerXY[pair[0]];
  const p1 = cornerXY[pair[1]];
  return [
    [ox + p0[0], oy + p0[1], z0],
    [ox + p1[0], oy + p1[1], z0],
    [ox + p1[0], oy + p1[1], z1],
    [ox + p0[0], oy + p0[1], z1],
  ];
}

function cubeQuads(bounds, z0, z1) {
  const x0 = bounds.x0, x1 = bounds.x1, y0 = bounds.y0, y1 = bounds.y1;
  return [
    [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]],
    [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]],
    [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]],
    [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]],
    [[x1, y1, z0], [x0, y1, z0], [x0, y1, z1], [x1, y1, z1]],
    [[x0, y1, z0], [x0, y0, z0], [x0, y0, z1], [x0, y1, z1]],
  ];
}

function drawFace(points3, fill, stroke) {
  const pts = points3.map(project);
  const zAvg = pts.reduce((s, p) => s + p[2], 0) / pts.length;
  return { pts, zAvg, fill, stroke };
}

function layerPanelSidesTouchingCorner(layer, corner) {
  const out = [];
  for (const side of layer.support_panels) {
    const pair = sideCorners[side];
    if (pair[0] === corner || pair[1] === corner) out.push(side);
  }
  return out;
}

function pointCornerWeights(px, py) {
  const u = clamp(px / X, 0, 1);
  const v = clamp(py / Y, 0, 1);
  return {
    FL: (1 - u) * (1 - v),
    FR: u * (1 - v),
    BL: (1 - u) * v,
    BR: u * v,
  };
}

function cubeBounds(state) {
  const sw = sceneWidth();
  const sd = sceneDepth();
  const sx = clamp(state.sizeX, 0.5, Math.max(0.5, Math.min(X, sw)));
  const sy = clamp(state.sizeY, 0.5, Math.max(0.5, Math.min(Y, sd)));
  const cx = clamp(state.posX, sx / 2, sw - sx / 2);
  const cy = clamp(state.posY, sy / 2, sd - sy / 2);
  return {
    x0: cx - sx / 2,
    x1: cx + sx / 2,
    y0: cy - sy / 2,
    y1: cy + sy / 2,
    sx,
    sy,
    cx,
    cy,
  };
}

function evaluateLoad(combo, state) {
  const boardDemand = {};
  const rodDemand = {};
  const panelDemand = {};
  const connectorDemand = {};
  const pathIssues = [];
  const eps = 1e-9;

  function locateCellForBounds(bounds) {
    const nx = Math.max(1, Math.round(state.layout.nx));
    const ny = Math.max(1, Math.round(state.layout.ny));
    const ix = clamp(Math.floor(bounds.cx / X), 0, nx - 1);
    const iy = clamp(Math.floor(bounds.cy / Y), 0, ny - 1);
    const ox = ix * X;
    const oy = iy * Y;
    let x0 = clamp(bounds.x0 - ox, 0, X);
    let x1 = clamp(bounds.x1 - ox, 0, X);
    let y0 = clamp(bounds.y0 - oy, 0, Y);
    let y1 = clamp(bounds.y1 - oy, 0, Y);
    if (x1 - x0 < 1e-3) {
      x0 = clamp(bounds.cx - ox - 0.25, 0, X);
      x1 = clamp(x0 + 0.5, 0, X);
    }
    if (y1 - y0 < 1e-3) {
      y0 = clamp(bounds.cy - oy - 0.25, 0, Y);
      y1 = clamp(y0 + 0.5, 0, Y);
    }
    return { ix, iy, local: { x0, x1, y0, y1 } };
  }

  for (let cubeIdx = 0; cubeIdx < state.cubes.length; cubeIdx++) {
    const cube = state.cubes[cubeIdx];
    const layer = clamp(Math.round(cube.layer), 1, N);
    const weight = Math.max(0, cube.weight);
    const bounds = cubeBounds(cube);
    const located = locateCellForBounds(bounds);
    const ix = located.ix;
    const iy = located.iy;
    const local = located.local;
    const ctag = cellTag(ix, iy);

    const samples = [
      [local.x0, local.y0],
      [local.x1, local.y0],
      [local.x0, local.y1],
      [local.x1, local.y1],
    ];
    let incoming = { FL: 0, FR: 0, BL: 0, BR: 0 };
    for (const p of samples) {
      const w = pointCornerWeights(p[0], p[1]);
      incoming.FL += weight * 0.25 * w.FL;
      incoming.FR += weight * 0.25 * w.FR;
      incoming.BL += weight * 0.25 * w.BL;
      incoming.BR += weight * 0.25 * w.BR;
    }

    add(boardDemand, keyInCell(ix, iy, `L${layer}`), weight);

    for (let lv = layer; lv >= 1; lv--) {
      const lp = combo.layers[lv - 1];
      const nextIncoming = { FL: 0, FR: 0, BL: 0, BR: 0 };
      for (const corner of CORNERS) {
        const load = incoming[corner] || 0;
        if (load <= eps) continue;
        add(connectorDemand, keyInCell(ix, iy, `L${lv}:${corner}`), load);

        const channels = [];
        if (lp.rods.includes(corner)) {
          channels.push({ kind: 'rod', id: corner, cap: state.caps.rod });
        }
        for (const side of layerPanelSidesTouchingCorner(lp, corner)) {
          channels.push({ kind: 'panel', id: side, cap: state.caps.panel / 2 });
        }

        if (!channels.length) {
          pathIssues.push(`[方块${cubeIdx + 1}][${ctag}] L${lv}:${corner} 无支撑，load=${load.toFixed(2)}`);
          continue;
        }

        const capSum = channels.reduce((s, it) => s + Math.max(it.cap, eps), 0);
        for (const ch of channels) {
          const share = load * Math.max(ch.cap, eps) / capSum;
          if (ch.kind === 'rod') {
            add(rodDemand, keyInCell(ix, iy, `L${lv}:${ch.id}`), share);
            if (lv > 1) add(nextIncoming, ch.id, share);
          } else {
            add(panelDemand, keyInCell(ix, iy, `L${lv}:${ch.id}`), share);
            if (lv > 1) {
              const pair = sideCorners[ch.id];
              add(nextIncoming, pair[0], share * 0.5);
              add(nextIncoming, pair[1], share * 0.5);
            }
          }
        }
      }
      incoming = nextIncoming;
    }
  }

  const rodUtil = {};
  const panelUtil = {};
  const connectorUtil = {};
  const boardUtil = {};
  const boardDeflectionUtil = {};
  let maxUtil = 0;
  const critical = [];

  function pushUtil(type, key, util) {
    if (!Number.isFinite(util)) return;
    critical.push({ type, key, util });
    if (util > maxUtil) maxUtil = util;
  }

  for (const key in rodDemand) {
    const util = rodDemand[key] / Math.max(state.caps.rod, eps);
    rodUtil[key] = util;
    pushUtil('rod', key, util);
  }
  for (const key in panelDemand) {
    const util = panelDemand[key] / Math.max(state.caps.panel, eps);
    panelUtil[key] = util;
    pushUtil('panel', key, util);
  }
  for (const key in connectorDemand) {
    const util = connectorDemand[key] / Math.max(state.caps.connector, eps);
    connectorUtil[key] = util;
    pushUtil('connector', key, util);
  }
  for (const key in boardDemand) {
    const util = boardDemand[key] / Math.max(state.caps.board, eps);
    boardUtil[key] = util;
    pushUtil('board', key, util);
    const utilDef = boardDemand[key] / Math.max(state.caps.boardDeflect, eps);
    boardDeflectionUtil[key] = utilDef;
    pushUtil('board_deflect', key, utilDef);
  }

  critical.sort((a, b) => b.util - a.util);
  const pass = pathIssues.length === 0 && maxUtil <= 1.0;

  return {
    boardDemand,
    rodDemand,
    panelDemand,
    connectorDemand,
    rodUtil,
    panelUtil,
    connectorUtil,
    boardUtil,
    boardDeflectionUtil,
    pathIssues,
    maxUtil,
    pass,
    critical: critical.slice(0, 6),
  };
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function splitCellPrefixedKey(key) {
  const m = /^(?:C(\\d+)-(\\d+)\\|)?(.+)$/.exec(String(key));
  if (!m) return null;
  return {
    ix: clamp((Number(m[1] || 1) - 1), 0, Math.max(0, Math.round(loadState.layout.nx) - 1)),
    iy: clamp((Number(m[2] || 1) - 1), 0, Math.max(0, Math.round(loadState.layout.ny) - 1)),
    local: m[3],
  };
}

function parseLayerCornerKey(key) {
  const part = splitCellPrefixedKey(key);
  if (!part) return null;
  const m = /^L(\\d+):([A-Z]{2})$/.exec(part.local);
  if (!m) return null;
  return { ix: part.ix, iy: part.iy, layer: clamp(Number(m[1]), 1, N), corner: m[2] };
}

function parseLayerSideKey(key) {
  const part = splitCellPrefixedKey(key);
  if (!part) return null;
  const m = /^L(\\d+):(front|back|left|right)$/.exec(part.local);
  if (!m) return null;
  return { ix: part.ix, iy: part.iy, layer: clamp(Number(m[1]), 1, N), side: m[2] };
}

function parseLayerOnlyKey(key) {
  const part = splitCellPrefixedKey(key);
  if (!part) return null;
  const m = /^L(\\d+)$/.exec(part.local);
  if (!m) return null;
  return { ix: part.ix, iy: part.iy, layer: clamp(Number(m[1]), 1, N) };
}

function overloadAnchor(type, key) {
  if (type === 'rod') {
    const info = parseLayerCornerKey(key);
    if (!info || !cornerXY[info.corner]) return null;
    return [info.ix * X + cornerXY[info.corner][0], info.iy * Y + cornerXY[info.corner][1], (info.layer - 0.5) * H];
  }
  if (type === 'panel') {
    const info = parseLayerSideKey(key);
    if (!info || !sideCorners[info.side]) return null;
    const pair = sideCorners[info.side];
    const p0 = cornerXY[pair[0]], p1 = cornerXY[pair[1]];
    return [info.ix * X + (p0[0] + p1[0]) * 0.5, info.iy * Y + (p0[1] + p1[1]) * 0.5, (info.layer - 0.5) * H];
  }
  if (type === 'connector') {
    const info = parseLayerCornerKey(key);
    if (!info || !cornerXY[info.corner]) return null;
    return [info.ix * X + cornerXY[info.corner][0], info.iy * Y + cornerXY[info.corner][1], info.layer * H];
  }
  if (type === 'board' || type === 'board_deflect') {
    const info = parseLayerOnlyKey(key);
    if (!info) return null;
    if (type === 'board_deflect') {
      return [info.ix * X + X * 0.62, info.iy * Y + Y * 0.38, info.layer * H];
    }
    return [info.ix * X + X * 0.5, info.iy * Y + Y * 0.5, info.layer * H];
  }
  return null;
}

function collectOverloadedBases(ev, state) {
  const out = [];
  function collect(type, label, demandMap, cap) {
    const safeCap = Math.max(cap, 1e-9);
    for (const key in demandMap) {
      const demand = Number(demandMap[key] || 0);
      const util = demand / safeCap;
      if (util > 1.0 + 1e-9) {
        out.push({ type, label, key, demand, cap: safeCap, util, anchor: overloadAnchor(type, key) });
      }
    }
  }
  collect('rod', '杆', ev.rodDemand, state.caps.rod);
  collect('panel', '支撑板', ev.panelDemand, state.caps.panel);
  collect('connector', '连接件', ev.connectorDemand, state.caps.connector);
  collect('board', '层板', ev.boardDemand, state.caps.board);
  collect('board_deflect', '层板挠度', ev.boardDemand, state.caps.boardDeflect);
  out.sort((a, b) => b.util - a.util);
  return out;
}

function renderFaultBox(ev) {
  if (!faultBox || !faultHint) return;
  const overloads = collectOverloadedBases(ev, loadState);
  const hasFailure = overloads.length > 0 || ev.pathIssues.length > 0;
  faultMarkers = [];
  if (!hasFailure) {
    faultBox.style.display = 'none';
    faultBox.innerHTML = '';
    faultHint.style.display = 'block';
    return;
  }
  faultHint.style.display = 'none';
  faultBox.style.display = 'block';

  const html = [];
  html.push('<h4>故障诊断</h4>');
  html.push('<div><b>状态：</b>不合格</div>');
  html.push(`<div><b>最大利用率：</b>${ev.maxUtil.toFixed(3)}</div>`);
  if (ev.pathIssues.length) {
    html.push('<div style=\"margin-top:6px;\"><b>传力路径问题：</b></div><ul>');
    for (const issue of ev.pathIssues.slice(0, 4)) {
      html.push(`<li>${escapeHtml(issue)}</li>`);
    }
    if (ev.pathIssues.length > 4) {
      html.push(`<li>...其余 ${ev.pathIssues.length - 4} 条</li>`);
    }
    html.push('</ul>');
  }
  if (overloads.length) {
    const shown = overloads.slice(0, 8);
    faultMarkers = shown
      .map((item, idx) => ({ ...item, markerId: idx + 1 }))
      .filter((item) => Array.isArray(item.anchor) && item.anchor.length === 3);
    html.push('<div style=\"margin-top:6px;\"><b>超限基（当前承载 / 限值）：</b></div><ul>');
    for (const item of shown) {
      const marker = faultMarkers.find((m) => m.type === item.type && m.key === item.key);
      const badge = marker
        ? `<span style=\"display:inline-block;min-width:18px;padding:0 5px;height:18px;line-height:18px;border-radius:10px;background:#991b1b;color:#fff;font-size:11px;text-align:center;margin-right:6px;\">#${marker.markerId}</span>`
        : '';
      html.push(
        `<li>${badge}${escapeHtml(item.label)} ${escapeHtml(item.key)}: ${item.demand.toFixed(2)} / ${item.cap.toFixed(2)} (util=${item.util.toFixed(3)})</li>`
      );
    }
    if (overloads.length > 8) {
      html.push(`<li>...其余 ${overloads.length - 8} 项</li>`);
    }
    html.push('</ul>');
    if (faultMarkers.length) {
      html.push('<div style=\"margin-top:6px;color:#7f1d1d;\">3D 视图中的同编号细引线与本列表一一对应。</div>');
    }
  }
  faultBox.innerHTML = html.join('');
}

function drawFaultLeaderLines() {
  if (!faultMarkers.length) return;
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  ctx.save();
  ctx.font = '11px "Segoe UI", "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  for (let i = 0; i < faultMarkers.length; i++) {
    const item = faultMarkers[i];
    if (!Array.isArray(item.anchor) || item.anchor.length !== 3) continue;
    const p = project(item.anchor);
    const edgeY = clamp(28 + i * 24, 14, h - 14);
    const edgeX = w - 2;
    const knotX = w - 30;
    const knotY = edgeY;

    ctx.strokeStyle = 'rgba(153,27,27,0.95)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(p[0], p[1]);
    ctx.lineTo(knotX, knotY);
    ctx.lineTo(edgeX, edgeY);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(p[0], p[1], 4, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.98)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(153,27,27,0.95)';
    ctx.lineWidth = 1;
    ctx.stroke();

    const bx = knotX - 12;
    ctx.beginPath();
    ctx.arc(bx, knotY, 8, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(153,27,27,0.98)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.95)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,1)';
    ctx.fillText(String(item.markerId), bx, knotY + 0.2);
  }
  ctx.restore();
}

function draw() {
  const w = stage.clientWidth;
  const h = stage.clientHeight;
  ctx.clearRect(0, 0, w, h);

  const combo = combos[current];
  if (!combo) return;
  const evaluation = evaluateLoad(combo, loadState);
  lastEval = evaluation;
  renderFaultBox(evaluation);

  const faces = [];
  const nx = Math.max(1, Math.round(loadState.layout.nx));
  const ny = Math.max(1, Math.round(loadState.layout.ny));

  for (let ix = 0; ix < nx; ix++) {
    for (let iy = 0; iy < ny; iy++) {
      const ox = ix * X;
      const oy = iy * Y;
      for (let level = 1; level <= N; level++) {
        const z = level * H;
        const util = Math.max(
          evaluation.boardUtil[keyInCell(ix, iy, `L${level}`)] || 0,
          evaluation.boardDeflectionUtil[keyInCell(ix, iy, `L${level}`)] || 0
        );
        faces.push(drawFace(
          [[ox, oy, z], [ox + X, oy, z], [ox + X, oy + Y, z], [ox, oy + Y, z]],
          stressColor(util, 0.82), 'rgba(75,85,99,0.95)'
        ));
      }

      for (let i = 0; i < combo.layers.length; i++) {
        const layer = combo.layers[i];
        const z0 = i * H;
        const z1 = (i + 1) * H;
        for (const side of layer.support_panels) {
          const util = evaluation.panelUtil[keyInCell(ix, iy, `L${i + 1}:${side}`)] || 0;
          faces.push(drawFace(panelQuad(side, z0, z1, ox, oy), stressColor(util, 0.70), 'rgba(75,85,99,0.95)'));
        }
      }
    }
  }

  for (let i = 0; i < loadState.cubes.length; i++) {
    const cube = loadState.cubes[i];
    const b = cubeBounds(cube);
    const cubeZ0 = clamp(Math.round(cube.layer), 1, N) * H;
    const cubeZ1 = cubeZ0 + clamp(cube.sizeZ, 0.5, H * 2.0);
    const fill = i === loadState.activeCube ? 'rgba(30,64,175,0.24)' : 'rgba(30,64,175,0.14)';
    const stroke = i === loadState.activeCube ? 'rgba(30,64,175,1.0)' : 'rgba(30,64,175,0.70)';
    for (const quad of cubeQuads(b, cubeZ0, cubeZ1)) {
      faces.push(drawFace(quad, fill, stroke));
    }
  }

  faces.sort((a, b) => a.zAvg - b.zAvg);
  for (const f of faces) {
    ctx.beginPath();
    ctx.moveTo(f.pts[0][0], f.pts[0][1]);
    for (let i = 1; i < f.pts.length; i++) ctx.lineTo(f.pts[i][0], f.pts[i][1]);
    ctx.closePath();
    ctx.fillStyle = f.fill;
    ctx.fill();
    ctx.strokeStyle = f.stroke;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  const rods = segmentRods(combo);
  ctx.lineWidth = 4;
  for (let ix = 0; ix < nx; ix++) {
    for (let iy = 0; iy < ny; iy++) {
      const ox = ix * X;
      const oy = iy * Y;
      for (const corner of CORNERS) {
        const xy = cornerXY[corner];
        for (const seg of rods[corner]) {
          const layer = seg[2];
          const util = evaluation.rodUtil[keyInCell(ix, iy, `L${layer}:${corner}`)] || 0;
          ctx.strokeStyle = stressColor(util, 1.0);
          const p0 = project([ox + xy[0], oy + xy[1], seg[0]]);
          const p1 = project([ox + xy[0], oy + xy[1], seg[1]]);
          ctx.beginPath();
          ctx.moveTo(p0[0], p0[1]);
          ctx.lineTo(p1[0], p1[1]);
          ctx.stroke();
        }
      }
    }
  }

  // Connector nodes (all three bases visualized).
  for (let ix = 0; ix < nx; ix++) {
    for (let iy = 0; iy < ny; iy++) {
      const ox = ix * X;
      const oy = iy * Y;
      for (let lv = 1; lv <= N; lv++) {
        const layer = combo.layers[lv - 1];
        for (const corner of CORNERS) {
          const touched = layer.rods.includes(corner) || layer.support_panels.some((side) => {
            const pair = sideCorners[side];
            return pair[0] === corner || pair[1] === corner;
          });
          if (!touched) continue;
          const util = evaluation.connectorUtil[keyInCell(ix, iy, `L${lv}:${corner}`)] || 0;
          const p = project([ox + cornerXY[corner][0], oy + cornerXY[corner][1], lv * H]);
          ctx.beginPath();
          ctx.arc(p[0], p[1], 4, 0, Math.PI * 2);
          ctx.fillStyle = stressColor(util, 1.0);
          ctx.fill();
          ctx.lineWidth = 1;
          ctx.strokeStyle = 'rgba(17,24,39,0.95)';
          ctx.stroke();
        }
      }
    }
  }

  drawFaultLeaderLines();
}

function refreshInfo() {
  const combo = combos[current];
  if (!combo) {
    document.getElementById('info').textContent = '';
    return;
  }
  const ev = lastEval || evaluateLoad(combo, loadState);
  const active = getActiveCube();
  const lines = [
    combo.combo_id + '  ' + combo.label,
    '旋转等价数量=' + combo.equivalent_count,
    `拼接 nx=${Math.round(loadState.layout.nx)}, ny=${Math.round(loadState.layout.ny)}, 总单元=${Math.round(loadState.layout.nx) * Math.round(loadState.layout.ny)}`,
    `方块数量=${loadState.cubes.length}，当前=C${loadState.activeCube + 1}`,
    `当前方块(层=${Math.round(active.layer)}, 尺寸=[${active.sizeX.toFixed(2)},${active.sizeY.toFixed(2)},${active.sizeZ.toFixed(2)}], 中心=[${active.posX.toFixed(2)},${active.posY.toFixed(2)}], 重量=${active.weight.toFixed(2)})`,
    `容量(杆=${loadState.caps.rod.toFixed(2)}, 支撑板=${loadState.caps.panel.toFixed(2)}, 连接件=${loadState.caps.connector.toFixed(2)}, 层板=${loadState.caps.board.toFixed(2)}, 挠度=${loadState.caps.boardDeflect.toFixed(2)})`,
    `承载判定=${ev.pass ? '通过' : '不通过'}，最大利用率=${ev.maxUtil.toFixed(3)}`,
  ];
  if (ev.pathIssues.length) {
    lines.push('传力路径问题=' + ev.pathIssues.join(' | '));
  }
  if (ev.critical.length) {
    const typeName = {
      rod: '杆',
      panel: '支撑板',
      connector: '连接件',
      board: '层板',
      board_deflect: '层板挠度',
    };
    lines.push('关键超限=' + ev.critical.map((it) => `${typeName[it.type] || it.type}:${it.key}:${it.util.toFixed(3)}`).join(' | '));
  }
  document.getElementById('info').textContent = lines.join('\\n');
}

function syncControlsFromState() {
  const active = getActiveCube();
  const nx = Math.max(1, Math.round(loadState.layout.nx));
  const ny = Math.max(1, Math.round(loadState.layout.ny));
  controls.nxCount.value = String(nx);
  controls.nyCount.value = String(ny);
  controls.cubeCount.value = String(loadState.cubes.length);
  controls.cubeLayer.value = String(Math.round(active.layer));
  controls.cubeWeight.value = active.weight.toFixed(2);
  controls.cubeSizeX.value = active.sizeX.toFixed(2);
  controls.cubeSizeY.value = active.sizeY.toFixed(2);
  controls.cubeSizeZ.value = active.sizeZ.toFixed(2);
  controls.cubePosX.value = active.posX.toFixed(2);
  controls.cubePosY.value = active.posY.toFixed(2);
  controls.capRod.value = loadState.caps.rod.toFixed(2);
  controls.capPanel.value = loadState.caps.panel.toFixed(2);
  controls.capConnector.value = loadState.caps.connector.toFixed(2);
  controls.capBoard.value = loadState.caps.board.toFixed(2);
  controls.capBoardDeflect.value = loadState.caps.boardDeflect.toFixed(2);
  controls.cubePosX.max = String(sceneWidth());
  controls.cubePosY.max = String(sceneDepth());
  if (controls.sceneMeta) {
    controls.sceneMeta.textContent = `N=${N}, x=${X}, y=${Y}, h=${H} | nx=${nx}, ny=${ny}`;
  }
  if (controls.tileInfo) {
    controls.tileInfo.textContent = `总单元数：${nx * ny}（X方向 ${nx} × Y方向 ${ny}）`;
  }
  syncCubeIndexOptions();
}

function normalizeCube(cube) {
  const sw = sceneWidth();
  const sd = sceneDepth();
  cube.layer = clamp(Math.round(cube.layer), 1, N);
  cube.weight = Math.max(0, cube.weight);
  cube.sizeX = clamp(cube.sizeX, 0.5, Math.max(0.5, Math.min(X, sw)));
  cube.sizeY = clamp(cube.sizeY, 0.5, Math.max(0.5, Math.min(Y, sd)));
  cube.sizeZ = clamp(cube.sizeZ, 0.5, H * 2.0);
  cube.posX = clamp(cube.posX, cube.sizeX / 2, sw - cube.sizeX / 2);
  cube.posY = clamp(cube.posY, cube.sizeY / 2, sd - cube.sizeY / 2);
}

function normalizeState() {
  loadState.layout.nx = clamp(Math.round(loadState.layout.nx), 1, 6);
  loadState.layout.ny = clamp(Math.round(loadState.layout.ny), 1, 6);
  if (!loadState.cubes.length) loadState.cubes.push(makeDefaultCube());
  loadState.activeCube = clamp(Math.round(loadState.activeCube), 0, loadState.cubes.length - 1);
  for (const cube of loadState.cubes) normalizeCube(cube);
  loadState.caps.rod = Math.max(1e-6, loadState.caps.rod);
  loadState.caps.panel = Math.max(1e-6, loadState.caps.panel);
  loadState.caps.connector = Math.max(1e-6, loadState.caps.connector);
  loadState.caps.board = Math.max(1e-6, loadState.caps.board);
  loadState.caps.boardDeflect = Math.max(1e-6, loadState.caps.boardDeflect);
}

function ensureCubeCount(targetCount) {
  const want = clamp(Math.round(targetCount), 1, 12);
  while (loadState.cubes.length < want) {
    const newCube = makeDefaultCube();
    newCube.layer = clamp(loadState.cubes.length + 1, 1, N);
    newCube.posX = sceneWidth() * 0.5;
    newCube.posY = sceneDepth() * 0.5;
    loadState.cubes.push(newCube);
  }
  while (loadState.cubes.length > want) {
    loadState.cubes.pop();
  }
  loadState.activeCube = clamp(loadState.activeCube, 0, loadState.cubes.length - 1);
}

function syncCubeIndexOptions() {
  const sel = controls.cubeIndex;
  const prev = loadState.activeCube;
  sel.innerHTML = '';
  for (let i = 0; i < loadState.cubes.length; i++) {
    const op = document.createElement('option');
    op.value = String(i);
    op.textContent = `C${i + 1}`;
    sel.appendChild(op);
  }
  loadState.activeCube = clamp(prev, 0, loadState.cubes.length - 1);
  sel.value = String(loadState.activeCube);
}

function onControlInput() {
  const oldNx = Math.round(loadState.layout.nx);
  const oldNy = Math.round(loadState.layout.ny);
  loadState.layout.nx = num(controls.nxCount.value, loadState.layout.nx);
  loadState.layout.ny = num(controls.nyCount.value, loadState.layout.ny);
  ensureCubeCount(num(controls.cubeCount.value, loadState.cubes.length));
  loadState.activeCube = clamp(num(controls.cubeIndex.value, loadState.activeCube), 0, loadState.cubes.length - 1);
  const active = getActiveCube();
  active.layer = num(controls.cubeLayer.value, active.layer);
  active.weight = num(controls.cubeWeight.value, active.weight);
  active.sizeX = num(controls.cubeSizeX.value, active.sizeX);
  active.sizeY = num(controls.cubeSizeY.value, active.sizeY);
  active.sizeZ = num(controls.cubeSizeZ.value, active.sizeZ);
  active.posX = num(controls.cubePosX.value, active.posX);
  active.posY = num(controls.cubePosY.value, active.posY);
  loadState.caps.rod = num(controls.capRod.value, loadState.caps.rod);
  loadState.caps.panel = num(controls.capPanel.value, loadState.caps.panel);
  loadState.caps.connector = num(controls.capConnector.value, loadState.caps.connector);
  loadState.caps.board = num(controls.capBoard.value, loadState.caps.board);
  loadState.caps.boardDeflect = num(controls.capBoardDeflect.value, loadState.caps.boardDeflect);
  normalizeState();
  const layoutChanged = oldNx !== Math.round(loadState.layout.nx) || oldNy !== Math.round(loadState.layout.ny);
  if (layoutChanged) fitView();
  syncControlsFromState();
  draw();
  refreshInfo();
}

function initControls() {
  controls.nxCount.min = '1';
  controls.nxCount.max = '6';
  controls.nxCount.step = '1';
  controls.nyCount.min = '1';
  controls.nyCount.max = '6';
  controls.nyCount.step = '1';
  controls.cubeCount.min = '1';
  controls.cubeCount.max = '12';
  controls.cubeCount.step = '1';
  controls.cubeLayer.min = '1';
  controls.cubeLayer.max = String(N);
  controls.cubeLayer.step = '1';
  controls.cubeWeight.min = '0';
  controls.cubeWeight.step = '1';
  controls.cubeSizeX.min = '0.5';
  controls.cubeSizeX.max = String(X);
  controls.cubeSizeX.step = '0.5';
  controls.cubeSizeY.min = '0.5';
  controls.cubeSizeY.max = String(Y);
  controls.cubeSizeY.step = '0.5';
  controls.cubeSizeZ.min = '0.5';
  controls.cubeSizeZ.max = String(H * 2.0);
  controls.cubeSizeZ.step = '0.5';
  controls.cubePosX.min = '0';
  controls.cubePosX.max = String(sceneWidth());
  controls.cubePosX.step = '0.5';
  controls.cubePosY.min = '0';
  controls.cubePosY.max = String(sceneDepth());
  controls.cubePosY.step = '0.5';

  for (const key of ['capRod', 'capPanel', 'capConnector', 'capBoard', 'capBoardDeflect']) {
    controls[key].min = '0.001';
    controls[key].step = '0.5';
  }

  const inputIds = [
    'nxCount', 'nyCount',
    'cubeCount', 'cubeLayer', 'cubeWeight', 'cubeSizeX', 'cubeSizeY', 'cubeSizeZ', 'cubePosX', 'cubePosY',
    'capRod', 'capPanel', 'capConnector', 'capBoard', 'capBoardDeflect',
  ];
  for (const id of inputIds) {
    controls[id].addEventListener('input', onControlInput);
    controls[id].addEventListener('change', onControlInput);
  }
  controls.cubeIndex.addEventListener('change', onControlInput);
  controls.resetCapsBtn.addEventListener('click', () => {
    loadState.caps = {
      rod: EXTERNAL_DEFAULTS.rod_capacity,
      panel: EXTERNAL_DEFAULTS.support_panel_capacity,
      connector: EXTERNAL_DEFAULTS.connector_capacity,
      board: EXTERNAL_DEFAULTS.board_capacity,
      boardDeflect: EXTERNAL_DEFAULTS.board_deflection_capacity,
    };
    normalizeState();
    syncControlsFromState();
    draw();
    refreshInfo();
  });

  normalizeState();
  syncControlsFromState();
}

function activeCubeCenterProjected() {
  const active = getActiveCube();
  const z0 = clamp(Math.round(active.layer), 1, N) * H;
  const z1 = z0 + clamp(active.sizeZ, 0.5, H * 2.0);
  return project([active.posX, active.posY, (z0 + z1) * 0.5]);
}

function pickCubeAtScreen(clientX, clientY) {
  const rect = cv.getBoundingClientRect();
  const lx = clientX - rect.left;
  const ly = clientY - rect.top;
  let best = -1;
  let bestD2 = 1e18;
  for (let i = 0; i < loadState.cubes.length; i++) {
    const cube = loadState.cubes[i];
    const z0 = clamp(Math.round(cube.layer), 1, N) * H;
    const z1 = z0 + clamp(cube.sizeZ, 0.5, H * 2.0);
    const c = project([cube.posX, cube.posY, (z0 + z1) * 0.5]);
    const dx = lx - c[0];
    const dy = ly - c[1];
    const d2 = dx * dx + dy * dy;
    if (d2 < bestD2) {
      bestD2 = d2;
      best = i;
    }
  }
  return bestD2 <= 20 * 20 ? best : -1;
}

function renderCurrent() {
  if (!combos.length) {
    showStatus('没有可渲染的组合。', true);
    draw();
    return;
  }
  const sel = document.getElementById('comboSelect');
  sel.value = String(current);
  draw();
  refreshInfo();
}

  try {
  const sel = document.getElementById('comboSelect');
  combos.forEach((c, idx) => {
    const op = document.createElement('option');
    op.value = String(idx);
    op.textContent = c.combo_id + '  （等价' + c.equivalent_count + '）  ' + c.label;
    sel.appendChild(op);
  });
  sel.addEventListener('change', () => {
    current = Number(sel.value);
    renderCurrent();
  });

  document.getElementById('prevBtn').addEventListener('click', () => {
    current = (current - 1 + combos.length) % combos.length;
    renderCurrent();
  });
  document.getElementById('nextBtn').addEventListener('click', () => {
    current = (current + 1) % combos.length;
    renderCurrent();
  });
  document.getElementById('fitBtn').addEventListener('click', () => {
    fitView();
    draw();
  });

  let dragging = false;
  let mode = 'rotate';
  let lastX = 0;
  let lastY = 0;
  cv.addEventListener('contextmenu', (e) => e.preventDefault());
  cv.addEventListener('mousedown', (e) => {
    dragging = true;
    if (e.button === 2) {
      mode = 'pan';
    } else {
      const picked = pickCubeAtScreen(e.clientX, e.clientY);
      if (picked >= 0) {
        loadState.activeCube = picked;
        mode = 'cube';
        syncControlsFromState();
        refreshInfo();
      } else {
        mode = 'rotate';
      }
    }
    lastX = e.clientX;
    lastY = e.clientY;
  });
  window.addEventListener('mouseup', () => dragging = false);
  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;
    lastX = e.clientX;
    lastY = e.clientY;
    if (mode === 'rotate') {
      yaw += dx * 0.008;
      pitch += dy * 0.008;
      pitch = Math.max(-1.4, Math.min(1.4, pitch));
    } else if (mode === 'pan') {
      panX += dx;
      panY += dy;
    } else if (mode === 'cube') {
      const active = getActiveCube();
      const rx = dx / Math.max(zoom, 1e-6);
      const ry = -dy / Math.max(zoom, 1e-6);
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const worldDx = rx * cy + ry * sy;
      const worldDy = -rx * sy + ry * cy;
      active.posX += worldDx;
      active.posY += worldDy;
      normalizeCube(active);
      syncControlsFromState();
      refreshInfo();
    }
    draw();
  });
  cv.addEventListener('wheel', (e) => {
    e.preventDefault();
    const k = Math.exp(-e.deltaY * 0.0015);
    zoom = Math.max(2.0, Math.min(40.0, zoom * k));
    draw();
  }, { passive: false });

  initControls();
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  renderCurrent();
  showStatus('可视化已就绪。可拖动方块并调整 nx/ny；组合数=' + combos.length, false);
} catch (err) {
  showStatus('可视化初始化失败：' + String(err), true);
}
</script>
</body>
</html>
""".replace("__COMBOS_JSON__", combos_json).replace("__EXT_PROPS__", ext_props_json).replace("__COUNT__", str(len(items))).replace("__N__", str(n)).replace(
        "__X__", fmt_num(x)
    ).replace("__Y__", fmt_num(y)).replace("__H__", fmt_num(h))


def main() -> None:
    args = parse_args()
    out_dir = resolve_output_dir(args.layers, args.x, args.y, args.h, args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("CASE-*.obj"):
        old.unlink()
    for old in out_dir.glob("CASE-*.png"):
        old.unlink()

    layer_patterns = build_layer_patterns()
    all_combos = [
        Combo(layers=layers)
        for layers in product(layer_patterns, repeat=args.layers)
    ]

    groups: dict[ComboKey, list[Combo]] = {}
    for combo in all_combos:
        key = canonical_key_under_rotation(combo)
        groups.setdefault(key, []).append(combo)

    canonical_keys = sorted(groups.keys())
    unique_items: list[dict] = []

    for idx, key in enumerate(canonical_keys, start=1):
        combo = key_to_combo(key)
        group_members = groups[key]
        combo_id = f"CASE-{idx:02d}"
        obj_name = f"{combo_id}.obj"
        png_name = f"{combo_id}.png"
        write_obj(combo, out_dir / obj_name, args.x, args.y, args.h)
        draw_preview_png(combo, out_dir / png_name, f"{combo_id} {combo_label(combo)}", args.x, args.y, args.h)

        unique_items.append(
            {
                "combo_id": combo_id,
                "label": combo_label(combo),
                "equivalent_count": len(group_members),
                "equivalent_members": [combo_label(item) for item in sorted(group_members, key=combo_key)],
                "layers": [
                    {
                        "rods": list(layer.rods),
                        "support_panels": list(layer.side_panels),
                        "open_sides": open_sides(layer.side_panels),
                    }
                    for layer in combo.layers
                ],
                "obj": obj_name,
                "preview_png": png_name,
            }
        )

    thumb_w, thumb_h = 260, 190
    cols = 5
    rows = max(1, math.ceil(len(unique_items) / cols))
    sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, item in enumerate(unique_items):
        r, c = divmod(idx, cols)
        x0, y0 = c * thumb_w, r * thumb_h
        img = Image.open(out_dir / item["preview_png"]).convert("RGB").resize((thumb_w, thumb_h - 20))
        sheet.paste(img, (x0, y0 + 20))
        draw.text((x0 + 8, y0 + 3), f"{item['combo_id']} ({item['equivalent_count']})", fill=(0, 0, 0))
    sheet.save(out_dir / "ALL_COMBOS_3D.png")

    summary = {
        "assumptions": {
            "N": args.layers,
            "x": args.x,
            "y": args.y,
            "h": args.h,
            "side_panel_height_max": args.h,
            "rod_length_unlimited": True,
            "payload_is_qualification_only": True,
            "opening_ignored": True,
            "external_property_defaults": DEFAULT_EXTERNAL_PROPERTIES,
            "load_model": "engineering_approximation",
            "interactive_cube_enabled": True,
        },
        "rule_interpretation": {
            "single_layer_patterns": len(layer_patterns),
            "raw_total_for_N": f"{len(layer_patterns)}^{args.layers} = {len(all_combos)}",
            "dedup": "rotation equivalence around vertical axis (0/90/180/270 deg)",
            "R2": "per layer E_total=4 with E(rod)=1 and E(panel)=2, shared panel corner counted once; full-corner coverage",
            "R4_note": "90-degree panel-panel connection is allowed but does not relax corner support completeness",
            "R7": "per layer at least one side open",
            "load_qualification": "load pass/fail and utilization are evaluated from external base capacities; not used to filter combo legality",
        },
        "raw_combo_count": len(all_combos),
        "unique_combo_count_after_rotation_dedup": len(unique_items),
        "valid_combos": unique_items,
        "overview_png": "ALL_COMBOS_3D.png",
        "interactive_html": "interactive_3d.html",
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "interactive_3d.html").write_text(
        build_interactive_html(unique_items, args.layers, args.x, args.y, args.h),
        encoding="utf-8",
    )

    try:
        out_dir_display = str(out_dir.relative_to(ROOT))
    except ValueError:
        out_dir_display = str(out_dir)

    print(
        json.dumps(
            {
                "single_layer_patterns": len(layer_patterns),
                "raw_combo_count": len(all_combos),
                "unique_combo_count": len(unique_items),
                "output_dir": out_dir_display,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

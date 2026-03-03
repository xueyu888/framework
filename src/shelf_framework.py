from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from itertools import combinations
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable

STRICT_MAPPING_LEVEL = "L3"
STRICT_MAPPING_REGISTRY = "standards/L3/mapping_registry.json"
STRICT_MAPPING_VALIDATION_COMMAND = (
    "uv run python scripts/validate_strict_mapping.py --check-changes"
)

EPSILON = 1e-6


@dataclass(frozen=True)
class Goal:
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Space3D:
    width: float
    depth: float
    height: float

    def is_valid(self) -> bool:
        return self.width > 0 and self.depth > 0 and self.height > 0


@dataclass(frozen=True)
class Opening2D:
    width: float
    height: float

    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0


@dataclass(frozen=True)
class Footprint2D:
    width: float
    depth: float

    def is_valid(self) -> bool:
        return self.width > 0 and self.depth > 0


@dataclass(frozen=True)
class BoundaryDefinition:
    layers_n: int
    payload_p_per_layer: float
    space_s_per_layer: Space3D
    opening_o: Opening2D
    footprint_a: Footprint2D

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if self.layers_n <= 0:
            errors.append("layers_n must be > 0")
        if self.payload_p_per_layer <= 0:
            errors.append("payload_p_per_layer must be > 0")
        if not self.space_s_per_layer.is_valid():
            errors.append("space_s_per_layer must be positive on all dimensions")
        if not self.opening_o.is_valid():
            errors.append("opening_o must be positive on all dimensions")
        if not self.footprint_a.is_valid():
            errors.append("footprint_a must be positive on all dimensions")

        return (len(errors) == 0, errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layers_n": self.layers_n,
            "payload_p_per_layer": self.payload_p_per_layer,
            "space_s_per_layer": asdict(self.space_s_per_layer),
            "opening_o": asdict(self.opening_o),
            "footprint_a": asdict(self.footprint_a),
        }


class Module(str, Enum):
    ROD = "rod"
    CONNECTOR = "connector"
    PANEL = "panel"


MODULE_ROLE: dict[Module, str] = {
    Module.ROD: "load-bearing support",
    Module.CONNECTOR: "joint between structural members",
    Module.PANEL: "placement surface",
}


ComboValidator = Callable[[set[Module]], bool]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    validator: ComboValidator

    def check(self, combo: set[Module]) -> bool:
        return self.validator(combo)


class CombinationRules:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    @staticmethod
    def all_subsets(modules: Iterable[Module] | None = None) -> list[set[Module]]:
        universe = list(modules or list(Module))
        all_sets: list[set[Module]] = [set()]
        for size in range(1, len(universe) + 1):
            for subset in combinations(universe, size):
                all_sets.append(set(subset))
        return all_sets

    def valid_subsets(self, modules: Iterable[Module] | None = None) -> list[set[Module]]:
        candidates = self.all_subsets(modules)
        valid: list[set[Module]] = []

        for combo in candidates:
            if all(rule.check(combo) for rule in self.rules):
                valid.append(combo)

        return valid

    @staticmethod
    def default() -> "CombinationRules":
        # R3-R5 are geometry constraints and are checked by shelf model geometry validation.
        return CombinationRules(
            rules=[
                Rule(
                    rule_id="R1",
                    description="module set must not be isolated",
                    validator=lambda combo: len(combo) >= 2,
                ),
                Rule(
                    rule_id="R2",
                    description="connector must exist in every usable combination",
                    validator=lambda combo: Module.CONNECTOR in combo,
                ),
                Rule(
                    rule_id="R7",
                    description="rod and panel must both exist in every usable combination",
                    validator=lambda combo: Module.ROD in combo and Module.PANEL in combo,
                ),
            ]
        )


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def key(self, ndigits: int = 6) -> tuple[float, float, float]:
        return (
            round(self.x, ndigits),
            round(self.y, ndigits),
            round(self.z, ndigits),
        )


def _vector(a: Point3D, b: Point3D) -> tuple[float, float, float]:
    return (b.x - a.x, b.y - a.y, b.z - a.z)


def _dot(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


def _cross(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


def _norm(v: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(v, v))


def _unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = _norm(v)
    if n <= EPSILON:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


@dataclass(frozen=True)
class Rod3D:
    rod_id: str
    start: Point3D
    end: Point3D

    def direction(self) -> tuple[float, float, float]:
        return _vector(self.start, self.end)

    def direction_unit(self) -> tuple[float, float, float]:
        return _unit(self.direction())

    def is_horizontal(self, tol: float = EPSILON) -> bool:
        _, _, dz = self.direction()
        return abs(dz) <= tol and _norm(self.direction()) > tol

    def to_dict(self) -> dict[str, Any]:
        return {
            "rod_id": self.rod_id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
        }


@dataclass(frozen=True)
class Panel3D:
    panel_id: str
    corners: tuple[Point3D, Point3D, Point3D, Point3D]

    def normal_unit(self) -> tuple[float, float, float]:
        a, b, c, _ = self.corners
        ab = _vector(a, b)
        ac = _vector(a, c)
        return _unit(_cross(ab, ac))

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "corners": [item.to_dict() for item in self.corners],
        }


@dataclass(frozen=True)
class Face3D:
    face_id: str
    corners: tuple[Point3D, Point3D, Point3D, Point3D]

    def to_dict(self) -> dict[str, Any]:
        return {
            "face_id": self.face_id,
            "corners": [item.to_dict() for item in self.corners],
        }


@dataclass(frozen=True)
class ModuleCell:
    cell_id: str
    row: int
    col: int
    level: int
    combo: set[Module]

    def combo_key(self) -> str:
        return ",".join(sorted(item.value for item in self.combo))

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "row": self.row,
            "col": self.col,
            "level": self.level,
            "combo": modules_to_list(self.combo),
        }


@dataclass(frozen=True)
class GeometryValidationResult:
    r3_rod_vertical: bool
    r4_rods_horizontal_relation: bool
    r5_rod_panel_perpendicular: bool
    r6_rod_link_face_corners: bool
    r8_panel_corners_have_connectors: bool
    r9_top_panel_on_column_top: bool
    r10_no_floating_cells: bool
    r11_connector_required_only_on_connected_rod_end: bool
    errors: list[str] = field(default_factory=list)

    def passed(self) -> bool:
        return (
            self.r3_rod_vertical
            and self.r4_rods_horizontal_relation
            and self.r5_rod_panel_perpendicular
            and self.r6_rod_link_face_corners
            and self.r8_panel_corners_have_connectors
            and self.r9_top_panel_on_column_top
            and self.r10_no_floating_cells
            and self.r11_connector_required_only_on_connected_rod_end
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_structure_from_occupied_cells(
    occupied_cells: Iterable[tuple[int, int, int]],
) -> dict[str, Any]:
    rod_segments: set[tuple[int, int, int]] = set()
    panel_top_corners: set[tuple[int, int, int]] = set()

    for row, col, level in occupied_cells:
        z1 = level + 1
        for row_edge in (row, row + 1):
            for col_edge in (col, col + 1):
                rod_segments.add((row_edge, col_edge, level))
                panel_top_corners.add((row_edge, col_edge, z1))

    # Count endpoint connectivity by unique rod segments, not per-cell contributions.
    endpoint_usage: dict[tuple[int, int, int], int] = {}
    for row_edge, col_edge, level in rod_segments:
        z0 = level
        z1 = level + 1
        for point in ((row_edge, col_edge, z0), (row_edge, col_edge, z1)):
            endpoint_usage[point] = endpoint_usage.get(point, 0) + 1

    rod_endpoints = set(endpoint_usage.keys())
    shared_rod_endpoints = {point for point, count in endpoint_usage.items() if count >= 2}
    required_connectors = shared_rod_endpoints | panel_top_corners
    free_rod_endpoints = rod_endpoints - required_connectors
    return {
        "rod_segments": rod_segments,
        "rod_endpoints": rod_endpoints,
        "panel_top_corners": panel_top_corners,
        "shared_rod_endpoints": shared_rod_endpoints,
        "required_connectors": required_connectors,
        "free_rod_endpoints": free_rod_endpoints,
    }


@dataclass(frozen=True)
class Shelf2x2x2Model:
    rows: int
    cols: int
    levels: int
    rods: list[Rod3D]
    panels: list[Panel3D]
    faces: list[Face3D]
    connectors: list[Point3D]
    cells: list[ModuleCell]
    rod_panel_links: list[tuple[str, str]]

    def group_by_module_combo(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for cell in self.cells:
            groups.setdefault(cell.combo_key(), []).append(cell.cell_id)
        return groups

    def derive_occupied_structure(self) -> dict[str, Any]:
        occupied_cells = [(cell.row, cell.col, cell.level) for cell in self.cells]
        return derive_structure_from_occupied_cells(occupied_cells)

    def _derive_axis_values(self) -> tuple[list[float], list[float], list[float]] | None:
        x_coords = sorted({round(v, 6) for rod in self.rods for v in (rod.start.x, rod.end.x)})
        y_coords = sorted({round(v, 6) for rod in self.rods for v in (rod.start.y, rod.end.y)})
        z_coords = sorted(
            {
                round(v, 6)
                for panel in self.panels
                for corner in panel.corners
                for v in (corner.z,)
            }
            | {round(v, 6) for rod in self.rods for v in (rod.start.z, rod.end.z)}
        )
        if len(x_coords) < self.cols + 1 or len(y_coords) < self.rows + 1 or len(z_coords) < self.levels + 1:
            return None
        return (x_coords, y_coords, z_coords)

    def _index_point_to_world(
        self,
        index_point: tuple[int, int, int],
        axes: tuple[list[float], list[float], list[float]],
    ) -> tuple[float, float, float]:
        row_edge, col_edge, z_idx = index_point
        x_coords, y_coords, z_coords = axes
        return (
            x_coords[col_edge],
            y_coords[row_edge],
            z_coords[z_idx],
        )

    def validate_subset_compliance(self, rules: CombinationRules) -> dict[str, Any]:
        max_combo = {Module.ROD, Module.CONNECTOR, Module.PANEL}
        valid_set = {frozenset(item) for item in rules.valid_subsets()}

        not_subset_cells: list[str] = []
        invalid_cells: list[str] = []
        for cell in self.cells:
            if not cell.combo.issubset(max_combo):
                not_subset_cells.append(cell.cell_id)
            if frozenset(cell.combo) not in valid_set:
                invalid_cells.append(cell.cell_id)

        return {
            "max_boundary": {"rows": self.rows, "cols": self.cols, "levels": self.levels},
            "max_combo": modules_to_list(max_combo),
            "all_cells_subset_of_max_combo": len(not_subset_cells) == 0,
            "all_cells_valid_combo": len(invalid_cells) == 0,
            "invalid_subset_cells": not_subset_cells,
            "invalid_rule_cells": invalid_cells,
        }

    def validate_geometry_rules(self, tol: float = EPSILON) -> GeometryValidationResult:
        errors: list[str] = []

        r3_ok = all(
            abs(rod.start.x - rod.end.x) <= tol
            and abs(rod.start.y - rod.end.y) <= tol
            and abs(rod.start.z - rod.end.z) > tol
            for rod in self.rods
        )
        if not r3_ok:
            errors.append("R3 failed: all rods must be vertical")

        # R4: rods must keep horizontal relation with each other (same bottom and top Z).
        z_start_set = {round(rod.start.z, 6) for rod in self.rods}
        z_end_set = {round(rod.end.z, 6) for rod in self.rods}
        r4_ok = len(z_start_set) == 1 and len(z_end_set) == 1
        if not r4_ok:
            errors.append("R4 failed: rods do not keep a consistent horizontal relation")

        # R5: rod and panel must be vertical (perpendicular) to each other.
        panel_map = {panel.panel_id: panel for panel in self.panels}
        rod_map = {rod.rod_id: rod for rod in self.rods}
        if not self.rod_panel_links:
            r5_ok = False
            errors.append("R5 failed: rod-panel links are missing")
        else:
            r5_ok = True
            for rod_id, panel_id in self.rod_panel_links:
                rod = rod_map.get(rod_id)
                panel = panel_map.get(panel_id)
                if rod is None or panel is None:
                    r5_ok = False
                    errors.append(f"R5 failed: invalid link ({rod_id}, {panel_id})")
                    continue
                rod_u = rod.direction_unit()
                panel_n = panel.normal_unit()
                # Line-plane perpendicular: line direction is parallel to panel normal.
                if abs(abs(_dot(rod_u, panel_n)) - 1.0) > tol:
                    r5_ok = False
                    errors.append(
                        f"R5 failed: rod {rod_id} is not perpendicular to panel {panel_id}"
                    )

        # R6: rods must connect to the 4 corners of every face.
        face_corners: dict[str, set[tuple[float, float, float]]] = {
            face.face_id: {corner.key() for corner in face.corners} for face in self.faces
        }
        rod_endpoints = [rod.start.key() for rod in self.rods] + [rod.end.key() for rod in self.rods]
        every_face_has_four_corners_linked = True
        rod_endpoint_set = set(rod_endpoints)
        for face_id, corners in face_corners.items():
            if not corners.issubset(rod_endpoint_set):
                every_face_has_four_corners_linked = False
                errors.append(f"R6 failed: rods do not cover all 4 corners of face {face_id}")

        r6_ok = every_face_has_four_corners_linked

        connector_points = {item.key() for item in self.connectors}
        r8_ok = True
        for panel in self.panels:
            panel_corner_keys = {corner.key() for corner in panel.corners}
            if not panel_corner_keys.issubset(connector_points):
                r8_ok = False
                errors.append(
                    f"R8 failed: panel {panel.panel_id} does not have connectors on all 4 corners"
                )

        # R9: for each occupied (row,col) column, the topmost occupied level must contain panel.
        top_level_by_column: dict[tuple[int, int], int] = {}
        for cell in self.cells:
            key = (cell.row, cell.col)
            top_level_by_column[key] = max(top_level_by_column.get(key, cell.level), cell.level)

        missing_top_panel_columns: list[str] = []
        for cell in self.cells:
            key = (cell.row, cell.col)
            if cell.level == top_level_by_column[key] and Module.PANEL not in cell.combo:
                missing_top_panel_columns.append(f"({cell.row},{cell.col})@L{cell.level}")

        r9_ok = len(missing_top_panel_columns) == 0
        if not r9_ok:
            missing_text = ", ".join(sorted(set(missing_top_panel_columns)))
            errors.append(f"R9 failed: top occupied level in columns missing panel: {missing_text}")

        # R10: every occupied cell above ground must have occupied support directly below.
        occupied = {(cell.row, cell.col, cell.level) for cell in self.cells}
        floating_cells = [
            (row, col, level)
            for row, col, level in sorted(occupied)
            if level > 0 and (row, col, level - 1) not in occupied
        ]
        r10_ok = len(floating_cells) == 0
        if not r10_ok:
            floating_text = ", ".join(f"({r},{c})@L{l}" for r, c, l in floating_cells)
            errors.append(f"R10 failed: floating occupied cells without support below: {floating_text}")

        # R11 strict: use the same occupied-cell-derived structure data as rendering/statistics.
        axes = self._derive_axis_values()
        if axes is None:
            r11_ok = False
            errors.append("R11 failed: cannot derive occupied-cell geometry axes for connector validation")
        else:
            derived = self.derive_occupied_structure()
            required_connector_points = {
                self._index_point_to_world(point, axes) for point in derived["required_connectors"]
            }
            free_rod_endpoints = {
                self._index_point_to_world(point, axes) for point in derived["free_rod_endpoints"]
            }
            missing_required_points = sorted(required_connector_points - connector_points)
            redundant_connectors_on_free_rod_end = sorted(free_rod_endpoints & connector_points)
            r11_ok = len(missing_required_points) == 0 and len(redundant_connectors_on_free_rod_end) == 0
            if not r11_ok:
                if missing_required_points:
                    missing_text = ", ".join(f"({x},{y},{z})" for x, y, z in missing_required_points)
                    errors.append(
                        "R11 failed: connector missing on required connection points: "
                        f"{missing_text}"
                    )
                if redundant_connectors_on_free_rod_end:
                    redundant_text = ", ".join(
                        f"({x},{y},{z})" for x, y, z in redundant_connectors_on_free_rod_end
                    )
                    errors.append(
                        "R11 failed: redundant connector on free rod endpoints: "
                        f"{redundant_text}"
                    )

        return GeometryValidationResult(
            r3_rod_vertical=r3_ok,
            r4_rods_horizontal_relation=r4_ok,
            r5_rod_panel_perpendicular=r5_ok,
            r6_rod_link_face_corners=r6_ok,
            r8_panel_corners_have_connectors=r8_ok,
            r9_top_panel_on_column_top=r9_ok,
            r10_no_floating_cells=r10_ok,
            r11_connector_required_only_on_connected_rod_end=r11_ok,
            errors=errors,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "levels": self.levels,
            "rods": [rod.to_dict() for rod in self.rods],
            "panels": [panel.to_dict() for panel in self.panels],
            "faces": [face.to_dict() for face in self.faces],
            "connectors": [connector.to_dict() for connector in self.connectors],
            "cells": [cell.to_dict() for cell in self.cells],
            "combo_groups": self.group_by_module_combo(),
        }


def build_shelf_2x2x2(
    width: float = 120.0,
    depth: float = 80.0,
    height: float = 140.0,
) -> Shelf2x2x2Model:
    x_values = [0.0, depth / 2.0, depth]
    y_values = [0.0, width / 2.0, width]
    z_values = [0.0, height / 2.0, height]
    x_min, x_max = x_values[0], x_values[-1]
    y_min, y_max = y_values[0], y_values[-1]
    z_min, z_max = z_values[0], z_values[-1]

    faces = [
        Face3D(
            face_id="x_min",
            corners=(
                Point3D(x_min, y_min, z_min),
                Point3D(x_min, y_max, z_min),
                Point3D(x_min, y_min, z_max),
                Point3D(x_min, y_max, z_max),
            ),
        ),
        Face3D(
            face_id="x_max",
            corners=(
                Point3D(x_max, y_min, z_min),
                Point3D(x_max, y_max, z_min),
                Point3D(x_max, y_min, z_max),
                Point3D(x_max, y_max, z_max),
            ),
        ),
        Face3D(
            face_id="y_min",
            corners=(
                Point3D(x_min, y_min, z_min),
                Point3D(x_max, y_min, z_min),
                Point3D(x_min, y_min, z_max),
                Point3D(x_max, y_min, z_max),
            ),
        ),
        Face3D(
            face_id="y_max",
            corners=(
                Point3D(x_min, y_max, z_min),
                Point3D(x_max, y_max, z_min),
                Point3D(x_min, y_max, z_max),
                Point3D(x_max, y_max, z_max),
            ),
        ),
        Face3D(
            face_id="z_min",
            corners=(
                Point3D(x_min, y_min, z_min),
                Point3D(x_max, y_min, z_min),
                Point3D(x_min, y_max, z_min),
                Point3D(x_max, y_max, z_min),
            ),
        ),
        Face3D(
            face_id="z_max",
            corners=(
                Point3D(x_min, y_min, z_max),
                Point3D(x_max, y_min, z_max),
                Point3D(x_min, y_max, z_max),
                Point3D(x_max, y_max, z_max),
            ),
        ),
    ]

    rods: list[Rod3D] = []

    for xi, x in enumerate(x_values):
        for yi, y in enumerate(y_values):
            rod_id = f"rod_{xi}_{yi}"
            start = Point3D(x, y, z_min)
            end = Point3D(x, y, z_max)
            rods.append(Rod3D(rod_id=rod_id, start=start, end=end))

    combo_pattern = [
        {Module.ROD, Module.CONNECTOR},
        {Module.PANEL, Module.CONNECTOR},
        {Module.ROD, Module.PANEL, Module.CONNECTOR},
    ]
    cells = [
        ModuleCell(
            cell_id=f"cell_{row}_{col}_{level}",
            row=row,
            col=col,
            level=level,
            combo=set(combo_pattern[(row + col + level) % len(combo_pattern)]),
        )
        for row in range(2)
        for col in range(2)
        for level in range(2)
    ]
    panels = [
        Panel3D(
            panel_id=f"panel_{cell.row}_{cell.col}_{cell.level}",
            corners=(
                Point3D(x_values[cell.col], y_values[cell.row], z_values[cell.level + 1]),
                Point3D(x_values[cell.col + 1], y_values[cell.row], z_values[cell.level + 1]),
                Point3D(x_values[cell.col], y_values[cell.row + 1], z_values[cell.level + 1]),
                Point3D(x_values[cell.col + 1], y_values[cell.row + 1], z_values[cell.level + 1]),
            ),
        )
        for cell in cells
    ]
    rod_panel_links = (
        [(rod.rod_id, panels[0].panel_id) for rod in rods]
        if panels
        else []
    )
    derived = derive_structure_from_occupied_cells(
        {(cell.row, cell.col, cell.level) for cell in cells}
    )
    connectors = [
        Point3D(x_values[col_edge], y_values[row_edge], z_values[z_idx])
        for row_edge, col_edge, z_idx in sorted(derived["required_connectors"])
    ]

    return Shelf2x2x2Model(
        rows=2,
        cols=2,
        levels=2,
        rods=rods,
        panels=panels,
        faces=faces,
        connectors=connectors,
        cells=cells,
        rod_panel_links=rod_panel_links,
    )


@dataclass(frozen=True)
class GridShelfVariant:
    variant_id: str
    rows: int
    cols: int
    levels: int
    combo: set[Module]
    model: Shelf2x2x2Model

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "rows": self.rows,
            "cols": self.cols,
            "levels": self.levels,
            "combo": modules_to_list(self.combo),
            "top_view": [[1 for _ in range(self.cols)] for _ in range(self.rows)],
            "model": self.model.to_dict(),
        }


def build_grid_shelf(
    rows: int,
    cols: int,
    levels: int,
    combo: set[Module],
    occupied_cells: set[tuple[int, int, int]] | None = None,
    cell_width: float = 60.0,
    cell_depth: float = 40.0,
    cell_height: float = 70.0,
) -> Shelf2x2x2Model:
    if rows <= 0 or cols <= 0 or levels <= 0:
        raise ValueError("rows/cols/levels must be > 0")

    x_values = [idx * cell_depth for idx in range(cols + 1)]
    y_values = [idx * cell_width for idx in range(rows + 1)]
    z_values = [idx * cell_height for idx in range(levels + 1)]
    x_min, x_max = x_values[0], x_values[-1]
    y_min, y_max = y_values[0], y_values[-1]
    z_min, z_max = z_values[0], z_values[-1]

    faces = [
        Face3D(
            face_id="x_min",
            corners=(
                Point3D(x_min, y_min, z_min),
                Point3D(x_min, y_max, z_min),
                Point3D(x_min, y_min, z_max),
                Point3D(x_min, y_max, z_max),
            ),
        ),
        Face3D(
            face_id="x_max",
            corners=(
                Point3D(x_max, y_min, z_min),
                Point3D(x_max, y_max, z_min),
                Point3D(x_max, y_min, z_max),
                Point3D(x_max, y_max, z_max),
            ),
        ),
        Face3D(
            face_id="y_min",
            corners=(
                Point3D(x_min, y_min, z_min),
                Point3D(x_max, y_min, z_min),
                Point3D(x_min, y_min, z_max),
                Point3D(x_max, y_min, z_max),
            ),
        ),
        Face3D(
            face_id="y_max",
            corners=(
                Point3D(x_min, y_max, z_min),
                Point3D(x_max, y_max, z_min),
                Point3D(x_min, y_max, z_max),
                Point3D(x_max, y_max, z_max),
            ),
        ),
        Face3D(
            face_id="z_min",
            corners=(
                Point3D(x_min, y_min, z_min),
                Point3D(x_max, y_min, z_min),
                Point3D(x_min, y_max, z_min),
                Point3D(x_max, y_max, z_min),
            ),
        ),
        Face3D(
            face_id="z_max",
            corners=(
                Point3D(x_min, y_min, z_max),
                Point3D(x_max, y_min, z_max),
                Point3D(x_min, y_max, z_max),
                Point3D(x_max, y_max, z_max),
            ),
        ),
    ]

    rods: list[Rod3D] = []

    for xi, x in enumerate(x_values):
        for yi, y in enumerate(y_values):
            rod_id = f"rod_{xi}_{yi}"
            start = Point3D(x, y, z_min)
            end = Point3D(x, y, z_max)
            rods.append(Rod3D(rod_id=rod_id, start=start, end=end))

    if occupied_cells is None:
        occupied_cells = {
            (row, col, level)
            for row in range(rows)
            for col in range(cols)
            for level in range(levels)
        }
    cells = [
        ModuleCell(
            cell_id=f"cell_{row}_{col}_{level}",
            row=row,
            col=col,
            level=level,
            combo=set(combo),
        )
        for row, col, level in sorted(occupied_cells)
    ]
    panels = [
        Panel3D(
            panel_id=f"panel_{cell.row}_{cell.col}_{cell.level}",
            corners=(
                Point3D(x_values[cell.col], y_values[cell.row], z_values[cell.level + 1]),
                Point3D(x_values[cell.col + 1], y_values[cell.row], z_values[cell.level + 1]),
                Point3D(x_values[cell.col], y_values[cell.row + 1], z_values[cell.level + 1]),
                Point3D(x_values[cell.col + 1], y_values[cell.row + 1], z_values[cell.level + 1]),
            ),
        )
        for cell in cells
    ]
    rod_panel_links = (
        [(rod.rod_id, panels[0].panel_id) for rod in rods]
        if panels
        else []
    )
    derived = derive_structure_from_occupied_cells(occupied_cells)
    connectors = [
        Point3D(x_values[col_edge], y_values[row_edge], z_values[z_idx])
        for row_edge, col_edge, z_idx in sorted(derived["required_connectors"])
    ]

    return Shelf2x2x2Model(
        rows=rows,
        cols=cols,
        levels=levels,
        rods=rods,
        panels=panels,
        faces=faces,
        connectors=connectors,
        cells=cells,
        rod_panel_links=rod_panel_links,
    )


def enumerate_grid_shelf_variants(
    max_rows: int,
    max_cols: int,
    max_levels: int,
    rules: CombinationRules,
) -> list[GridShelfVariant]:
    valid_combos = rules.valid_subsets()
    variants: list[GridShelfVariant] = []
    all_cells = [
        (row, col, level)
        for row in range(max_rows)
        for col in range(max_cols)
        for level in range(max_levels)
    ]
    seen_shape_keys: set[tuple[tuple[int, int, int], ...]] = set()

    # Shape deduplication uses row/col planar rotations only.
    # level axis is fixed and must not be swapped with row/col.
    planar_rotations = (0, 1, 2, 3) if max_rows == max_cols else (0, 2)

    def canonical_shape_key(cells: set[tuple[int, int, int]]) -> tuple[tuple[int, int, int], ...]:
        keys: list[tuple[tuple[int, int, int], ...]] = []
        for rot in planar_rotations:
            rotated: list[tuple[int, int, int]] = []
            for row, col, level in cells:
                if rot == 0:
                    nr, nc = row, col
                elif rot == 1:
                    nr, nc = col, max_rows - 1 - row
                elif rot == 2:
                    nr, nc = max_rows - 1 - row, max_cols - 1 - col
                else:
                    nr, nc = max_cols - 1 - col, row
                rotated.append((nr, nc, level))
            keys.append(tuple(sorted(rotated)))
        return min(keys)

    def is_connected(cells: set[tuple[int, int, int]]) -> bool:
        if not cells:
            return False
        visited: set[tuple[int, int, int]] = set()
        stack = [next(iter(cells))]
        while stack:
            row, col, level = stack.pop()
            if (row, col, level) in visited:
                continue
            visited.add((row, col, level))
            neighbors = [
                (row + 1, col, level),
                (row - 1, col, level),
                (row, col + 1, level),
                (row, col - 1, level),
                (row, col, level + 1),
                (row, col, level - 1),
            ]
            for item in neighbors:
                if item in cells and item not in visited:
                    stack.append(item)
        return len(visited) == len(cells)

    def bbox_dims(cells: set[tuple[int, int, int]]) -> tuple[int, int, int]:
        rows = [item[0] for item in cells]
        cols = [item[1] for item in cells]
        levels = [item[2] for item in cells]
        return (max(rows) - min(rows) + 1, max(cols) - min(cols) + 1, max(levels) - min(levels) + 1)

    n = len(all_cells)
    for mask in range(1, 1 << n):
        occupied: set[tuple[int, int, int]] = set()
        for idx, cell in enumerate(all_cells):
            if (mask >> idx) & 1:
                occupied.add(cell)
        if not is_connected(occupied):
            continue
        shape_key = canonical_shape_key(occupied)
        if shape_key in seen_shape_keys:
            continue
        seen_shape_keys.add(shape_key)

        rows, cols, levels = bbox_dims(occupied)
        for combo in valid_combos:
            combo_key = "-".join(modules_to_list(combo))
            variant_id = f"grid_{rows}x{cols}x{levels}__{combo_key}__m{mask}"
            model = build_grid_shelf(max_rows, max_cols, max_levels, combo, occupied_cells=occupied)
            variants.append(
                GridShelfVariant(
                    variant_id=variant_id,
                    rows=rows,
                    cols=cols,
                    levels=levels,
                    combo=set(combo),
                    model=model,
                )
            )

    return variants


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationInput:
    boundary: BoundaryDefinition
    combo: set[Module]
    valid_combinations: list[set[Module]]
    baseline_efficiency: float
    target_efficiency: float
    geometry: GeometryValidationResult | None = None


@dataclass(frozen=True)
class VerificationResult:
    boundary_valid: bool
    combination_valid: bool
    geometry_valid: bool
    efficiency_improved: bool
    passed: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify(payload: VerificationInput) -> VerificationResult:
    boundary_valid, boundary_errors = payload.boundary.validate()
    combo_key = frozenset(payload.combo)
    valid_set = {frozenset(item) for item in payload.valid_combinations}
    combination_valid = combo_key in valid_set
    geometry_valid = payload.geometry.passed() if payload.geometry is not None else True
    efficiency_improved = payload.target_efficiency > payload.baseline_efficiency

    reasons: list[str] = []
    reasons.extend(boundary_errors)
    if not combination_valid:
        reasons.append("combo is not in valid combinations")
    if payload.geometry is not None and not geometry_valid:
        reasons.extend(payload.geometry.errors)
    if not efficiency_improved:
        reasons.append("target_efficiency must be > baseline_efficiency")

    return VerificationResult(
        boundary_valid=boundary_valid,
        combination_valid=combination_valid,
        geometry_valid=geometry_valid,
        efficiency_improved=efficiency_improved,
        passed=boundary_valid and combination_valid and geometry_valid and efficiency_improved,
        reasons=reasons,
    )


@dataclass(frozen=True)
class LogicStep:
    step_id: str
    label: str
    depends_on: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LogicRecord:
    steps: list[LogicStep]

    @classmethod
    def build(cls, steps: list[LogicStep]) -> "LogicRecord":
        record = cls(steps=steps)
        result = record.validate_self_consistency()
        if not result["ok"]:
            errors = "; ".join(result["errors"])
            raise ValueError(f"logic record is inconsistent: {errors}")
        return record

    def validate_self_consistency(self) -> dict[str, Any]:
        seen: set[str] = set()
        errors: list[str] = []

        for step in self.steps:
            if step.step_id in seen:
                errors.append(f"duplicate step id: {step.step_id}")
            for dep in step.depends_on:
                if dep not in seen:
                    errors.append(
                        f"step {step.step_id} depends on missing or future step: {dep}"
                    )
            seen.add(step.step_id)

        return {"ok": len(errors) == 0, "errors": errors}

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "self_consistency": self.validate_self_consistency(),
        }

    def export_json(self, path: str | Path) -> None:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def modules_to_list(combo: set[Module]) -> list[str]:
    return sorted(item.value for item in combo)


def strict_mapping_meta() -> dict[str, str]:
    return {
        "level": STRICT_MAPPING_LEVEL,
        "registry": STRICT_MAPPING_REGISTRY,
        "validation_command": STRICT_MAPPING_VALIDATION_COMMAND,
    }

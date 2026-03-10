from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, Callable

from project_runtime.aitrans import (
    SUPPORTED_PROJECT_TEMPLATE as AITRANS_TEMPLATE,
    load_aitrans_project,
    materialize_aitrans_project,
)
from project_runtime.knowledge_base import (
    SUPPORTED_PROJECT_TEMPLATE as KNOWLEDGE_BASE_TEMPLATE,
    load_knowledge_base_project,
    materialize_knowledge_base_project,
)

ProjectLoader = Callable[[str | Path], Any]
ProjectMaterializer = Callable[[str | Path, str | Path | None], Any]
REPO_ROOT = Path(__file__).resolve().parents[2]


def _normalize_project_path(project_file: str | Path) -> Path:
    project_path = Path(project_file)
    if not project_path.is_absolute():
        project_path = REPO_ROOT / project_path
    return project_path.resolve()


def detect_project_template(product_spec_file: str | Path) -> str:
    resolved_file = _normalize_project_path(product_spec_file)
    with resolved_file.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"project spec must decode into a table: {resolved_file}")
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError(f"missing required [project] table: {resolved_file}")
    template = project.get("template")
    if not isinstance(template, str) or not template.strip():
        raise ValueError(f"missing required project.template: {resolved_file}")
    return template.strip()


PROJECT_LOADERS: dict[str, ProjectLoader] = {
    KNOWLEDGE_BASE_TEMPLATE: load_knowledge_base_project,
    AITRANS_TEMPLATE: load_aitrans_project,
}

PROJECT_MATERIALIZERS: dict[str, ProjectMaterializer] = {
    KNOWLEDGE_BASE_TEMPLATE: materialize_knowledge_base_project,
    AITRANS_TEMPLATE: materialize_aitrans_project,
}


def load_project(product_spec_file: str | Path) -> Any:
    template = detect_project_template(product_spec_file)
    loader = PROJECT_LOADERS.get(template)
    if loader is None:
        raise ValueError(f"unsupported project template: {template}")
    return loader(product_spec_file)


def materialize_project(
    product_spec_file: str | Path,
    output_dir: str | Path | None = None,
) -> Any:
    template = detect_project_template(product_spec_file)
    materializer = PROJECT_MATERIALIZERS.get(template)
    if materializer is None:
        raise ValueError(f"unsupported project template: {template}")
    return materializer(product_spec_file, output_dir)

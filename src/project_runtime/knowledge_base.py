from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import tomllib
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE = REPO_ROOT / "projects/knowledge_base_basic/project.toml"
SUPPORTED_PROJECT_TEMPLATE = "knowledge_base_workbench"


@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    template: str
    display_name: str
    description: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectFrameworkRefs:
    frontend: str
    workspace: str
    backend: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompositionProfile:
    surface: str
    detail_flow: str
    write_flow: str
    supports_edit: bool
    supports_draft: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouteBoundaryValues:
    home: str
    workbench: str
    api_prefix: str
    workspace_flow: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FrontendBoundaryValues:
    page_title: str
    hero_kicker: str
    hero_title: str
    hero_copy: str
    contract_title: str
    contract_value: str
    contract_meta: str
    boundary_title: str
    boundary_meta: str
    search_title: str
    read_title: str
    compose_title: str
    query_button_label: str
    reset_button_label: str
    save_draft_label: str
    publish_label: str
    clear_label: str
    edit_label: str
    keyword_placeholder: str
    title_placeholder: str
    summary_placeholder: str
    body_placeholder: str
    tags_placeholder: str
    list_empty_title: str
    list_empty_description: str
    list_error_title: str
    list_error_description: str
    detail_empty_title: str
    detail_empty_description: str
    detail_no_selection_title: str
    detail_no_selection_description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackendConstraintProfile:
    default_page_size: int
    max_page_size: int
    max_tags_per_article: int
    min_title_length: int
    max_title_length: int
    min_summary_length: int
    max_summary_length: int
    min_body_length: int
    max_body_length: int
    allowed_statuses: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SceneProfile:
    scene_id: str
    title: str
    steps: tuple[str, ...]
    entry_path: str
    return_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SeedArticle:
    slug: str
    title: str
    summary: str
    body: str
    tags: tuple[str, ...]
    status: str
    updated_at: str
    related_slugs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeBaseProjectConfig:
    source_file: str
    metadata: ProjectMetadata
    framework_refs: ProjectFrameworkRefs
    composition_profile: CompositionProfile
    route_boundary_values: RouteBoundaryValues
    frontend_boundary_values: FrontendBoundaryValues
    backend_constraint_profile: BackendConstraintProfile
    scenes: tuple[SceneProfile, ...]
    seed_articles: tuple[SeedArticle, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def public_summary(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "project": self.metadata.to_dict(),
            "framework_refs": self.framework_refs.to_dict(),
            "composition_profile": self.composition_profile.to_dict(),
            "route_boundary_values": self.route_boundary_values.to_dict(),
            "backend_constraint_profile": self.backend_constraint_profile.to_dict(),
            "scene_count": len(self.scenes),
            "seed_article_count": len(self.seed_articles),
        }


def _normalize_project_path(project_file: str | Path) -> Path:
    project_path = Path(project_file)
    if not project_path.is_absolute():
        project_path = (REPO_ROOT / project_path).resolve()
    return project_path


def _read_toml_file(project_path: Path) -> dict[str, Any]:
    if not project_path.exists():
        raise FileNotFoundError(f"missing project config: {project_path}")
    with project_path.open("rb") as fh:
        data = tomllib.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"project config must decode into object: {project_path}")
    return data


def _require_table(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing required table: {key}")
    return value


def _require_string(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required string: {key}")
    return value.strip()


def _require_bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing required bool: {key}")
    return value


def _require_int(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if not isinstance(value, int):
        raise ValueError(f"missing required int: {key}")
    return value


def _require_string_tuple(parent: dict[str, Any], key: str) -> tuple[str, ...]:
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing required string list: {key}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key} must only contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _require_scene_profiles(data: dict[str, Any]) -> tuple[SceneProfile, ...]:
    value = data.get("scenes")
    if not isinstance(value, list) or not value:
        raise ValueError("project config must define non-empty [[scenes]]")

    seen_scene_ids: set[str] = set()
    scenes: list[SceneProfile] = []
    for raw_scene in value:
        if not isinstance(raw_scene, dict):
            raise ValueError("each [[scenes]] entry must be a table")
        scene = SceneProfile(
            scene_id=_require_string(raw_scene, "scene_id"),
            title=_require_string(raw_scene, "title"),
            steps=_require_string_tuple(raw_scene, "steps"),
            entry_path=_require_string(raw_scene, "entry_path"),
            return_path=_require_string(raw_scene, "return_path"),
        )
        if scene.scene_id in seen_scene_ids:
            raise ValueError(f"duplicate scene_id: {scene.scene_id}")
        seen_scene_ids.add(scene.scene_id)
        scenes.append(scene)
    return tuple(scenes)


def _require_seed_articles(data: dict[str, Any]) -> tuple[SeedArticle, ...]:
    value = data.get("seed_articles")
    if not isinstance(value, list) or not value:
        raise ValueError("project config must define non-empty [[seed_articles]]")

    seen_slugs: set[str] = set()
    articles: list[SeedArticle] = []
    for raw_article in value:
        if not isinstance(raw_article, dict):
            raise ValueError("each [[seed_articles]] entry must be a table")
        article = SeedArticle(
            slug=_require_string(raw_article, "slug"),
            title=_require_string(raw_article, "title"),
            summary=_require_string(raw_article, "summary"),
            body=_require_string(raw_article, "body"),
            tags=_require_string_tuple(raw_article, "tags"),
            status=_require_string(raw_article, "status"),
            updated_at=_require_string(raw_article, "updated_at"),
            related_slugs=_require_string_tuple(raw_article, "related_slugs")
            if raw_article.get("related_slugs")
            else tuple(),
        )
        if article.slug in seen_slugs:
            raise ValueError(f"duplicate seed article slug: {article.slug}")
        seen_slugs.add(article.slug)
        articles.append(article)
    return tuple(articles)


def _validate_project_config(config: KnowledgeBaseProjectConfig) -> KnowledgeBaseProjectConfig:
    if config.metadata.template != SUPPORTED_PROJECT_TEMPLATE:
        raise ValueError(f"unsupported project template: {config.metadata.template}")

    for framework_file in config.framework_refs.to_dict().values():
        framework_path = REPO_ROOT / framework_file
        if not framework_path.exists():
            raise ValueError(f"framework ref does not exist: {framework_file}")

    routes = config.route_boundary_values
    for route_value in routes.to_dict().values():
        if not route_value.startswith("/"):
            raise ValueError(f"route must start with '/': {route_value}")
    if routes.home == routes.workbench:
        raise ValueError("home route must not equal workbench route")
    if not routes.api_prefix.startswith("/api"):
        raise ValueError("api_prefix must start with '/api'")
    if not routes.workspace_flow.startswith(routes.api_prefix):
        raise ValueError("workspace_flow must stay under api_prefix")

    constraints = config.backend_constraint_profile
    if constraints.default_page_size <= 0:
        raise ValueError("default_page_size must be positive")
    if constraints.max_page_size < constraints.default_page_size:
        raise ValueError("max_page_size must be >= default_page_size")
    if constraints.max_tags_per_article <= 0:
        raise ValueError("max_tags_per_article must be positive")
    if constraints.min_title_length <= 0 or constraints.max_title_length < constraints.min_title_length:
        raise ValueError("title length constraints are invalid")
    if constraints.min_summary_length <= 0 or constraints.max_summary_length < constraints.min_summary_length:
        raise ValueError("summary length constraints are invalid")
    if constraints.min_body_length <= 0 or constraints.max_body_length < constraints.min_body_length:
        raise ValueError("body length constraints are invalid")
    if not constraints.allowed_statuses:
        raise ValueError("allowed_statuses must not be empty")
    if len(set(constraints.allowed_statuses)) != len(constraints.allowed_statuses):
        raise ValueError("allowed_statuses must not contain duplicates")
    if "published" not in constraints.allowed_statuses:
        raise ValueError("allowed_statuses must include published")
    if config.composition_profile.supports_draft and "draft" not in constraints.allowed_statuses:
        raise ValueError("draft support requires draft in allowed_statuses")

    scene_ids = {scene.scene_id for scene in config.scenes}
    required_scene_ids = {"browse", "read", "write"}
    if config.composition_profile.supports_edit:
        required_scene_ids.add("edit")
    missing_scenes = sorted(required_scene_ids.difference(scene_ids))
    if missing_scenes:
        raise ValueError(f"missing required scenes for template: {missing_scenes}")

    seen_article_titles: set[str] = set()
    for article in config.seed_articles:
        if article.status not in constraints.allowed_statuses:
            raise ValueError(f"seed article uses unsupported status: {article.slug}")
        if not constraints.min_title_length <= len(article.title.strip()) <= constraints.max_title_length:
            raise ValueError(f"seed article title violates title length constraints: {article.slug}")
        if not constraints.min_summary_length <= len(article.summary.strip()) <= constraints.max_summary_length:
            raise ValueError(f"seed article summary violates summary length constraints: {article.slug}")
        if not constraints.min_body_length <= len(article.body.strip()) <= constraints.max_body_length:
            raise ValueError(f"seed article body violates body length constraints: {article.slug}")
        if len(article.tags) > constraints.max_tags_per_article:
            raise ValueError(f"seed article tags exceed max_tags_per_article: {article.slug}")
        normalized_title = article.title.strip().lower()
        if normalized_title in seen_article_titles:
            raise ValueError(f"duplicate seed article title: {article.title}")
        seen_article_titles.add(normalized_title)

    return config


def load_knowledge_base_project(
    project_file: str | Path = DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE,
) -> KnowledgeBaseProjectConfig:
    project_path = _normalize_project_path(project_file)
    raw = _read_toml_file(project_path)
    try:
        source_file = project_path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        source_file = str(project_path)

    project_table = _require_table(raw, "project")
    framework_refs_table = _require_table(raw, "framework_refs")
    composition_table = _require_table(raw, "composition_profile")

    boundary_values = _require_table(raw, "boundary_values")
    route_table = _require_table(boundary_values, "routes")
    frontend_table = _require_table(boundary_values, "frontend")

    constraint_profile = _require_table(raw, "constraint_profile")
    backend_table = _require_table(constraint_profile, "backend")

    config = KnowledgeBaseProjectConfig(
        source_file=source_file,
        metadata=ProjectMetadata(
            project_id=_require_string(project_table, "project_id"),
            template=_require_string(project_table, "template"),
            display_name=_require_string(project_table, "display_name"),
            description=_require_string(project_table, "description"),
            version=_require_string(project_table, "version"),
        ),
        framework_refs=ProjectFrameworkRefs(
            frontend=_require_string(framework_refs_table, "frontend"),
            workspace=_require_string(framework_refs_table, "workspace"),
            backend=_require_string(framework_refs_table, "backend"),
        ),
        composition_profile=CompositionProfile(
            surface=_require_string(composition_table, "surface"),
            detail_flow=_require_string(composition_table, "detail_flow"),
            write_flow=_require_string(composition_table, "write_flow"),
            supports_edit=_require_bool(composition_table, "supports_edit"),
            supports_draft=_require_bool(composition_table, "supports_draft"),
        ),
        route_boundary_values=RouteBoundaryValues(
            home=_require_string(route_table, "home"),
            workbench=_require_string(route_table, "workbench"),
            api_prefix=_require_string(route_table, "api_prefix"),
            workspace_flow=_require_string(route_table, "workspace_flow"),
        ),
        frontend_boundary_values=FrontendBoundaryValues(
            page_title=_require_string(frontend_table, "page_title"),
            hero_kicker=_require_string(frontend_table, "hero_kicker"),
            hero_title=_require_string(frontend_table, "hero_title"),
            hero_copy=_require_string(frontend_table, "hero_copy"),
            contract_title=_require_string(frontend_table, "contract_title"),
            contract_value=_require_string(frontend_table, "contract_value"),
            contract_meta=_require_string(frontend_table, "contract_meta"),
            boundary_title=_require_string(frontend_table, "boundary_title"),
            boundary_meta=_require_string(frontend_table, "boundary_meta"),
            search_title=_require_string(frontend_table, "search_title"),
            read_title=_require_string(frontend_table, "read_title"),
            compose_title=_require_string(frontend_table, "compose_title"),
            query_button_label=_require_string(frontend_table, "query_button_label"),
            reset_button_label=_require_string(frontend_table, "reset_button_label"),
            save_draft_label=_require_string(frontend_table, "save_draft_label"),
            publish_label=_require_string(frontend_table, "publish_label"),
            clear_label=_require_string(frontend_table, "clear_label"),
            edit_label=_require_string(frontend_table, "edit_label"),
            keyword_placeholder=_require_string(frontend_table, "keyword_placeholder"),
            title_placeholder=_require_string(frontend_table, "title_placeholder"),
            summary_placeholder=_require_string(frontend_table, "summary_placeholder"),
            body_placeholder=_require_string(frontend_table, "body_placeholder"),
            tags_placeholder=_require_string(frontend_table, "tags_placeholder"),
            list_empty_title=_require_string(frontend_table, "list_empty_title"),
            list_empty_description=_require_string(frontend_table, "list_empty_description"),
            list_error_title=_require_string(frontend_table, "list_error_title"),
            list_error_description=_require_string(frontend_table, "list_error_description"),
            detail_empty_title=_require_string(frontend_table, "detail_empty_title"),
            detail_empty_description=_require_string(frontend_table, "detail_empty_description"),
            detail_no_selection_title=_require_string(frontend_table, "detail_no_selection_title"),
            detail_no_selection_description=_require_string(frontend_table, "detail_no_selection_description"),
        ),
        backend_constraint_profile=BackendConstraintProfile(
            default_page_size=_require_int(backend_table, "default_page_size"),
            max_page_size=_require_int(backend_table, "max_page_size"),
            max_tags_per_article=_require_int(backend_table, "max_tags_per_article"),
            min_title_length=_require_int(backend_table, "min_title_length"),
            max_title_length=_require_int(backend_table, "max_title_length"),
            min_summary_length=_require_int(backend_table, "min_summary_length"),
            max_summary_length=_require_int(backend_table, "max_summary_length"),
            min_body_length=_require_int(backend_table, "min_body_length"),
            max_body_length=_require_int(backend_table, "max_body_length"),
            allowed_statuses=_require_string_tuple(backend_table, "allowed_statuses"),
        ),
        scenes=_require_scene_profiles(raw),
        seed_articles=_require_seed_articles(raw),
    )
    return _validate_project_config(config)

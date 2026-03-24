from __future__ import annotations

from typing import Any

from project_runtime.models import ProjectRuntimeAssembly


def resolve_runtime_blueprint(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "runtime_blueprint")


def resolve_frontend_app_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "frontend_app_spec")


def resolve_review_workbench_domain_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "review_workbench_domain_spec")


def resolve_backend_service_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "backend_service_spec")


def project_runtime_public_summary(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    frontend_spec = resolve_frontend_app_spec(project)
    domain_spec = resolve_review_workbench_domain_spec(project)
    backend_spec = resolve_backend_service_spec(project)
    blueprint = resolve_runtime_blueprint(project)
    workbench = domain_spec.get("workbench", {})
    scenes = workbench.get("scenes", [])
    return {
        "project_file": project.project_file,
        "project": project.metadata.to_dict(),
        "framework": [item.to_dict() for item in project.config.framework_modules],
        "route": frontend_spec.get("contract", {}).get("route_contract", {}),
        "resolved_module_ids": sorted(project.root_module_ids.values()),
        "module_chain": ["framework", "config", "code", "evidence"],
        "platform_summary": {
            "default_scene_id": workbench.get("default_scene_id"),
            "scene_count": len(scenes) if isinstance(scenes, list) else 0,
            "scene_ids": workbench.get("scene_ids", []),
        },
        "frontend_summary": {
            "page_ids": list(frontend_spec.get("ui", {}).get("pages", {}).keys()),
            "component_ids": list(frontend_spec.get("ui", {}).get("components", {}).keys()),
        },
        "backend_summary": {
            "transport": backend_spec.get("transport", {}),
            "contracts": backend_spec.get("contracts", {}),
        },
        "runtime_summary": {
            "landing_path": blueprint.get("landing_path"),
            "page_route_ids": [
                item.get("route_id")
                for item in blueprint.get("page_routes", [])
                if isinstance(item, dict)
            ],
        },
        "validation_reports": project.validation_reports.to_dict(),
        "generated_artifacts": project.generated_artifacts.to_dict() if project.generated_artifacts else None,
    }


def _require_dict_export(project: ProjectRuntimeAssembly, export_key: str) -> dict[str, Any]:
    value = project.require_runtime_export(export_key)
    if not isinstance(value, dict):
        raise ValueError(f"runtime export must be a dict: {export_key}")
    return dict(value)

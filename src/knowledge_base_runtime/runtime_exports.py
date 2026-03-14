from __future__ import annotations

from typing import Any

from project_runtime import KnowledgeDocument, ProjectRuntimeAssembly


def resolve_runtime_blueprint(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "runtime_blueprint")


def resolve_frontend_app_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "frontend_app_spec")


def resolve_knowledge_base_domain_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "knowledge_base_domain_spec")


def resolve_backend_service_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return _require_dict_export(project, "backend_service_spec")


def resolve_runtime_documents(project: ProjectRuntimeAssembly) -> tuple[KnowledgeDocument, ...]:
    value = project.require_runtime_export("runtime_documents")
    if not isinstance(value, list):
        raise ValueError("runtime blueprint requires runtime_documents export")
    raw_documents = value
    if not isinstance(raw_documents, list):
        raise ValueError("runtime blueprint requires runtime_documents export")
    documents = tuple(
        KnowledgeDocument.from_dict(item)
        for item in raw_documents
        if isinstance(item, dict)
    )
    if not documents:
        raise ValueError("runtime blueprint requires at least one compiled document")
    return documents


def project_runtime_routes(project: ProjectRuntimeAssembly) -> dict[str, dict[str, str]]:
    route = project.route
    return {
        "pages": {
            "home": route.home,
            "chat_home": route.workbench,
            "basketball_showcase": route.basketball_showcase,
            "knowledge_list": route.knowledge_list,
            "knowledge_detail": f"{route.knowledge_detail}/{{knowledge_base_id}}",
            "document_detail": f"{route.document_detail_prefix}/{{document_id}}",
        },
        "api": {
            "knowledge_bases": f"{route.api_prefix}/knowledge-bases",
            "knowledge_base_detail": f"{route.api_prefix}/knowledge-bases/{{knowledge_base_id}}",
            "documents": f"{route.api_prefix}/documents",
            "create_document": f"{route.api_prefix}/documents",
            "document_detail": f"{route.api_prefix}/documents/{{document_id}}",
            "delete_document": f"{route.api_prefix}/documents/{{document_id}}",
            "section_detail": f"{route.api_prefix}/documents/{{document_id}}/sections/{{section_id}}",
            "tags": f"{route.api_prefix}/tags",
            "chat_turns": f"{route.api_prefix}/chat/turns",
            "project_config": project.refinement.evidence.project_config_endpoint,
        },
    }


def project_runtime_public_summary(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    frontend_spec = resolve_frontend_app_spec(project)
    service_spec = resolve_backend_service_spec(project)
    documents = resolve_runtime_documents(project)
    blueprint = resolve_runtime_blueprint(project)
    ui = frontend_spec.get("ui", {})
    return {
        "project_file": project.project_file,
        "project": project.metadata.to_dict(),
        "selection": project.selection.to_dict(),
        "route": project.route.to_dict(),
        "a11y": project.a11y.to_dict(),
        "routes": project_runtime_routes(project),
        "document_count": len(documents),
        "resolved_module_ids": list(project.package_compile_order),
        "package_compile_order": list(project.package_compile_order),
        "frontend_summary": {
            "page_ids": list(ui.get("pages", {}).keys()) if isinstance(ui.get("pages"), dict) else [],
            "component_ids": list(ui.get("components", {}).keys()) if isinstance(ui.get("components"), dict) else [],
        },
        "runtime_summary": {
            "landing_path": blueprint.get("landing_path"),
            "page_route_ids": [
                item.get("route_id")
                for item in blueprint.get("page_routes", [])
                if isinstance(item, dict)
            ],
        },
        "backend_summary": {
            "retrieval": service_spec.get("retrieval", {}),
            "answer_policy": {
                "citation_style": service_spec.get("answer_policy", {}).get("citation_style"),
            },
        },
        "validation_reports": project.validation_reports.to_dict(),
        "generated_artifacts": project.generated_artifacts.to_dict() if project.generated_artifacts else None,
    }


def _require_dict_export(project: ProjectRuntimeAssembly, export_key: str) -> dict[str, Any]:
    value = project.require_runtime_export(export_key)
    if not isinstance(value, dict):
        raise ValueError(f"runtime export must be a dict: {export_key}")
    return dict(value)

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from knowledge_base_runtime.backend import KnowledgeRepository, build_knowledge_base_router
from knowledge_base_runtime.frontend import (
    compose_basketball_showcase_page,
    compose_document_detail_page,
    compose_knowledge_base_detail_page,
    compose_knowledge_base_list_page,
    compose_knowledge_base_page,
)
from knowledge_base_runtime.runtime_exports import (
    project_runtime_public_summary,
    resolve_backend_service_spec,
)
from project_runtime import ProjectRuntimeAssembly
from project_runtime.pipeline import load_project_runtime


@dataclass(frozen=True)
class BackendTransportContract:
    mode: str
    project_config_endpoint: str


def _require_backend_transport(project: ProjectRuntimeAssembly) -> BackendTransportContract:
    service_spec = resolve_backend_service_spec(project)
    transport = service_spec.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("backend_service_spec.transport is required for runtime app construction")
    mode = transport.get("mode")
    if not isinstance(mode, str):
        raise ValueError("backend_service_spec.transport.mode must be a string")
    project_config_endpoint = transport.get("project_config_endpoint")
    if not isinstance(project_config_endpoint, str) or not project_config_endpoint.startswith(project.route.api_prefix):
        raise ValueError("backend_service_spec.transport.project_config_endpoint must stay under route.api_prefix")
    return BackendTransportContract(mode=mode, project_config_endpoint=project_config_endpoint)


def build_project_runtime_app(project: ProjectRuntimeAssembly | None = None) -> FastAPI:
    assembly = project or load_project_runtime()
    transport = _require_backend_transport(assembly)
    repository = KnowledgeRepository(assembly)
    app = FastAPI(
        title=assembly.metadata.display_name,
        summary=assembly.metadata.description,
        version=assembly.metadata.version,
    )
    app.include_router(build_knowledge_base_router(assembly, repository))

    @app.get(assembly.route.home, include_in_schema=False)
    def root() -> dict[str, object]:
        return {
            "project": project_runtime_public_summary(assembly),
            "frontend": assembly.route.workbench,
            "project_config": transport.project_config_endpoint,
        }

    @app.get(assembly.route.workbench, response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_page() -> str:
        return compose_knowledge_base_page(assembly)

    @app.get(assembly.route.basketball_showcase, response_class=HTMLResponse, include_in_schema=False)
    def basketball_showcase_page() -> str:
        return compose_basketball_showcase_page(assembly)

    @app.get(assembly.route.knowledge_list, response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_list_page() -> str:
        return compose_knowledge_base_list_page(assembly, repository)

    @app.get(f"{assembly.route.knowledge_detail}/{{knowledge_base_id}}", response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_detail_page(knowledge_base_id: str) -> str:
        knowledge_base = repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return compose_knowledge_base_detail_page(assembly, knowledge_base)

    @app.get(
        f"{assembly.route.document_detail_prefix}/{{document_id}}",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def document_detail_page(document_id: str, section: str | None = None) -> str:
        document = repository.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return compose_document_detail_page(assembly, document, active_section_id=section)

    @app.get(transport.project_config_endpoint)
    def project_config() -> dict[str, object]:
        return assembly.project_config_view

    return app

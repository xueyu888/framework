from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from knowledge_base_demo.backend import build_knowledge_base_router, verify_knowledge_base_backend
from knowledge_base_demo.frontend import compose_knowledge_base_page, verify_knowledge_base_frontend
from knowledge_base_demo.workspace import compose_workspace_flow, verify_workspace_flow
from project_runtime.knowledge_base import KnowledgeBaseProjectConfig, load_knowledge_base_project


def build_knowledge_base_demo_app(
    project_config: KnowledgeBaseProjectConfig | None = None,
) -> FastAPI:
    config = project_config or load_knowledge_base_project()
    app = FastAPI(
        title=config.metadata.display_name,
        summary=config.metadata.description,
        version=config.metadata.version,
    )
    app.include_router(build_knowledge_base_router(config))

    @app.get(config.route_boundary_values.home, include_in_schema=False)
    def root() -> dict[str, object]:
        return {
            "project": config.public_summary(),
            "frontend": config.route_boundary_values.workbench,
            "openapi": "/docs",
            "workspace_flow": config.route_boundary_values.workspace_flow,
        }

    @app.get(config.route_boundary_values.workbench, response_class=HTMLResponse, include_in_schema=False)
    def knowledge_base_page() -> str:
        return compose_knowledge_base_page(config)

    @app.get(config.route_boundary_values.workspace_flow)
    def workspace_flow() -> dict[str, object]:
        return {
            "project": config.public_summary(),
            "scenes": [item.to_dict() for item in compose_workspace_flow(config)],
            "frontend_verification": verify_knowledge_base_frontend(config).to_dict(),
            "workspace_verification": verify_workspace_flow(config).to_dict(),
            "backend_verification": verify_knowledge_base_backend(config).to_dict(),
        }

    return app


app = build_knowledge_base_demo_app()

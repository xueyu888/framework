from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from framework_core import Base, BoundaryDefinition, BoundaryItem, Capability, VerificationInput, VerificationResult, verify
from project_runtime.knowledge_base import KnowledgeBaseProjectConfig, load_knowledge_base_project

KNOWLEDGE_BASE_WORKSPACE_CAPABILITIES = (
    Capability("C1", "Model browse, read, create, optional edit, and save scenes as one knowledge workspace"),
    Capability("C2", "Keep query context, selected article, and write or editing context stable across scenes"),
    Capability("C3", "Provide recoverable feedback loops for success, failure, and re-entry"),
    Capability("C4", "Exclude runtime shell concerns and backend storage details"),
)

KNOWLEDGE_BASE_WORKSPACE_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("SCENE", "browse, search, read, create, optional edit, and save scenes must follow the configured composition profile"),
        BoundaryItem("CONTEXT", "query context, selected article, and write or editing state must be transferable"),
        BoundaryItem("ENTRY", "home, deep link, create entry, and optional edit entry paths must be explicit"),
        BoundaryItem("RETURN", "detail, create, and optional edit scenes must expose stable return paths"),
        BoundaryItem("FEEDBACK", "save success, save failure, and empty-result feedback must be explicit"),
        BoundaryItem("OBS", "scene transitions and save outcomes must be observable"),
    )
)

KNOWLEDGE_BASE_WORKSPACE_BASES = (
    Base("B1", "browse-read scene base", "L1.M0[R1,R2]"),
    Base("B2", "write-feedback scene base", "L1.M1[R1,R2,R3]"),
    Base("B3", "context handoff base", "L1.M0[R2] + L1.M1[R2,R3]"),
)


@dataclass(frozen=True)
class WorkspaceScenario:
    scene_id: str
    title: str
    steps: tuple[str, ...]
    entry_path: str
    return_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_project_config(project_config: KnowledgeBaseProjectConfig | None) -> KnowledgeBaseProjectConfig:
    return project_config or load_knowledge_base_project()


def compose_workspace_flow(
    project_config: KnowledgeBaseProjectConfig | None = None,
) -> tuple[WorkspaceScenario, ...]:
    config = _resolve_project_config(project_config)
    return tuple(
        WorkspaceScenario(
            scene_id=scene.scene_id,
            title=scene.title,
            steps=scene.steps,
            entry_path=scene.entry_path,
            return_path=scene.return_path,
        )
        for scene in config.scenes
    )


def verify_workspace_flow(
    project_config: KnowledgeBaseProjectConfig | None = None,
) -> VerificationResult:
    config = _resolve_project_config(project_config)
    boundary_valid, boundary_errors = KNOWLEDGE_BASE_WORKSPACE_BOUNDARY.validate()
    base_result = verify(
        VerificationInput(
            subject="knowledge base workspace flow",
            pass_criteria=[
                (
                    "workspace scenes cover browse, read, create, and edit flows"
                    if config.composition_profile.supports_edit
                    else "workspace scenes cover browse, read, and create flows"
                ),
                "all scenes keep explicit entry and return paths",
                "context handoff remains observable",
            ],
            evidence={
                "project": config.public_summary(),
                "capabilities": [item.to_dict() for item in KNOWLEDGE_BASE_WORKSPACE_CAPABILITIES],
                "boundary": KNOWLEDGE_BASE_WORKSPACE_BOUNDARY.to_dict(),
                "bases": [item.to_dict() for item in KNOWLEDGE_BASE_WORKSPACE_BASES],
                "scenes": [item.to_dict() for item in compose_workspace_flow(config)],
            },
        )
    )
    reasons = [*boundary_errors, *base_result.reasons]
    return VerificationResult(
        passed=boundary_valid and base_result.passed,
        reasons=reasons,
        evidence=base_result.evidence,
    )

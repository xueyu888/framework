from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
import tomllib
from typing import TYPE_CHECKING, Any, Callable, get_args, get_origin, get_type_hints

from fastapi.routing import APIRoute
from framework_ir import FrameworkModuleIR, parse_framework_module

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_MANIFEST_VERSION = "governance-manifest/v1"
GOVERNANCE_TREE_VERSION = "governance-tree/v1"
GOVERNANCE_GENERATOR_VERSION = "project_runtime.governance/v1"

ANNOTATION_LINE_PATTERN = re.compile(r"^\s*#\s*@governed_symbol\s+(.*)$")
ANNOTATION_PAIR_PATTERN = re.compile(r"([a-z_]+)=([^\s]+)")
DEFINITION_LINE_PATTERN = re.compile(r"^\s*(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class GovernedBinding:
    symbol_id: str
    owner: str
    kind: str
    risk: str
    file: str
    locator: str
    line: int

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "locator": self.locator,
            "annotation": "governed_symbol",
            "line": self.line,
        }


@dataclass(frozen=True)
class UpstreamRef:
    layer: str
    file: str
    ref_kind: str
    ref_id: str

    def key(self) -> tuple[str, str, str, str]:
        return (self.layer, self.file, self.ref_kind, self.ref_id)

    def to_manifest_dict(self, digest: str | None = None) -> dict[str, Any]:
        payload = {
            "layer": self.layer,
            "file": self.file,
            "ref_kind": self.ref_kind,
            "ref_id": self.ref_id,
        }
        if digest is not None:
            payload["digest"] = digest
        return payload


@dataclass(frozen=True)
class SymbolDefinition:
    symbol_id: str
    owner: str
    kind: str
    risk: str
    expected_builder: Callable[[KnowledgeBaseProject], dict[str, Any]]
    actual_extractor: Callable[[KnowledgeBaseProject], dict[str, Any]]
    extractor: str
    comparator: str
    upstream_ref_builder: Callable[[KnowledgeBaseProject], tuple[UpstreamRef, ...]]
    required_bindings: tuple[tuple[str, str], ...]
    high_risk_file_checks: tuple[tuple[str, str], ...] = ()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _relative(path: Path | str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return str(candidate)
    return candidate.as_posix()


def _expected_generated_artifact_paths(project: KnowledgeBaseProject) -> dict[str, str]:
    if project.generated_artifacts is not None:
        return {
            "framework_ir_json": project.generated_artifacts.framework_ir_json,
            "product_spec_json": project.generated_artifacts.product_spec_json,
            "implementation_bundle_py": project.generated_artifacts.implementation_bundle_py,
            "generation_manifest_json": project.generated_artifacts.generation_manifest_json,
            "governance_manifest_json": project.generated_artifacts.governance_manifest_json,
            "governance_tree_json": project.generated_artifacts.governance_tree_json,
        }

    generated_dir = Path(project.product_spec_file).parent / "generated"
    artifact_names = project.implementation.artifacts
    return {
        "framework_ir_json": _relative(generated_dir / artifact_names.framework_ir_json),
        "product_spec_json": _relative(generated_dir / artifact_names.product_spec_json),
        "implementation_bundle_py": _relative(generated_dir / artifact_names.implementation_bundle_py),
        "generation_manifest_json": _relative(generated_dir / artifact_names.generation_manifest_json),
        "governance_manifest_json": _relative(generated_dir / artifact_names.governance_manifest_json),
        "governance_tree_json": _relative(generated_dir / artifact_names.governance_tree_json),
    }


def _metadata_pairs(fragment: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in ANNOTATION_PAIR_PATTERN.finditer(fragment)}


def scan_governed_python_bindings(file_path: Path) -> list[GovernedBinding]:
    rel_file = _relative(file_path)
    bindings: list[GovernedBinding] = []
    pending: tuple[dict[str, str], int] | None = None
    for line_number, raw_line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        annotation_match = ANNOTATION_LINE_PATTERN.match(raw_line)
        if annotation_match:
            pending = (_metadata_pairs(annotation_match.group(1)), line_number)
            continue
        if pending is None:
            continue
        stripped = raw_line.strip()
        definition_match = DEFINITION_LINE_PATTERN.match(raw_line)
        if definition_match is not None:
            metadata, annotation_line = pending
            symbol_id = metadata.get("id")
            owner = metadata.get("owner")
            kind = metadata.get("kind")
            risk = metadata.get("risk")
            if symbol_id and owner and kind and risk:
                name = definition_match.group(1)
                locator = ("class:" if stripped.startswith("class ") else "function:") + name
                bindings.append(
                    GovernedBinding(
                        symbol_id=symbol_id,
                        owner=owner,
                        kind=kind,
                        risk=risk,
                        file=rel_file,
                        locator=locator,
                        line=annotation_line,
                    )
                )
            pending = None
            continue
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("@")
            or stripped.endswith("(")
            or stripped.endswith(",")
            or stripped in {")", "]", "}"}
        ):
            continue
        if definition_match is None:
            pending = None
            continue
        pending = None
    return bindings


def collect_governed_bindings(files: list[str]) -> dict[str, list[GovernedBinding]]:
    index: dict[str, list[GovernedBinding]] = {}
    for rel_file in files:
        file_path = REPO_ROOT / rel_file
        if not file_path.exists():
            continue
        for binding in scan_governed_python_bindings(file_path):
            index.setdefault(binding.symbol_id, []).append(binding)
    return index


def _annotation_present_before_line(file_path: Path, line_number: int) -> bool:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    for index in range(line_number - 2, -1, -1):
        if index < 0 or index >= len(lines):
            continue
        candidate = lines[index].strip()
        if not candidate:
            continue
        if ANNOTATION_LINE_PATTERN.match(lines[index]):
            return True
        if (
            not candidate.startswith("#")
            and not candidate.startswith("@")
            and not candidate.endswith("(")
            and not candidate.endswith(",")
            and candidate not in {")", "]", "}"}
        ):
            break
    return False


def _route_decorated_function_names(
    file_path: Path,
    builder_name: str,
    receiver_name: str,
) -> list[tuple[str, int]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=file_path.as_posix())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == builder_name:
            results: list[tuple[str, int]] = []
            for child in node.body:
                if not isinstance(child, ast.FunctionDef):
                    continue
                if not any(_is_receiver_route_decorator(item, receiver_name) for item in child.decorator_list):
                    continue
                results.append((child.name, child.lineno))
            return results
    return []


def _is_receiver_route_decorator(node: ast.expr, receiver_name: str) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in {"get", "post", "delete"}:
        return False
    if not isinstance(func.value, ast.Name):
        return False
    return func.value.id == receiver_name


def find_unbound_high_risk_structures() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for rel_file, builder_name in (
        ("src/knowledge_base_runtime/app.py", "build_knowledge_base_runtime_app"),
        ("src/knowledge_base_runtime/backend.py", "build_knowledge_base_router"),
    ):
        file_path = REPO_ROOT / rel_file
        receiver_name = "app" if file_path.name == "app.py" else "router"
        for func_name, line_number in _route_decorated_function_names(file_path, builder_name, receiver_name):
            if _annotation_present_before_line(file_path, line_number):
                continue
            issues.append(
                {
                    "file": rel_file,
                    "line": line_number,
                    "locator": f"function:{func_name}",
                    "message": (
                        "New high-risk governed behavior detected but no governed_symbol binding found."
                    ),
                }
            )
    return issues


def _binding_validation_issues(
    binding_index: dict[str, list[GovernedBinding]],
    definitions: tuple[SymbolDefinition, ...],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    definitions_by_symbol = {item.symbol_id: item for item in definitions}
    allowed_bindings = {
        item.symbol_id: {(rel_file, locator) for rel_file, locator in item.required_bindings}
        for item in definitions
    }
    for symbol_id, bindings in binding_index.items():
        definition = definitions_by_symbol.get(symbol_id)
        if definition is None:
            for binding in bindings:
                issues.append(
                    {
                        "code": "UNKNOWN_BINDING",
                        "message": f"unknown governed symbol binding: {symbol_id}",
                        "file": binding.file,
                        "line": binding.line,
                        "symbol_id": symbol_id,
                        "locator": binding.locator,
                    }
                )
            continue
        allowed = allowed_bindings[symbol_id]
        for binding in bindings:
            if (binding.file, binding.locator) not in allowed:
                issues.append(
                    {
                        "code": "UNEXPECTED_BINDING",
                        "message": (
                            f"unexpected governed binding for {symbol_id}: "
                            f"{binding.file} -> {binding.locator}"
                        ),
                        "file": binding.file,
                        "line": binding.line,
                        "symbol_id": symbol_id,
                        "locator": binding.locator,
                    }
                )
            if (
                binding.owner != definition.owner
                or binding.kind != definition.kind
                or binding.risk != definition.risk
            ):
                issues.append(
                    {
                        "code": "INVALID_BINDING_METADATA",
                        "message": (
                            f"governed binding metadata mismatch for {symbol_id}: "
                            f"expected owner={definition.owner} kind={definition.kind} risk={definition.risk}"
                        ),
                        "file": binding.file,
                        "line": binding.line,
                        "symbol_id": symbol_id,
                        "locator": binding.locator,
                    }
                )
    return issues


def _framework_rule_refs(module: FrameworkModuleIR, rule_ids: tuple[str, ...] | None = None) -> tuple[UpstreamRef, ...]:
    allowed = set(rule_ids) if rule_ids else None
    refs: list[UpstreamRef] = []
    for rule in module.rules:
        if allowed is not None and rule.rule_id not in allowed:
            continue
        refs.append(
            UpstreamRef(
                layer="framework",
                file=module.path,
                ref_kind="rule",
                ref_id=rule.rule_id,
            )
        )
    return tuple(refs)


def _product_section_refs(product_spec_file: str, *sections: str) -> tuple[UpstreamRef, ...]:
    return tuple(
        UpstreamRef(
            layer="product_spec",
            file=product_spec_file,
            ref_kind="section",
            ref_id=section,
        )
        for section in sections
    )


def _implementation_section_refs(implementation_config_file: str, *sections: str) -> tuple[UpstreamRef, ...]:
    return tuple(
        UpstreamRef(
            layer="implementation_config",
            file=implementation_config_file,
            ref_kind="section",
            ref_id=section,
        )
        for section in sections
    )


def _route_detail_path(project: KnowledgeBaseProject) -> str:
    return f"{project.route.knowledge_detail}/{{knowledge_base_id}}"


def _document_detail_path(project: KnowledgeBaseProject) -> str:
    return f"{project.route.document_detail_prefix}/{{document_id}}"


def _expected_runtime_page_routes(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "home": project.route.home,
        "chat_home": project.route.workbench,
        "knowledge_list": project.route.knowledge_list,
        "knowledge_detail": _route_detail_path(project),
        "document_detail": _document_detail_path(project),
        "product_spec": project.implementation.evidence.product_spec_endpoint,
    }


def _actual_runtime_page_routes(project: KnowledgeBaseProject) -> dict[str, Any]:
    from knowledge_base_runtime.app import build_knowledge_base_runtime_app

    app = build_knowledge_base_runtime_app(project)
    expected_names = {
        "root": "home",
        "knowledge_base_page": "chat_home",
        "knowledge_base_list_page": "knowledge_list",
        "knowledge_base_detail_page": "knowledge_detail",
        "document_detail_page": "document_detail",
        "product_spec": "product_spec",
    }
    payload: dict[str, Any] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        key = expected_names.get(route.endpoint.__name__)
        if key is None:
            continue
        payload[key] = route.path
    return payload


def _expected_frontend_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    interaction_actions = [
        "start_new_chat",
        "select_session",
        "open_knowledge_switch",
        "search_documents",
        "select_document",
        "submit_chat",
        "open_citation_drawer",
        "browse_knowledge_bases",
        "open_knowledge_base_detail",
        "open_document_detail",
        "return_from_citation",
    ]
    if project.library.allow_create:
        interaction_actions.append("create_document")
    if project.library.allow_delete:
        interaction_actions.append("delete_document")
    return {
        "module_id": project.frontend_ir.module_id,
        "shell": project.surface.shell,
        "layout_variant": project.surface.layout_variant,
        "surface_config": {
            "sidebar_width": project.surface.sidebar_width,
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "surface_regions": [
            "conversation_sidebar",
            "chat_main",
            "citation_drawer",
            "knowledge_pages",
        ],
        "interaction_actions": interaction_actions,
        "state_channels": [
            {"state_id": "current_conversation", "sticky": True},
            {"state_id": "current_knowledge_base", "sticky": True},
            {"state_id": "current_document", "sticky": project.context.sticky_document},
            {"state_id": "current_section", "sticky": True},
            {"state_id": "citation_drawer_state", "sticky": True},
            {"state_id": "streaming_reply", "sticky": False},
        ],
        "route_contract": project.route.to_dict(),
        "a11y": project.a11y.to_dict(),
        "component_variants": {
            "conversation_list": project.library.list_variant,
            "preview_surface": project.preview.preview_variant,
            "chat_bubble": project.chat.bubble_variant,
            "chat_composer": project.chat.composer_variant,
            "citation_summary": project.return_config.citation_card_variant,
        },
        "base_ids": [item.base_id for item in project.frontend_ir.bases],
        "rule_ids": [item.rule_id for item in project.frontend_ir.rules],
    }


def _actual_frontend_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "module_id": project.frontend_contract["module_id"],
        "shell": project.frontend_contract["shell"],
        "layout_variant": project.frontend_contract["layout_variant"],
        "surface_config": project.frontend_contract["surface_config"],
        "surface_regions": [item["region_id"] for item in project.frontend_contract["surface_regions"]],
        "interaction_actions": [item["action_id"] for item in project.frontend_contract["interaction_actions"]],
        "state_channels": [
            {"state_id": item["state_id"], "sticky": item["sticky"]}
            for item in project.frontend_contract["state_channels"]
        ],
        "route_contract": project.frontend_contract["route_contract"],
        "a11y": project.frontend_contract["a11y"],
        "component_variants": project.frontend_contract["component_variants"],
        "base_ids": project.frontend_contract["base_ids"],
        "rule_ids": project.frontend_contract["rule_ids"],
    }


def _expected_workbench_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    library_actions = ["switch_knowledge_base", "browse_documents", "open_document_detail"]
    if project.library.allow_create:
        library_actions.append("create_document")
    if project.library.allow_delete:
        library_actions.append("delete_document")
    return {
        "module_id": project.domain_ir.module_id,
        "layout_variant": project.surface.layout_variant,
        "regions": [
            "conversation_sidebar",
            "chat_main",
            "citation_drawer",
            "knowledge_list_page",
            "knowledge_detail_page",
            "document_detail_page",
        ],
        "surface": {
            "sidebar_width": project.surface.sidebar_width,
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "library_actions": library_actions,
        "preview": {
            "anchor_mode": project.preview.anchor_mode,
            "show_toc": project.preview.show_toc,
            "preview_variant": project.preview.preview_variant,
        },
        "chat": {
            "citation_style": project.chat.citation_style,
            "mode": project.chat.mode,
        },
        "context": {
            "selection_mode": project.context.selection_mode,
            "max_citations": project.context.max_citations,
            "max_preview_sections": project.context.max_preview_sections,
        },
        "return": {
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
            "citation_card_variant": project.return_config.citation_card_variant,
        },
        "flow": [
            {
                "stage_id": "knowledge_base_select",
                "depends_on": [],
                "produces": ["knowledge_base_id"],
            },
            {
                "stage_id": "conversation",
                "depends_on": ["knowledge_base_id"],
                "produces": ["conversation_id", "answer", "citations"],
            },
            {
                "stage_id": "citation_review",
                "depends_on": ["conversation_id", "citations"],
                "produces": ["document_id", "section_id", "drawer_state"],
            },
            {
                "stage_id": "document_detail",
                "depends_on": ["document_id", "section_id"],
                "produces": ["document_page", "return_path"],
            },
        ],
        "citation_return_contract": {
            "query_keys": ["document", "section", "citation"],
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
        },
        "base_ids": [item.base_id for item in project.domain_ir.bases],
        "rule_ids": [item.rule_id for item in project.domain_ir.rules],
    }


def _actual_workbench_surface_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "module_id": project.workbench_contract["module_id"],
        "layout_variant": project.workbench_contract["layout_variant"],
        "regions": list(project.workbench_contract["regions"]),
        "surface": project.workbench_contract["surface"],
        "library_actions": list(project.workbench_contract["library"]["actions"]),
        "preview": {
            "anchor_mode": project.workbench_contract["preview"]["anchor_mode"],
            "show_toc": project.workbench_contract["preview"]["show_toc"],
            "preview_variant": project.workbench_contract["preview"]["preview_variant"],
        },
        "chat": {
            "citation_style": project.workbench_contract["chat"]["citation_style"],
            "mode": project.workbench_contract["chat"]["mode"],
        },
        "context": {
            "selection_mode": project.workbench_contract["context"]["selection_mode"],
            "max_citations": project.workbench_contract["context"]["max_citations"],
            "max_preview_sections": project.workbench_contract["context"]["max_preview_sections"],
        },
        "return": {
            "targets": list(project.workbench_contract["return"]["targets"]),
            "anchor_restore": project.workbench_contract["return"]["anchor_restore"],
            "citation_card_variant": project.workbench_contract["return"]["citation_card_variant"],
        },
        "flow": project.workbench_contract["flow"],
        "citation_return_contract": project.workbench_contract["citation_return_contract"],
        "base_ids": project.workbench_contract["base_ids"],
        "rule_ids": project.workbench_contract["rule_ids"],
    }


def _expected_ui_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": {
            "framework_modules": {
                "frontend": project.frontend_ir.module_id,
                "domain": project.domain_ir.module_id,
            },
            "boundary_sections": {
                "SURFACE": "surface",
                "VISUAL": "visual",
                "ROUTE": "route",
                "A11Y": "a11y",
                "LIBRARY": "library",
                "PREVIEW": "preview",
                "CHAT": "chat",
                "CONTEXT": "context",
                "RETURN": "return",
            },
            "rule_drivers": {
                "frontend": [item.rule_id for item in project.frontend_ir.rules],
                "domain": [item.rule_id for item in project.domain_ir.rules],
            },
        },
        "shell": {
            "id": project.surface.shell,
            "layout_variant": project.surface.layout_variant,
            "regions": ["conversation_sidebar", "chat_main", "citation_drawer"],
            "secondary_pages": ["knowledge_list", "knowledge_detail", "document_detail"],
            "preview_mode": project.surface.preview_mode,
            "density": project.surface.density,
        },
        "pages": {
            "chat_home": {
                "path": project.route.workbench,
                "slots": [
                    "conversation_sidebar",
                    "chat_header",
                    "message_stream",
                    "chat_composer",
                    "citation_drawer",
                    "knowledge_switch_dialog",
                ],
            },
            "knowledge_list": {
                "path": project.route.knowledge_list,
                "title": project.surface.copy.library_title,
            },
            "knowledge_detail": {
                "path": _route_detail_path(project),
            },
            "document_detail": {
                "path": _document_detail_path(project),
            },
        },
        "conversation": {
            "welcome_prompts": list(project.chat.welcome_prompts),
            "welcome_title": "今天想了解什么？",
        },
        "citation": {
            "style": project.chat.citation_style,
            "summary_variant": project.return_config.citation_card_variant,
            "drawer_sections": ["snippet", "source_context"],
            "document_detail_path": _document_detail_path(project),
        },
    }


def _actual_ui_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": project.ui_spec["derived_from"],
        "shell": {
            "id": project.ui_spec["shell"]["id"],
            "layout_variant": project.ui_spec["shell"]["layout_variant"],
            "regions": project.ui_spec["shell"]["regions"],
            "secondary_pages": project.ui_spec["shell"]["secondary_pages"],
            "preview_mode": project.ui_spec["shell"]["preview_mode"],
            "density": project.ui_spec["shell"]["density"],
        },
        "pages": {
            "chat_home": {
                "path": project.ui_spec["pages"]["chat_home"]["path"],
                "slots": project.ui_spec["pages"]["chat_home"]["slots"],
            },
            "knowledge_list": {
                "path": project.ui_spec["pages"]["knowledge_list"]["path"],
                "title": project.ui_spec["pages"]["knowledge_list"]["title"],
            },
            "knowledge_detail": {
                "path": project.ui_spec["pages"]["knowledge_detail"]["path"],
            },
            "document_detail": {
                "path": project.ui_spec["pages"]["document_detail"]["path"],
            },
        },
        "conversation": {
            "welcome_prompts": project.ui_spec["conversation"]["welcome_prompts"],
            "welcome_title": project.ui_spec["conversation"]["welcome_title"],
        },
        "citation": project.ui_spec["citation"],
    }


def _expected_backend_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": {
            "framework_modules": {
                "domain": project.domain_ir.module_id,
                "backend": project.backend_ir.module_id,
            },
            "boundary_sections": {
                "LIBRARY": "library",
                "PREVIEW": "preview",
                "CHAT": "chat",
                "CONTEXT": "context",
                "RETURN": "return",
            },
            "rule_drivers": {
                "domain": [item.rule_id for item in project.domain_ir.rules],
                "backend": [item.rule_id for item in project.backend_ir.rules],
            },
        },
        "knowledge_base": {
            "knowledge_base_id": project.library.knowledge_base_id,
            "knowledge_base_name": project.library.knowledge_base_name,
            "knowledge_base_description": project.library.knowledge_base_description,
            "source_types": list(project.library.source_types),
            "metadata_fields": list(project.library.metadata_fields),
        },
        "retrieval": {
            "max_preview_sections": project.context.max_preview_sections,
            "max_citations": project.context.max_citations,
            "selection_mode": project.context.selection_mode,
        },
        "interaction_flow": _expected_workbench_surface_contract(project)["flow"],
        "answer_policy": {
            "citation_style": project.chat.citation_style,
        },
        "return_policy": {
            "targets": list(project.return_config.targets),
            "anchor_restore": project.return_config.anchor_restore,
            "chat_path": project.route.workbench,
            "knowledge_base_detail_path": _route_detail_path(project),
            "document_detail_path": _document_detail_path(project),
        },
        "write_policy": {
            "allow_create": project.library.allow_create,
            "allow_delete": project.library.allow_delete,
        },
    }


def _actual_backend_surface_spec(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "derived_from": project.backend_spec["derived_from"],
        "knowledge_base": project.backend_spec["knowledge_base"],
        "retrieval": {
            "max_preview_sections": project.backend_spec["retrieval"]["max_preview_sections"],
            "max_citations": project.backend_spec["retrieval"]["max_citations"],
            "selection_mode": project.backend_spec["retrieval"]["selection_mode"],
        },
        "interaction_flow": project.backend_spec["interaction_flow"],
        "answer_policy": {
            "citation_style": project.backend_spec["answer_policy"]["citation_style"],
        },
        "return_policy": project.backend_spec["return_policy"],
        "write_policy": project.backend_spec["write_policy"],
    }


def _expected_api_library_contracts(project: KnowledgeBaseProject) -> dict[str, Any]:
    prefix = project.route.api_prefix
    return {
        "list_knowledge_bases": {
            "path": f"{prefix}/knowledge-bases",
            "method": "GET",
            "request_fields": [],
            "response_fields": [
                "knowledge_base_id",
                "name",
                "description",
                "document_count",
                "source_types",
                "updated_at",
            ],
            "citation_item_fields": [],
        },
        "get_knowledge_base": {
            "path": f"{prefix}/knowledge-bases/{{knowledge_base_id}}",
            "method": "GET",
            "request_fields": [],
            "response_fields": [
                "knowledge_base_id",
                "name",
                "description",
                "document_count",
                "source_types",
                "updated_at",
                "documents",
            ],
            "citation_item_fields": [],
        },
        "list_documents": {
            "path": f"{prefix}/documents",
            "method": "GET",
            "request_fields": [],
            "response_fields": [
                "document_id",
                "title",
                "summary",
                "tags",
                "updated_at",
                "section_count",
            ],
            "citation_item_fields": [],
        },
        "create_document": {
            "path": f"{prefix}/documents",
            "method": "POST",
            "request_fields": ["document_id", "title", "summary", "body_markdown", "tags", "updated_at"],
            "response_fields": ["document_id", "title", "summary", "tags", "updated_at", "section_count", "body_html", "sections"],
            "citation_item_fields": [],
        },
        "get_document": {
            "path": f"{prefix}/documents/{{document_id}}",
            "method": "GET",
            "request_fields": [],
            "response_fields": ["document_id", "title", "summary", "tags", "updated_at", "section_count", "body_html", "sections"],
            "citation_item_fields": [],
        },
        "get_section": {
            "path": f"{prefix}/documents/{{document_id}}/sections/{{section_id}}",
            "method": "GET",
            "request_fields": [],
            "response_fields": ["section_id", "title", "level", "html", "plain_text"],
            "citation_item_fields": [],
        },
        "delete_document": {
            "path": f"{prefix}/documents/{{document_id}}",
            "method": "DELETE",
            "request_fields": [],
            "response_fields": ["document_id", "deleted"],
            "citation_item_fields": [],
        },
        "list_tags": {
            "path": f"{prefix}/tags",
            "method": "GET",
            "request_fields": [],
            "response_fields": ["items"],
            "citation_item_fields": [],
        },
    }


def _expected_api_chat_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    prefix = project.route.api_prefix
    return {
        "create_chat_turn": {
            "path": f"{prefix}/chat/turns",
            "method": "POST",
            "request_fields": ["message", "document_id", "section_id"],
            "response_fields": ["answer", "citations", "context_document_id", "context_section_id"],
            "citation_item_fields": [
                "citation_id",
                "document_id",
                "document_title",
                "section_id",
                "section_title",
                "snippet",
                "return_path",
                "document_path",
            ],
        }
    }


def _route_contracts_from_router(project: KnowledgeBaseProject) -> dict[str, dict[str, Any]]:
    from knowledge_base_runtime.backend import KnowledgeRepository, build_knowledge_base_router

    router = build_knowledge_base_router(project, KnowledgeRepository(project))
    payload: dict[str, dict[str, Any]] = {}
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        payload[route.endpoint.__name__] = {
            "path": route.path,
            "method": next(iter(sorted(route.methods - {'HEAD', 'OPTIONS'})), ""),
            "request_fields": _request_model_fields(route.endpoint),
            "response_fields": _response_model_fields(route.response_model),
            "citation_item_fields": _nested_response_model_fields(route.response_model, "citations"),
        }
    return payload


def _actual_api_library_contracts(project: KnowledgeBaseProject) -> dict[str, Any]:
    route_contracts = _route_contracts_from_router(project)
    wanted = (
        "list_knowledge_bases",
        "get_knowledge_base",
        "list_documents",
        "create_document",
        "get_document",
        "get_section",
        "delete_document",
        "list_tags",
    )
    return {key: route_contracts[key] for key in wanted}


def _actual_api_chat_contract(project: KnowledgeBaseProject) -> dict[str, Any]:
    route_contracts = _route_contracts_from_router(project)
    return {"create_chat_turn": route_contracts["create_chat_turn"]}


def _response_model_fields(model: Any) -> list[str]:
    model_type = _unwrap_model_type(model)
    if model_type is None:
        return []
    fields = getattr(model_type, "model_fields", None)
    if not isinstance(fields, dict):
        return []
    return list(fields.keys())


def _nested_response_model_fields(model: Any, field_name: str) -> list[str]:
    model_type = _unwrap_model_type(model)
    if model_type is None:
        return []
    fields = getattr(model_type, "model_fields", None)
    if not isinstance(fields, dict) or field_name not in fields:
        return []
    annotation = fields[field_name].annotation
    nested_type = _unwrap_model_type(annotation)
    if nested_type is None:
        return []
    nested_fields = getattr(nested_type, "model_fields", None)
    if not isinstance(nested_fields, dict):
        return []
    return list(nested_fields.keys())


def _request_model_fields(func: Callable[..., Any]) -> list[str]:
    signature = inspect.signature(func)
    try:
        resolved_hints = get_type_hints(func, globalns=getattr(func, "__globals__", {}), localns=None)
    except Exception:
        resolved_hints = {}
    for parameter in signature.parameters.values():
        annotation = resolved_hints.get(parameter.name, parameter.annotation)
        model_type = _unwrap_model_type(annotation)
        if model_type is None:
            continue
        fields = getattr(model_type, "model_fields", None)
        if isinstance(fields, dict):
            return list(fields.keys())
    return []


def _unwrap_model_type(model: Any) -> Any | None:
    if model is None:
        return None
    origin = get_origin(model)
    if origin in {list, tuple}:
        args = get_args(model)
        return _unwrap_model_type(args[0] if args else None)
    return model


def _expected_answer_behavior(project: KnowledgeBaseProject) -> dict[str, Any]:
    return {
        "citation_style": project.chat.citation_style,
        "citation_required": project.chat.citations_enabled,
        "max_citations_respected": True,
        "return_path_prefix": project.route.workbench,
        "document_path_prefix": project.route.document_detail_prefix,
        "context_tracks_lead": True,
    }


def _actual_answer_behavior(project: KnowledgeBaseProject) -> dict[str, Any]:
    from knowledge_base_runtime.backend import KnowledgeRepository

    repository = KnowledgeRepository(project)
    response = repository.answer_question(
        "Explain the generated runtime and citation drawer.",
        document_id="framework-compilation-chain",
        section_id="generated-runtime",
    )
    citations = list(response.citations)
    citation_style = "inline_refs" if citations and "[1]" in response.answer else "missing_inline_refs"
    return_path_prefix = project.route.workbench
    document_path_prefix = project.route.document_detail_prefix
    if citations and not all(item.return_path.startswith(f"{return_path_prefix}?") for item in citations):
        return_path_prefix = "mismatch"
    if citations and not all(item.document_path.startswith(document_path_prefix) for item in citations):
        document_path_prefix = "mismatch"
    context_tracks_lead = True
    if citations:
        lead = citations[0]
        context_tracks_lead = (
            response.context_document_id == lead.document_id
            and response.context_section_id == lead.section_id
        )
    return {
        "citation_style": citation_style,
        "citation_required": bool(citations),
        "max_citations_respected": len(citations) <= project.context.max_citations,
        "return_path_prefix": return_path_prefix,
        "document_path_prefix": document_path_prefix,
        "context_tracks_lead": context_tracks_lead,
    }


def _definitions(project: KnowledgeBaseProject) -> tuple[SymbolDefinition, ...]:
    product_spec_file = project.product_spec_file
    implementation_config_file = project.implementation_config_file
    frontend_refs = _framework_rule_refs(project.frontend_ir)
    domain_refs = _framework_rule_refs(project.domain_ir)
    backend_refs = _framework_rule_refs(project.backend_ir)
    return (
        SymbolDefinition(
            symbol_id="kb.runtime.page_routes",
            owner="framework",
            kind="runtime_routes",
            risk="high",
            expected_builder=_expected_runtime_page_routes,
            actual_extractor=_actual_runtime_page_routes,
            extractor="python.runtime_routes.v1",
            comparator="exact_contract.v1",
            upstream_ref_builder=lambda current: (
                *frontend_refs,
                *_product_section_refs(product_spec_file, "route"),
                *_implementation_section_refs(implementation_config_file, "evidence"),
            ),
            required_bindings=(
                ("src/knowledge_base_runtime/app.py", "function:root"),
                ("src/knowledge_base_runtime/app.py", "function:knowledge_base_page"),
                ("src/knowledge_base_runtime/app.py", "function:knowledge_base_list_page"),
                ("src/knowledge_base_runtime/app.py", "function:knowledge_base_detail_page"),
                ("src/knowledge_base_runtime/app.py", "function:document_detail_page"),
                ("src/knowledge_base_runtime/app.py", "function:product_spec"),
            ),
            high_risk_file_checks=(("src/knowledge_base_runtime/app.py", "build_knowledge_base_runtime_app"),),
        ),
        SymbolDefinition(
            symbol_id="kb.frontend.surface_contract",
            owner="framework",
            kind="surface_contract",
            risk="high",
            expected_builder=_expected_frontend_surface_contract,
            actual_extractor=_actual_frontend_surface_contract,
            extractor="frontend.surface_contract.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *frontend_refs,
                *_product_section_refs(product_spec_file, "surface", "route", "a11y", "library", "preview", "chat", "return"),
            ),
            required_bindings=(("src/frontend_kernel/contracts.py", "function:build_frontend_contract"),),
        ),
        SymbolDefinition(
            symbol_id="kb.workbench.surface_contract",
            owner="framework",
            kind="surface_contract",
            risk="high",
            expected_builder=_expected_workbench_surface_contract,
            actual_extractor=_actual_workbench_surface_contract,
            extractor="python.workbench_surface.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *domain_refs,
                *_product_section_refs(product_spec_file, "library", "preview", "chat", "context", "return", "surface"),
            ),
            required_bindings=(("src/knowledge_base_framework/workbench.py", "function:build_workbench_contract"),),
        ),
        SymbolDefinition(
            symbol_id="kb.ui.surface_spec",
            owner="framework",
            kind="ui_surface",
            risk="high",
            expected_builder=_expected_ui_surface_spec,
            actual_extractor=_actual_ui_surface_spec,
            extractor="python.ui_surface.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *frontend_refs,
                *_product_section_refs(product_spec_file, "surface", "route", "chat", "return"),
            ),
            required_bindings=(("src/project_runtime/knowledge_base.py", "function:_build_ui_spec"),),
        ),
        SymbolDefinition(
            symbol_id="kb.backend.surface_spec",
            owner="implementation_config",
            kind="backend_surface",
            risk="high",
            expected_builder=_expected_backend_surface_spec,
            actual_extractor=_actual_backend_surface_spec,
            extractor="python.backend_surface.v1",
            comparator="surface_contract_exact.v1",
            upstream_ref_builder=lambda current: (
                *backend_refs,
                *_product_section_refs(product_spec_file, "library", "chat", "context", "return", "route"),
                *_implementation_section_refs(implementation_config_file, "backend"),
            ),
            required_bindings=(("src/project_runtime/knowledge_base.py", "function:_build_backend_spec"),),
        ),
        SymbolDefinition(
            symbol_id="kb.api.library_contracts",
            owner="framework",
            kind="api_contract",
            risk="high",
            expected_builder=_expected_api_library_contracts,
            actual_extractor=_actual_api_library_contracts,
            extractor="python.api_contract.v1",
            comparator="exact_contract.v1",
            upstream_ref_builder=lambda current: (
                *backend_refs,
                *_product_section_refs(product_spec_file, "route", "library", "preview"),
            ),
            required_bindings=(
                ("src/knowledge_base_runtime/backend.py", "function:list_knowledge_bases"),
                ("src/knowledge_base_runtime/backend.py", "function:get_knowledge_base"),
                ("src/knowledge_base_runtime/backend.py", "function:list_documents"),
                ("src/knowledge_base_runtime/backend.py", "function:create_document"),
                ("src/knowledge_base_runtime/backend.py", "function:get_document"),
                ("src/knowledge_base_runtime/backend.py", "function:get_section"),
                ("src/knowledge_base_runtime/backend.py", "function:delete_document"),
                ("src/knowledge_base_runtime/backend.py", "function:list_tags"),
            ),
            high_risk_file_checks=(("src/knowledge_base_runtime/backend.py", "build_knowledge_base_router"),),
        ),
        SymbolDefinition(
            symbol_id="kb.api.chat_contract",
            owner="framework",
            kind="api_contract",
            risk="high",
            expected_builder=_expected_api_chat_contract,
            actual_extractor=_actual_api_chat_contract,
            extractor="python.api_contract.v1",
            comparator="exact_contract.v1",
            upstream_ref_builder=lambda current: (
                *backend_refs,
                *_product_section_refs(product_spec_file, "route", "chat", "context", "return"),
            ),
            required_bindings=(("src/knowledge_base_runtime/backend.py", "function:create_chat_turn"),),
            high_risk_file_checks=(("src/knowledge_base_runtime/backend.py", "build_knowledge_base_router"),),
        ),
        SymbolDefinition(
            symbol_id="kb.answer.behavior",
            owner="product_spec",
            kind="answer_behavior",
            risk="high",
            expected_builder=_expected_answer_behavior,
            actual_extractor=_actual_answer_behavior,
            extractor="python.answer_behavior.v1",
            comparator="ordered_behavior_surface.v1",
            upstream_ref_builder=lambda current: (
                *domain_refs,
                *_product_section_refs(product_spec_file, "chat", "context", "return"),
                *_implementation_section_refs(implementation_config_file, "backend"),
            ),
            required_bindings=(
                ("src/knowledge_base_runtime/backend.py", "function:answer_question"),
            ),
        ),
    )


def governed_files_for_project(project: KnowledgeBaseProject) -> list[str]:
    files: set[str] = set()
    for definition in _definitions(project):
        for rel_file, _ in definition.required_bindings:
            files.add(rel_file)
    return sorted(files)


def _build_governance_snapshot(project: KnowledgeBaseProject) -> dict[str, Any]:
    definitions = _definitions(project)
    bindings_by_symbol = collect_governed_bindings(governed_files_for_project(project))
    binding_issues = _binding_validation_issues(bindings_by_symbol, definitions)
    if binding_issues:
        details = "; ".join(
            f"{item['file']}:{item['line']} {item['code']} {item['message']}" for item in binding_issues
        )
        raise ValueError(f"invalid governed bindings: {details}")
    unbound = find_unbound_high_risk_structures()
    if unbound:
        details = "; ".join(f"{item['file']}:{item['line']} -> {item['locator']}" for item in unbound)
        raise ValueError(f"missing governed_symbol binding for high-risk structures: {details}")
    upstream_closure: dict[tuple[str, str, str, str], str] = {}
    symbols: list[dict[str, Any]] = []
    for definition in definitions:
        bindings = sorted(
            bindings_by_symbol.get(definition.symbol_id, []),
            key=lambda item: (item.file, item.line, item.locator),
        )
        missing_bindings = [
            f"{rel_file} -> {locator}"
            for rel_file, locator in definition.required_bindings
            if not _binding_exists(bindings_by_symbol, definition.symbol_id, rel_file, locator)
        ]
        if missing_bindings:
            raise ValueError(
                f"missing governed_symbol binding(s) for {definition.symbol_id}: {', '.join(missing_bindings)}"
            )
        expected_evidence = definition.expected_builder(project)
        upstream_refs = definition.upstream_ref_builder(project)
        for ref in upstream_refs:
            upstream_closure[ref.key()] = digest_upstream_ref(ref)
        symbols.append(
            {
                "symbol_id": definition.symbol_id,
                "owner": definition.owner,
                "kind": definition.kind,
                "risk": definition.risk,
                "bindings": [item.to_manifest_dict() for item in bindings],
                "upstream_refs": [
                    ref.to_manifest_dict(digest=upstream_closure[ref.key()])
                    for ref in upstream_refs
                ],
                "expected": {
                    "extractor": definition.extractor,
                    "comparator": definition.comparator,
                    "fingerprint": _fingerprint(expected_evidence),
                    "evidence": expected_evidence,
                },
            }
        )
    closure_items = [
        {
            "layer": layer,
            "file": file_name,
            "ref_kind": ref_kind,
            "ref_id": ref_id,
            "digest": digest,
        }
        for (layer, file_name, ref_kind, ref_id), digest in sorted(upstream_closure.items())
    ]
    return {
        "definitions": definitions,
        "symbols": symbols,
        "upstream_closure": closure_items,
    }


def build_governance_manifest(project: KnowledgeBaseProject) -> dict[str, Any]:
    snapshot = _build_governance_snapshot(project)
    return {
        "manifest_version": GOVERNANCE_MANIFEST_VERSION,
        "project_id": project.metadata.project_id,
        "generator_version": GOVERNANCE_GENERATOR_VERSION,
        "upstream_closure": snapshot["upstream_closure"],
        "symbols": snapshot["symbols"],
    }


def build_governance_tree(project: KnowledgeBaseProject) -> dict[str, Any]:
    snapshot = _build_governance_snapshot(project)
    project_root_id = f"project:{project.metadata.project_id}"
    framework_root_id = f"{project_root_id}:framework"
    product_root_id = f"{project_root_id}:product_spec"
    implementation_root_id = f"{project_root_id}:implementation_config"
    code_root_id = f"{project_root_id}:code"
    evidence_root_id = f"{project_root_id}:evidence"

    nodes: dict[str, dict[str, Any]] = {}

    def add_node(node_id: str, *, parent: str | None, **payload: Any) -> dict[str, Any]:
        existing = nodes.get(node_id)
        if existing is None:
            existing = {
                "node_id": node_id,
                "parent": parent,
                "children": [],
            }
            existing.update(payload)
            nodes[node_id] = existing
        if parent is not None and parent in nodes and node_id not in nodes[parent]["children"]:
            nodes[parent]["children"].append(node_id)
        return existing

    add_node(
        project_root_id,
        parent=None,
        kind="project_root",
        layer="Project",
        title=project.metadata.display_name,
        file=project.product_spec_file,
    )
    add_node(framework_root_id, parent=project_root_id, kind="framework_root", layer="Framework", title="Framework")
    add_node(product_root_id, parent=project_root_id, kind="product_root", layer="Product Spec", title="Product Spec")
    add_node(
        implementation_root_id,
        parent=project_root_id,
        kind="implementation_root",
        layer="Implementation Config",
        title="Implementation Config",
    )
    add_node(code_root_id, parent=project_root_id, kind="code_root", layer="Code", title="Code")
    add_node(evidence_root_id, parent=project_root_id, kind="evidence_root", layer="Evidence", title="Evidence")

    framework_modules: dict[str, FrameworkModuleIR] = {}
    for item in snapshot["upstream_closure"]:
        layer = str(item["layer"])
        file_name = str(item["file"])
        ref_kind = str(item["ref_kind"])
        ref_id = str(item["ref_id"])
        digest = str(item["digest"])
        if layer == "framework":
            module = framework_modules.get(file_name)
            if module is None:
                module = parse_framework_module(REPO_ROOT / file_name)
                framework_modules[file_name] = module
            module_node_id = f"{framework_root_id}:module:{module.module_id}"
            add_node(
                module_node_id,
                parent=framework_root_id,
                kind="framework_module",
                layer="Framework",
                title=module.module_id,
                file=file_name,
            )
            rule_node_id = f"{module_node_id}:rule:{ref_id}"
            add_node(
                rule_node_id,
                parent=module_node_id,
                kind="framework_rule",
                layer="Framework",
                title=ref_id,
                file=file_name,
                ref_kind=ref_kind,
                ref_id=ref_id,
                digest=digest,
            )
            continue
        if layer == "product_spec":
            file_node_id = f"{product_root_id}:file:{file_name}"
            add_node(
                file_node_id,
                parent=product_root_id,
                kind="product_file",
                layer="Product Spec",
                title=Path(file_name).name,
                file=file_name,
            )
            section_node_id = f"{file_node_id}:section:{ref_id}"
            add_node(
                section_node_id,
                parent=file_node_id,
                kind="product_section",
                layer="Product Spec",
                title=ref_id,
                file=file_name,
                ref_kind=ref_kind,
                ref_id=ref_id,
                digest=digest,
            )
            continue
        if layer == "implementation_config":
            file_node_id = f"{implementation_root_id}:file:{file_name}"
            add_node(
                file_node_id,
                parent=implementation_root_id,
                kind="implementation_file",
                layer="Implementation Config",
                title=Path(file_name).name,
                file=file_name,
            )
            section_node_id = f"{file_node_id}:section:{ref_id}"
            add_node(
                section_node_id,
                parent=file_node_id,
                kind="implementation_section",
                layer="Implementation Config",
                title=ref_id,
                file=file_name,
                ref_kind=ref_kind,
                ref_id=ref_id,
                digest=digest,
            )

    for symbol in snapshot["symbols"]:
        symbol_id = str(symbol["symbol_id"])
        upstream_node_ids: list[str] = []
        for ref in symbol["upstream_refs"]:
            ref_layer = str(ref["layer"])
            ref_file = str(ref["file"])
            ref_id = str(ref["ref_id"])
            if ref_layer == "framework":
                module = framework_modules.get(ref_file)
                if module is None:
                    module = parse_framework_module(REPO_ROOT / ref_file)
                    framework_modules[ref_file] = module
                upstream_node_ids.append(f"{framework_root_id}:module:{module.module_id}:rule:{ref_id}")
            elif ref_layer == "product_spec":
                upstream_node_ids.append(f"{product_root_id}:file:{ref_file}:section:{ref_id}")
            elif ref_layer == "implementation_config":
                upstream_node_ids.append(f"{implementation_root_id}:file:{ref_file}:section:{ref_id}")
        primary_binding = symbol["bindings"][0] if symbol["bindings"] else {}
        add_node(
            f"{code_root_id}:symbol:{symbol_id}",
            parent=code_root_id,
            kind="code_symbol",
            layer="Code",
            title=symbol_id,
            symbol_id=symbol_id,
            owner=symbol["owner"],
            symbol_kind=symbol["kind"],
            risk=symbol["risk"],
            file=primary_binding.get("file"),
            locator=primary_binding.get("locator"),
            bindings=symbol["bindings"],
            derived_from=upstream_node_ids,
            validator="governed_symbol_compare",
            expected=symbol["expected"],
        )

    generated_paths = _expected_generated_artifact_paths(project)
    evidence_dependencies = {
        "framework_ir_json": [framework_root_id],
        "product_spec_json": [product_root_id],
        "implementation_bundle_py": [framework_root_id, product_root_id, implementation_root_id, code_root_id],
        "generation_manifest_json": [project_root_id],
        "governance_manifest_json": [framework_root_id, product_root_id, implementation_root_id, code_root_id],
        "governance_tree_json": [project_root_id],
    }
    for artifact_key, rel_path in generated_paths.items():
        add_node(
            f"{evidence_root_id}:artifact:{artifact_key}",
            parent=evidence_root_id,
            kind="evidence_artifact",
            layer="Evidence",
            title=artifact_key,
            artifact=artifact_key,
            file=rel_path,
            derived_from=evidence_dependencies.get(artifact_key, [project_root_id]),
        )

    return {
        "tree_version": GOVERNANCE_TREE_VERSION,
        "project_id": project.metadata.project_id,
        "generator_version": GOVERNANCE_GENERATOR_VERSION,
        "root_node_id": project_root_id,
        "upstream_closure": snapshot["upstream_closure"],
        "nodes": [nodes[node_id] for node_id in sorted(nodes)],
    }


def digest_upstream_ref(ref: UpstreamRef) -> str:
    file_path = REPO_ROOT / ref.file
    if ref.layer == "framework":
        module = parse_framework_module(file_path)
        return _fingerprint(_framework_ref_payload(module, ref))
    if ref.layer in {"product_spec", "implementation_config"}:
        with file_path.open("rb") as fh:
            data = tomllib.load(fh)
        value = _resolve_section(data, ref.ref_id)
        return _fingerprint(value)
    raise ValueError(f"unsupported governance upstream layer: {ref.layer}")


def _framework_ref_payload(module: FrameworkModuleIR, ref: UpstreamRef) -> dict[str, Any]:
    if ref.ref_kind == "rule":
        for rule in module.rules:
            if rule.rule_id == ref.ref_id:
                return rule.to_dict()
        raise KeyError(f"missing framework rule ref {ref.ref_id} in {module.path}")
    raise ValueError(f"unsupported framework ref kind: {ref.ref_kind}")


def _resolve_section(data: dict[str, Any], section_path: str) -> Any:
    current: Any = data
    for part in section_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"missing section path: {section_path}")
        current = current[part]
    return current


def parse_governance_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("governance manifest must decode into object")
    if payload.get("manifest_version") != GOVERNANCE_MANIFEST_VERSION:
        raise ValueError(
            f"unsupported governance manifest version: {payload.get('manifest_version')}"
        )
    if not isinstance(payload.get("symbols"), list):
        raise ValueError("governance manifest missing symbols list")
    if not isinstance(payload.get("upstream_closure"), list):
        raise ValueError("governance manifest missing upstream_closure list")
    return payload


def parse_governance_tree(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("governance tree must decode into object")
    if payload.get("tree_version") != GOVERNANCE_TREE_VERSION:
        raise ValueError(f"unsupported governance tree version: {payload.get('tree_version')}")
    if not isinstance(payload.get("root_node_id"), str) or not payload.get("root_node_id"):
        raise ValueError("governance tree missing root_node_id")
    if not isinstance(payload.get("nodes"), list):
        raise ValueError("governance tree missing nodes list")
    if not isinstance(payload.get("upstream_closure"), list):
        raise ValueError("governance tree missing upstream_closure list")
    return payload


def validate_manifest_closure(payload: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in payload.get("upstream_closure", []):
        if not isinstance(item, dict):
            continue
        try:
            ref = UpstreamRef(
                layer=str(item["layer"]),
                file=str(item["file"]),
                ref_kind=str(item["ref_kind"]),
                ref_id=str(item["ref_id"]),
            )
        except KeyError as exc:
            issues.append(
                {
                    "code": "STALE_EVIDENCE",
                    "message": f"governance manifest closure entry is invalid: missing {exc}",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        actual_digest = digest_upstream_ref(ref)
        if actual_digest == item.get("digest"):
            continue
        issues.append(
            {
                "code": "STALE_EVIDENCE",
                "message": (
                    "governance manifest is stale; expected evidence no longer matches current upstream closure"
                ),
                "file": ref.file,
                "line": 1,
                "ref": ref.to_manifest_dict(),
            }
        )
    return issues


def _tree_node_index(payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    node_index: dict[str, dict[str, Any]] = {}
    for entry in payload.get("nodes", []):
        if not isinstance(entry, dict):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": "governance tree node entry must be an object",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        node_id = str(entry.get("node_id") or "").strip()
        if not node_id:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": "governance tree node entry is missing node_id",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        if node_id in node_index:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"duplicate governance tree node entry: {node_id}",
                    "file": "",
                    "line": 1,
                    "node_id": node_id,
                }
            )
            continue
        node_index[node_id] = entry
    return node_index, issues


def validate_tree_closure(payload: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    node_index, node_issues = _tree_node_index(payload)
    issues.extend(node_issues)
    root_node_id = str(payload.get("root_node_id") or "").strip()
    if not root_node_id:
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": "governance tree is missing root_node_id",
                "file": "",
                "line": 1,
            }
        )
    elif root_node_id not in node_index:
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": f"governance tree root node does not exist: {root_node_id}",
                "file": "",
                "line": 1,
                "node_id": root_node_id,
            }
        )
    else:
        if node_index[root_node_id].get("parent") is not None:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": "governance tree root node must not have a parent",
                    "file": "",
                    "line": 1,
                    "node_id": root_node_id,
                }
            )
    for node_id, node in node_index.items():
        children = node.get("children")
        if not isinstance(children, list):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree node must define children list: {node_id}",
                    "file": "",
                    "line": 1,
                    "node_id": node_id,
                }
            )
            children = []
        parent = node.get("parent")
        if parent is not None and parent not in node_index:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree node references missing parent: {node_id} -> {parent}",
                    "file": "",
                    "line": 1,
                    "node_id": node_id,
                }
            )
        for child_id in children:
            if child_id not in node_index:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"governance tree node references missing child: {node_id} -> {child_id}",
                        "file": "",
                        "line": 1,
                        "node_id": node_id,
                    }
                )
                continue
            if node_index[child_id].get("parent") != node_id:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": (
                            f"governance tree parent/child relationship is inconsistent: "
                            f"{node_id} -> {child_id}"
                        ),
                        "file": "",
                        "line": 1,
                        "node_id": node_id,
                    }
                )
    issues.extend(validate_manifest_closure(payload))
    return issues


def compare_project_to_manifest(project: KnowledgeBaseProject, payload: dict[str, Any]) -> list[dict[str, Any]]:
    definition_items = _definitions(project)
    definitions = {item.symbol_id: item for item in definition_items}
    binding_index = collect_governed_bindings(governed_files_for_project(project))
    issues: list[dict[str, Any]] = []
    issues.extend(_binding_validation_issues(binding_index, definition_items))

    manifest_symbols: dict[str, dict[str, Any]] = {}
    for symbol in payload.get("symbols", []):
        if not isinstance(symbol, dict):
            issues.append(
                {
                    "code": "GOVERNANCE_MANIFEST_INVALID",
                    "message": "governance manifest symbol entry must be an object",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        symbol_id = str(symbol.get("symbol_id") or "").strip()
        if not symbol_id:
            issues.append(
                {
                    "code": "GOVERNANCE_MANIFEST_INVALID",
                    "message": "governance manifest symbol entry is missing symbol_id",
                    "file": "",
                    "line": 1,
                }
            )
            continue
        if symbol_id in manifest_symbols:
            issues.append(
                {
                    "code": "GOVERNANCE_MANIFEST_INVALID",
                    "message": f"duplicate governance manifest symbol entry: {symbol_id}",
                    "file": "",
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
            continue
        manifest_symbols[symbol_id] = symbol

    for symbol_id in sorted(set(manifest_symbols) - set(definitions)):
        issues.append(
            {
                "code": "GOVERNANCE_MANIFEST_INVALID",
                "message": f"unknown governance symbol in manifest: {symbol_id}",
                "file": "",
                "line": 1,
                "symbol_id": symbol_id,
            }
        )

    for symbol_id, definition in definitions.items():
        symbol = manifest_symbols.get(symbol_id)
        if symbol is None:
            issues.append(
                {
                    "code": "GOVERNANCE_MANIFEST_INVALID",
                    "message": f"governance manifest is missing symbol entry: {symbol_id}",
                    "file": "",
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
            continue
        for rel_file, locator in definition.required_bindings:
            if not _binding_exists(binding_index, symbol_id, rel_file, locator):
                issues.append(
                    {
                        "code": "MISSING_BINDING",
                        "message": f"required governed binding is missing for {symbol_id}: {rel_file} -> {locator}",
                        "file": rel_file,
                        "line": 1,
                    }
                )
        actual_evidence = definition.actual_extractor(project)
        actual_fingerprint = _fingerprint(actual_evidence)
        expected = symbol.get("expected", {})
        if expected.get("fingerprint") == actual_fingerprint:
            continue
        issues.append(
            {
                "code": "EXPECTATION_MISMATCH",
                "message": f"governed symbol no longer matches derived expectation: {symbol_id}",
                "file": definition.required_bindings[0][0],
                "line": 1,
                "symbol_id": symbol_id,
                "owner": definition.owner,
                "kind": definition.kind,
                "expected": expected.get("evidence"),
                "actual": actual_evidence,
            }
        )
    for item in find_unbound_high_risk_structures():
        issues.append(
            {
                "code": "MISSING_BINDING",
                "message": item["message"],
                "file": item["file"],
                "line": item["line"],
                "locator": item["locator"],
            }
        )
    return issues


def compare_project_to_tree(project: KnowledgeBaseProject, payload: dict[str, Any]) -> list[dict[str, Any]]:
    definition_items = _definitions(project)
    definitions = {item.symbol_id: item for item in definition_items}
    binding_index = collect_governed_bindings(governed_files_for_project(project))
    issues: list[dict[str, Any]] = []
    issues.extend(_binding_validation_issues(binding_index, definition_items))

    node_index, node_issues = _tree_node_index(payload)
    issues.extend(node_issues)
    code_symbol_nodes: dict[str, dict[str, Any]] = {}
    evidence_artifact_nodes: dict[str, dict[str, Any]] = {}

    for node in node_index.values():
        kind = str(node.get("kind") or "").strip()
        if kind == "code_symbol":
            symbol_id = str(node.get("symbol_id") or "").strip()
            if not symbol_id:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": "governance tree code symbol node is missing symbol_id",
                        "file": "",
                        "line": 1,
                        "node_id": node["node_id"],
                    }
                )
                continue
            if symbol_id in code_symbol_nodes:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"duplicate governance tree code symbol node: {symbol_id}",
                        "file": "",
                        "line": 1,
                        "symbol_id": symbol_id,
                    }
                )
                continue
            code_symbol_nodes[symbol_id] = node
            continue
        if kind == "evidence_artifact":
            artifact = str(node.get("artifact") or "").strip()
            if not artifact:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": "governance tree evidence artifact node is missing artifact",
                        "file": "",
                        "line": 1,
                        "node_id": node["node_id"],
                    }
                )
                continue
            if artifact in evidence_artifact_nodes:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"duplicate governance tree evidence artifact node: {artifact}",
                        "file": "",
                        "line": 1,
                        "artifact": artifact,
                    }
                )
                continue
            evidence_artifact_nodes[artifact] = node

    expected_artifacts = _expected_generated_artifact_paths(project)
    for artifact_key, rel_path in expected_artifacts.items():
        artifact_node: dict[str, Any] | None = evidence_artifact_nodes.get(artifact_key)
        if artifact_node is None:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree is missing evidence artifact node: {artifact_key}",
                    "file": "",
                    "line": 1,
                    "artifact": artifact_key,
                }
            )
            continue
        if artifact_node.get("file") != rel_path:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": (
                        f"governance tree evidence artifact path drifted for {artifact_key}: "
                        f"expected {rel_path}"
                    ),
                    "file": "",
                    "line": 1,
                    "artifact": artifact_key,
                }
            )
    for artifact_key in sorted(set(evidence_artifact_nodes) - set(expected_artifacts)):
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": f"unknown evidence artifact node in governance tree: {artifact_key}",
                "file": "",
                "line": 1,
                "artifact": artifact_key,
            }
        )

    for symbol_id in sorted(set(code_symbol_nodes) - set(definitions)):
        issues.append(
            {
                "code": "GOVERNANCE_TREE_INVALID",
                "message": f"unknown code symbol in governance tree: {symbol_id}",
                "file": "",
                "line": 1,
                "symbol_id": symbol_id,
            }
        )

    for symbol_id, definition in definitions.items():
        symbol_node: dict[str, Any] | None = code_symbol_nodes.get(symbol_id)
        if symbol_node is None:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree is missing code symbol node: {symbol_id}",
                    "file": "",
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
            continue
        if (
            symbol_node.get("owner") != definition.owner
            or symbol_node.get("symbol_kind") != definition.kind
            or symbol_node.get("kind") != "code_symbol"
        ):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree metadata mismatch for code symbol: {symbol_id}",
                    "file": str(symbol_node.get("file") or ""),
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
        if symbol_node.get("risk") != definition.risk:
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree risk metadata mismatch for code symbol: {symbol_id}",
                    "file": str(symbol_node.get("file") or ""),
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
        tree_bindings = symbol_node.get("bindings")
        if not isinstance(tree_bindings, list):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree code symbol bindings must be a list: {symbol_id}",
                    "file": str(symbol_node.get("file") or ""),
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
        else:
            expected_binding_set = {
                (item.file, item.locator)
                for item in binding_index.get(symbol_id, [])
            }
            actual_binding_set = {
                (str(item.get("file") or ""), str(item.get("locator") or ""))
                for item in tree_bindings
                if isinstance(item, dict)
            }
            if expected_binding_set != actual_binding_set:
                issues.append(
                    {
                        "code": "GOVERNANCE_TREE_INVALID",
                        "message": f"governance tree binding set drifted for {symbol_id}",
                        "file": str(symbol_node.get("file") or ""),
                        "line": 1,
                        "symbol_id": symbol_id,
                        "expected": sorted(expected_binding_set),
                        "actual": sorted(actual_binding_set),
                    }
                )
        for rel_file, locator in definition.required_bindings:
            if not _binding_exists(binding_index, symbol_id, rel_file, locator):
                issues.append(
                    {
                        "code": "MISSING_BINDING",
                        "message": f"required governed binding is missing for {symbol_id}: {rel_file} -> {locator}",
                        "file": rel_file,
                        "line": 1,
                    }
                )
        actual_evidence = definition.actual_extractor(project)
        actual_fingerprint = _fingerprint(actual_evidence)
        expected = symbol_node.get("expected", {})
        if not isinstance(expected, dict):
            issues.append(
                {
                    "code": "GOVERNANCE_TREE_INVALID",
                    "message": f"governance tree code symbol expected payload must be an object: {symbol_id}",
                    "file": str(symbol_node.get("file") or ""),
                    "line": 1,
                    "symbol_id": symbol_id,
                }
            )
            continue
        if expected.get("fingerprint") == actual_fingerprint:
            continue
        issues.append(
            {
                "code": "EXPECTATION_MISMATCH",
                "message": f"governed symbol no longer matches derived expectation: {symbol_id}",
                "file": definition.required_bindings[0][0],
                "line": 1,
                "symbol_id": symbol_id,
                "owner": definition.owner,
                "kind": definition.kind,
                "expected": expected.get("evidence"),
                "actual": actual_evidence,
            }
        )
    for item in find_unbound_high_risk_structures():
        issues.append(
            {
                "code": "MISSING_BINDING",
                "message": item["message"],
                "file": item["file"],
                "line": item["line"],
                "locator": item["locator"],
            }
        )
    return issues


def _binding_exists(
    binding_index: dict[str, list[GovernedBinding]],
    symbol_id: str,
    rel_file: str,
    locator: str,
) -> bool:
    for item in binding_index.get(symbol_id, []):
        if item.file == rel_file and item.locator == locator:
            return True
    return False

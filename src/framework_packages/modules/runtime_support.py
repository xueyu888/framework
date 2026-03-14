from __future__ import annotations

from typing import Any

from framework_packages.contract import PackageCompileInput
from knowledge_base_runtime.runtime_profile import KnowledgeBaseRuntimeProfile, load_knowledge_base_runtime_profile
from project_runtime.documents import export_documents
from project_runtime.models import RouteConfig, SeedDocumentSource, UiSpecPaths


def compose_frontend_action_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    route = _route(payload)
    copy_titles = {
        "chat_title": _config_value(payload, "truth.surface.copy.chat_title"),
        "preview_title": _config_value(payload, "truth.surface.copy.preview_title"),
        "library_title": _config_value(payload, "truth.surface.copy.library_title"),
    }
    allow_create = bool(_config_value(payload, "truth.library.allow_create"))
    allow_delete = bool(_config_value(payload, "truth.library.allow_delete"))
    return {
        "preset": _config_value(payload, "selection.preset"),
        "surface_regions": [
            {"region_id": region_id, "title": title, "boundary": "SURFACE"}
            for region_id, title in (
                ("conversation_sidebar", "Conversation Sidebar"),
                ("chat_main", copy_titles["chat_title"]),
                ("citation_drawer", copy_titles["preview_title"]),
                ("knowledge_pages", copy_titles["library_title"]),
            )
        ],
        "interaction_actions": list(
            contract.frontend_interaction_actions(
                allow_create=allow_create,
                allow_delete=allow_delete,
            )
        ),
        "state_channels": list(contract.resolve_state_channels(sticky_document=_sticky_document(payload))),
        "extend_slots": [
            {"slot_id": "domain_workbench", "module_id": payload.root_module_id("knowledge_base")},
            {"slot_id": "backend_contract", "module_id": payload.root_module_id("backend")},
        ],
        "route_contract": dict(route.to_dict()),
        "a11y": _a11y(payload),
    }


def compose_frontend_surface_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    surface = _surface(payload)
    visual = _visual(payload)
    visual_tokens = _visual_tokens(
        contract=contract,
        surface=surface,
        visual=visual,
        preview_variant=str(_config_value(payload, "truth.preview.preview_variant")),
    )
    return {
        "contract_surface": {
            "shell": surface["shell"],
            "layout_variant": surface["layout_variant"],
            "surface_config": {
                "sidebar_width": surface["sidebar_width"],
                "preview_mode": surface["preview_mode"],
                "density": surface["density"],
            },
            "visual_config": dict(visual),
            "surface_composition": {
                "sidebar": list(contract.surface_composition_sidebar),
                "main": list(contract.surface_composition_main),
                "overlay": list(contract.surface_composition_overlay),
                "secondary_pages": list(contract.secondary_pages),
            },
        },
        "ui_shell": {
            "id": surface["shell"],
            "layout_variant": surface["layout_variant"],
            "regions": list(contract.shell_regions),
            "secondary_pages": list(contract.secondary_pages),
            "default_page": "chat_home",
            "preview_mode": surface["preview_mode"],
            "density": surface["density"],
        },
        "ui_visual": {
            "theme": dict(visual),
            "tokens": visual_tokens,
        },
        "components": {
            "conversation_sidebar": {
                "title": "历史会话",
                "actions": ["start_new_chat", "select_session", "open_knowledge_switch"],
                "new_chat_label": "新建聊天",
                "browse_knowledge_label": "浏览知识库与文档",
                "basketball_showcase_label": _config_value(payload, "truth.showcase_page.title"),
                "knowledge_entry_label": f"知识库 · {_config_value(payload, 'truth.library.knowledge_base_name')}",
            }
        },
        "copy": {
            "hero_kicker": surface["copy"]["hero_kicker"],
            "hero_title": surface["copy"]["hero_title"],
            "hero_copy": surface["copy"]["hero_copy"],
        },
    }


def compose_frontend_navigation_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    surface = {
        "copy": {
            "hero_title": _config_value(payload, "truth.surface.copy.hero_title"),
            "library_title": _config_value(payload, "truth.surface.copy.library_title"),
        }
    }
    route = _route(payload)
    showcase_page = _showcase_page(payload)
    paths = UiSpecPaths.from_route(route)
    return {
        "pages": _ui_pages(
            surface=surface,
            route=route,
            showcase_page=showcase_page,
            paths=paths,
            contract=contract,
        ),
        "components": {
            "aux_sidebar": {
                "nav": {
                    "chat": "返回聊天",
                    "basketball_showcase": showcase_page["title"],
                    "knowledge_list": "知识库列表",
                    "knowledge_detail": "当前知识库详情",
                },
                "note": "辅助页面负责知识库浏览、来源验证与文档追溯，不抢占聊天主舞台。",
            },
            "knowledge_switch_dialog": {
                "title": "切换知识库",
                "description": "默认保持 ChatGPT 风格聊天界面，知识库切换只在需要时展开。",
                "close_aria_label": "Close knowledge dialog",
                "select_action_label": "使用此知识库",
                "detail_action_label": "查看详情",
                "card_actions": ["select", "open_knowledge_detail"],
            },
        },
    }


def compose_frontend_conversation_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    showcase_title = _config_value(payload, "truth.showcase_page.title")
    chat = _chat(payload)
    return {
        "implementation": _frontend_refinement(payload),
        "components": {
            "chat_header": {
                "title_source": "conversation.title",
                "subtitle_template": "知识库 · {knowledge_base_name}",
                "knowledge_badge_template": "基于：{knowledge_base_name}",
                "knowledge_entry_link_label": "知识库入口",
                "showcase_link_label": showcase_title,
            },
            "message_stream": {
                "roles": ["user", "assistant"],
                "role_labels": {"user": "You", "assistant": "Assistant"},
                "assistant_actions": ["copy_answer"],
                "copy_action_label": "复制回答",
                "copy_failure_message": "复制失败，请手动复制。",
                "loading_label": "正在检索知识库并整理回答…",
                "summary_template": "参考了 {count} 个来源",
                "citation_style": chat["citation_style"],
            },
            "chat_composer": {
                "placeholder": chat["placeholder"],
                "submit_label": "发送",
                "context_template": "当前上下文：{context_label}",
                "citation_hint": "引用默认轻量展示，点击后打开来源抽屉",
                "mode_label": "知识问答",
                "knowledge_link_label": "查看知识库",
                "showcase_link_label": showcase_title,
            },
        },
        "conversation": {
            "default_title": "新建聊天",
            "relative_groups": {
                "today": "今天",
                "last_7_days": "7 天内",
                "last_30_days": "30 天内",
                "older": "更早",
            },
            "welcome_kicker": _config_value(payload, "truth.surface.copy.chat_title"),
            "welcome_title": "今天想了解什么？",
            "welcome_copy": chat["welcome"],
            "welcome_prompts": list(chat["welcome_prompts"]),
            "current_knowledge_base_template": "当前知识库：{knowledge_base_name}",
        },
    }


def compose_frontend_feedback_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    citation_style = _config_value(payload, "truth.chat.citation_style")
    bubble_variant = _config_value(payload, "truth.chat.bubble_variant")
    composer_variant = _config_value(payload, "truth.chat.composer_variant")
    return_config = _return_config(payload)
    return {
        "component_variants": {
            "conversation_list": _config_value(payload, "truth.library.list_variant"),
            "preview_surface": _config_value(payload, "truth.preview.preview_variant"),
            "chat_bubble": bubble_variant,
            "chat_composer": composer_variant,
            "citation_summary": return_config["citation_card_variant"],
        },
        "components": {
            "citation_drawer": {
                "title": _config_value(payload, "truth.surface.copy.preview_title"),
                "close_aria_label": "Close citation drawer",
                "tab_variant": "numbered",
                "sections": list(contract.drawer_sections),
                "section_label": "章节",
                "snippet_title": "命中片段",
                "source_context_title": "来源上下文",
                "empty_context_text": "暂无来源上下文。",
                "load_failure_text": "无法加载来源片段。",
                "document_link_label": "打开文档详情",
                "return_targets": list(return_config["targets"]),
            }
        },
        "citation": {
            "style": citation_style,
            "summary_variant": return_config["citation_card_variant"],
            "drawer_sections": list(contract.drawer_sections),
        },
    }


def assemble_frontend_app_spec(payload: PackageCompileInput) -> dict[str, Any]:
    action_fragment = _require_child_runtime_export(payload, "frontend.L1.M0", "frontend_action_fragment")
    surface_fragment = _require_child_runtime_export(payload, "frontend.L1.M2", "frontend_surface_fragment")
    navigation_fragment = _require_child_runtime_export(payload, "frontend.L1.M3", "frontend_navigation_fragment")
    conversation_fragment = _require_child_runtime_export(payload, "frontend.L1.M1", "frontend_conversation_fragment")
    feedback_fragment = _require_child_runtime_export(payload, "frontend.L1.M4", "frontend_feedback_fragment")
    roots = _selected_roots(payload)
    return {
        "contract": {
            "module_id": payload.framework_module.module_id,
            "preset": action_fragment["preset"],
            "shell": surface_fragment["contract_surface"]["shell"],
            "layout_variant": surface_fragment["contract_surface"]["layout_variant"],
            "surface_config": dict(surface_fragment["contract_surface"]["surface_config"]),
            "visual_config": dict(surface_fragment["contract_surface"]["visual_config"]),
            "surface_composition": dict(surface_fragment["contract_surface"]["surface_composition"]),
            "surface_regions": list(action_fragment["surface_regions"]),
            "interaction_actions": list(action_fragment["interaction_actions"]),
            "state_channels": list(action_fragment["state_channels"]),
            "extend_slots": list(action_fragment["extend_slots"]),
            "route_contract": dict(action_fragment["route_contract"]),
            "a11y": dict(action_fragment["a11y"]),
            "component_variants": dict(feedback_fragment["component_variants"]),
            "base_ids": [item.base_id for item in payload.framework_module.bases],
            "rule_ids": [item.rule_id for item in payload.framework_module.rules],
        },
        "ui": {
            "derived_from": {
                "framework_modules": {
                    "frontend": roots["frontend"]["module_id"],
                    "knowledge_base": roots["knowledge_base"]["module_id"],
                },
                "selection": _selection_payload_from_preset(payload, preset=str(action_fragment["preset"])),
                "registry_binding": {
                    roots["frontend"]["module_id"]: roots["frontend"]["entry_class_name"],
                    roots["knowledge_base"]["module_id"]: roots["knowledge_base"]["entry_class_name"],
                },
                "child_runtime_modules": sorted(payload.child_runtime_exports),
            },
            "implementation": dict(conversation_fragment["implementation"]),
            "shell": dict(surface_fragment["ui_shell"]),
            "visual": dict(surface_fragment["ui_visual"]),
            "pages": dict(navigation_fragment["pages"]),
            "components": {
                **surface_fragment["components"],
                **navigation_fragment["components"],
                **conversation_fragment["components"],
                **feedback_fragment["components"],
            },
            "conversation": dict(conversation_fragment["conversation"]),
            "citation": {
                **feedback_fragment["citation"],
                "document_detail_path": navigation_fragment["pages"]["document_detail"]["path"],
            },
        },
        "copy": dict(surface_fragment["copy"]),
    }


def assemble_runtime_page_blueprint(frontend_spec: dict[str, Any]) -> dict[str, Any]:
    ui = frontend_spec.get("ui")
    if not isinstance(ui, dict):
        raise ValueError("frontend_app_spec.ui must be a dict")
    pages = ui.get("pages")
    if not isinstance(pages, dict):
        raise ValueError("frontend_app_spec.ui.pages must be a dict")
    return {
        "landing_path": _require_page_path(pages, "chat_home"),
        "page_routes": [
            {
                "route_id": "chat_home",
                "path": _require_page_path(pages, "chat_home"),
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_knowledge_base_page_handler",
            },
            {
                "route_id": "basketball_showcase",
                "path": _require_page_path(pages, "basketball_showcase"),
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_basketball_showcase_page_handler",
            },
            {
                "route_id": "knowledge_list",
                "path": _require_page_path(pages, "knowledge_list"),
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_knowledge_base_list_page_handler",
            },
            {
                "route_id": "knowledge_detail",
                "path": _require_page_path(pages, "knowledge_detail"),
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_knowledge_base_detail_page_handler",
            },
            {
                "route_id": "document_detail",
                "path": _require_page_path(pages, "document_detail"),
                "response_class": "html",
                "handler_factory": "knowledge_base_runtime.frontend:build_document_detail_page_handler",
            },
        ],
    }


def compose_knowledge_base_surface_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    surface = _workbench_surface(payload)
    library = _library(payload)
    preview = _preview(payload)
    chat = _chat(payload)
    return_config = _return_config(payload)
    documents = tuple(
        SeedDocumentSource.from_dict(item)
        for item in _config_value(payload, "truth.documents")
        if isinstance(item, dict)
    )
    return {
        "workbench": {
            "layout_variant": surface["layout_variant"],
            "regions": list(contract.workbench_region_ids),
            "surface": {
                "sidebar_width": surface["sidebar_width"],
                "preview_mode": surface["preview_mode"],
                "density": surface["density"],
            },
            "library": {
                **library,
                "actions": list(
                    contract.workbench_library_actions(
                        allow_create=library["allow_create"],
                        allow_delete=library["allow_delete"],
                    )
                ),
            },
            "preview": preview,
            "chat": chat,
            "return": return_config,
            "knowledge_bases": [
                {
                    "knowledge_base_id": library["knowledge_base_id"],
                    "name": library["knowledge_base_name"],
                    "description": library["knowledge_base_description"],
                    "document_count": len(documents),
                }
            ],
        }
    }


def compose_knowledge_base_context_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    documents = tuple(
        SeedDocumentSource.from_dict(item)
        for item in _config_value(payload, "truth.documents")
        if isinstance(item, dict)
    )
    compiled_documents = export_documents(documents)
    context = _context(payload)
    return_config = _return_config(payload)
    return {
        "workbench": {
            "context": context,
            "flow": list(contract.workbench_flow_dicts()),
            "citation_return": {
                "query_keys": list(contract.workbench_citation_query_keys),
                "targets": list(return_config["targets"]),
                "anchor_restore": return_config["anchor_restore"],
            },
            "documents": [
                {
                    "document_id": item["document_id"],
                    "title": item["title"],
                    "section_ids": [
                        section["section_id"]
                        for section in item.get("sections", [])
                        if isinstance(section, dict)
                    ],
                    "section_count": len(item.get("sections", [])),
                }
                for item in compiled_documents
            ],
        },
        "documents": compiled_documents,
    }


def assemble_knowledge_base_domain_spec(payload: PackageCompileInput) -> dict[str, Any]:
    surface_fragment = _require_child_runtime_export(payload, "knowledge_base.L1.M0", "knowledge_base_surface_fragment")
    context_fragment = _require_child_runtime_export(payload, "knowledge_base.L1.M1", "knowledge_base_context_fragment")
    workbench = {
        **surface_fragment["workbench"],
        **context_fragment["workbench"],
        "module_id": payload.framework_module.module_id,
        "base_ids": [item.base_id for item in payload.framework_module.bases],
        "rule_ids": [item.rule_id for item in payload.framework_module.rules],
    }
    return {
        "workbench": workbench,
        "documents": list(context_fragment["documents"]),
    }


def assemble_runtime_documents(payload: PackageCompileInput) -> list[dict[str, Any]]:
    context_fragment = _require_child_runtime_export(payload, "knowledge_base.L1.M1", "knowledge_base_context_fragment")
    documents = context_fragment.get("documents")
    if not isinstance(documents, list):
        raise ValueError("knowledge_base_context_fragment.documents must be a list")
    return [dict(item) for item in documents if isinstance(item, dict)]


def compose_backend_service_fragment(payload: PackageCompileInput) -> dict[str, Any]:
    contract = load_knowledge_base_runtime_profile()
    selection = _selection_payload(payload)
    roots = _selected_roots(payload)
    route = _route(payload)
    library = _backend_library(payload)
    chat = _backend_chat(payload)
    context = _context(payload)
    return_config = _backend_return(payload)
    backend = _backend_refinement(payload)
    evidence = _evidence_refinement(payload)
    paths = UiSpecPaths.from_route(route)
    return {
        "derived_from": {
            "framework_modules": {
                "knowledge_base": roots["knowledge_base"]["module_id"],
                "backend": roots["backend"]["module_id"],
            },
            "selection": selection,
            "registry_binding": {
                roots["knowledge_base"]["module_id"]: roots["knowledge_base"]["entry_class_name"],
                roots["backend"]["module_id"]: roots["backend"]["entry_class_name"],
            },
        },
        "implementation": {
            "backend_renderer": backend["renderer"],
        },
        "knowledge_base": {
            "knowledge_base_id": library["knowledge_base_id"],
            "knowledge_base_name": library["knowledge_base_name"],
            "knowledge_base_description": library["knowledge_base_description"],
            "source_types": list(library["source_types"]),
            "metadata_fields": list(library["metadata_fields"]),
        },
        "transport": {
            "mode": backend["transport"],
            "api_prefix": route.api_prefix,
            "project_config_endpoint": evidence["project_config_endpoint"],
        },
        "retrieval": {
            "strategy": backend["retrieval_strategy"],
            "query_token_min_length": 3,
            "focus_section_bonus": 4,
            "token_match_bonus": 3,
            "max_preview_sections": context["max_preview_sections"],
            "max_citations": context["max_citations"],
            "selection_mode": context["selection_mode"],
        },
        "interaction_flow": list(contract.workbench_flow_dicts()),
        "answer_policy": {
            "citation_style": chat["citation_style"],
            "no_match_text": (
                "当前知识库里没有找到足够相关的证据。你可以换一种问法，或者先浏览知识库与文档详情页确认可用来源。"
            ),
            "lead_template": "根据当前知识库，最相关的证据来自《{document_title}》的“{section_title}”。[{citation_index}]",
            "lead_snippet_template": "该片段指出：{snippet}",
            "followup_template": "补充来源还包括《{document_title}》的“{section_title}”。[{citation_index}] {snippet}",
            "closing_text": "点击文中引用可打开来源抽屉，并继续进入文档详情页查看完整上下文。",
        },
        "interaction_copy": {
            "loading_text": "正在检索知识库并整理回答…",
            "error_text": "回答生成失败。你可以重新提问，或稍后再试。",
        },
        "return_policy": {
            "targets": list(return_config["targets"]),
            "anchor_restore": return_config["anchor_restore"],
            "chat_path": route.workbench,
            "knowledge_base_detail_path": paths.knowledge_base_detail_path,
            "document_detail_path": paths.document_detail_path,
        },
        "write_policy": {
            "allow_create": library["allow_create"],
            "allow_delete": library["allow_delete"],
        },
    }


def assemble_backend_service_spec(payload: PackageCompileInput) -> dict[str, Any]:
    spec = _require_child_runtime_export(payload, "backend.L1.M0", "backend_service_fragment")
    spec["module_id"] = payload.framework_module.module_id
    spec["base_ids"] = [item.base_id for item in payload.framework_module.bases]
    spec["rule_ids"] = [item.rule_id for item in payload.framework_module.rules]
    spec["derived_from"]["child_runtime_modules"] = sorted(payload.child_runtime_exports)
    return spec


def assemble_runtime_api_blueprint(service_spec: dict[str, Any]) -> dict[str, Any]:
    transport = service_spec.get("transport")
    if not isinstance(transport, dict):
        raise ValueError("backend_service_spec.transport must be a dict")
    mode = transport.get("mode")
    project_config_endpoint = transport.get("project_config_endpoint")
    if not isinstance(mode, str):
        raise ValueError("backend_service_spec.transport.mode must be a string")
    if not isinstance(project_config_endpoint, str):
        raise ValueError("backend_service_spec.transport.project_config_endpoint must be a string")
    return {
        "transport": {
            "mode": mode,
            "project_config_endpoint": project_config_endpoint,
        },
        "summary_factory": "knowledge_base_runtime.runtime_exports:project_runtime_public_summary",
        "repository_factory": "knowledge_base_runtime.backend:build_runtime_repository",
        "api_router_factory": "knowledge_base_runtime.backend:build_knowledge_base_router",
    }


def _require_child_runtime_export(
    payload: PackageCompileInput,
    module_id: str,
    export_key: str,
) -> dict[str, Any]:
    module_exports = payload.child_runtime_exports.get(module_id)
    if module_exports is None:
        raise KeyError(f"missing child runtime exports for module: {module_id}")
    value = module_exports.get(export_key)
    if not isinstance(value, dict):
        raise ValueError(f"missing dict runtime export {export_key} from module: {module_id}")
    return dict(value)


def _config_value(payload: PackageCompileInput, path: str) -> Any:
    if path not in payload.config_slice:
        raise KeyError(path)
    return payload.config_slice[path]


def _selected_roots(payload: PackageCompileInput) -> dict[str, dict[str, str]]:
    return {item.role: item.to_dict() for item in payload.selected_roots}


def _selection_payload(payload: PackageCompileInput) -> dict[str, Any]:
    return _selection_payload_from_preset(payload, preset=_config_value(payload, "selection.preset"))


def _selection_payload_from_preset(payload: PackageCompileInput, *, preset: str) -> dict[str, Any]:
    roots = [item.to_dict() for item in payload.selected_roots]
    return {
        "preset": preset,
        "roots": roots,
        "root_modules": {item["role"]: item["framework_file"] for item in roots},
    }


def _surface(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "shell": _config_value(payload, "truth.surface.shell"),
        "layout_variant": _config_value(payload, "truth.surface.layout_variant"),
        "sidebar_width": _config_value(payload, "truth.surface.sidebar_width"),
        "preview_mode": _config_value(payload, "truth.surface.preview_mode"),
        "density": _config_value(payload, "truth.surface.density"),
        "copy": {
            "hero_kicker": _config_value(payload, "truth.surface.copy.hero_kicker"),
            "hero_title": _config_value(payload, "truth.surface.copy.hero_title"),
            "hero_copy": _config_value(payload, "truth.surface.copy.hero_copy"),
            "library_title": _config_value(payload, "truth.surface.copy.library_title"),
            "preview_title": _config_value(payload, "truth.surface.copy.preview_title"),
            "toc_title": _config_value(payload, "truth.surface.copy.toc_title"),
            "chat_title": _config_value(payload, "truth.surface.copy.chat_title"),
            "empty_state_title": _config_value(payload, "truth.surface.copy.empty_state_title"),
            "empty_state_copy": _config_value(payload, "truth.surface.copy.empty_state_copy"),
        },
    }


def _workbench_surface(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "layout_variant": _config_value(payload, "truth.surface.layout_variant"),
        "sidebar_width": _config_value(payload, "truth.surface.sidebar_width"),
        "preview_mode": _config_value(payload, "truth.surface.preview_mode"),
        "density": _config_value(payload, "truth.surface.density"),
    }


def _visual(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "brand": _config_value(payload, "truth.visual.brand"),
        "accent": _config_value(payload, "truth.visual.accent"),
        "surface_preset": _config_value(payload, "truth.visual.surface_preset"),
        "radius_scale": _config_value(payload, "truth.visual.radius_scale"),
        "shadow_level": _config_value(payload, "truth.visual.shadow_level"),
        "font_scale": _config_value(payload, "truth.visual.font_scale"),
    }


def _route(payload: PackageCompileInput) -> RouteConfig:
    return RouteConfig(
        home=_config_value(payload, "truth.route.home"),
        workbench=_config_value(payload, "truth.route.workbench"),
        basketball_showcase=_config_value(payload, "truth.route.basketball_showcase"),
        knowledge_list=_config_value(payload, "truth.route.knowledge_list"),
        knowledge_detail=_config_value(payload, "truth.route.knowledge_detail"),
        document_detail_prefix=_config_value(payload, "truth.route.document_detail_prefix"),
        api_prefix=_config_value(payload, "truth.route.api_prefix"),
    )


def _showcase_page(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "title": _config_value(payload, "truth.showcase_page.title"),
        "kicker": _config_value(payload, "truth.showcase_page.kicker"),
        "headline": _config_value(payload, "truth.showcase_page.headline"),
        "intro": _config_value(payload, "truth.showcase_page.intro"),
        "back_to_chat_label": _config_value(payload, "truth.showcase_page.back_to_chat_label"),
        "browse_knowledge_label": _config_value(payload, "truth.showcase_page.browse_knowledge_label"),
    }


def _a11y(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "reading_order": list(_config_value(payload, "truth.a11y.reading_order")),
        "keyboard_nav": list(_config_value(payload, "truth.a11y.keyboard_nav")),
        "announcements": list(_config_value(payload, "truth.a11y.announcements")),
    }


def _library(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "knowledge_base_id": _config_value(payload, "truth.library.knowledge_base_id"),
        "knowledge_base_name": _config_value(payload, "truth.library.knowledge_base_name"),
        "knowledge_base_description": _config_value(payload, "truth.library.knowledge_base_description"),
        "enabled": _config_value(payload, "truth.library.enabled"),
        "source_types": tuple(_config_value(payload, "truth.library.source_types")),
        "metadata_fields": tuple(_config_value(payload, "truth.library.metadata_fields")),
        "default_focus": _config_value(payload, "truth.library.default_focus"),
        "list_variant": _config_value(payload, "truth.library.list_variant"),
        "allow_create": _config_value(payload, "truth.library.allow_create"),
        "allow_delete": _config_value(payload, "truth.library.allow_delete"),
        "search_placeholder": _config_value(payload, "truth.library.search_placeholder"),
    }


def _backend_library(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "knowledge_base_id": _config_value(payload, "truth.library.knowledge_base_id"),
        "knowledge_base_name": _config_value(payload, "truth.library.knowledge_base_name"),
        "knowledge_base_description": _config_value(payload, "truth.library.knowledge_base_description"),
        "source_types": tuple(_config_value(payload, "truth.library.source_types")),
        "metadata_fields": tuple(_config_value(payload, "truth.library.metadata_fields")),
        "allow_create": _config_value(payload, "truth.library.allow_create"),
        "allow_delete": _config_value(payload, "truth.library.allow_delete"),
    }


def _preview(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "enabled": _config_value(payload, "truth.preview.enabled"),
        "renderers": list(_config_value(payload, "truth.preview.renderers")),
        "anchor_mode": _config_value(payload, "truth.preview.anchor_mode"),
        "show_toc": _config_value(payload, "truth.preview.show_toc"),
        "preview_variant": _config_value(payload, "truth.preview.preview_variant"),
    }


def _chat(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "enabled": _config_value(payload, "truth.chat.enabled"),
        "citations_enabled": _config_value(payload, "truth.chat.citations_enabled"),
        "mode": _config_value(payload, "truth.chat.mode"),
        "citation_style": _config_value(payload, "truth.chat.citation_style"),
        "bubble_variant": _config_value(payload, "truth.chat.bubble_variant"),
        "composer_variant": _config_value(payload, "truth.chat.composer_variant"),
        "system_prompt": _config_value(payload, "truth.chat.system_prompt"),
        "placeholder": _config_value(payload, "truth.chat.placeholder"),
        "welcome": _config_value(payload, "truth.chat.welcome"),
        "welcome_prompts": list(_config_value(payload, "truth.chat.welcome_prompts")),
    }


def _backend_chat(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "citation_style": _config_value(payload, "truth.chat.citation_style"),
    }


def _context(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "selection_mode": _config_value(payload, "truth.context.selection_mode"),
        "max_citations": _config_value(payload, "truth.context.max_citations"),
        "max_preview_sections": _config_value(payload, "truth.context.max_preview_sections"),
        "sticky_document": _config_value(payload, "truth.context.sticky_document"),
    }


def _sticky_document(payload: PackageCompileInput) -> bool:
    value = _config_value(payload, "truth.context.sticky_document")
    return bool(value)


def _return_config(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "enabled": _config_value(payload, "truth.return.enabled"),
        "targets": tuple(_config_value(payload, "truth.return.targets")),
        "anchor_restore": _config_value(payload, "truth.return.anchor_restore"),
        "citation_card_variant": _config_value(payload, "truth.return.citation_card_variant"),
    }


def _backend_return(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "targets": tuple(_config_value(payload, "truth.return.targets")),
        "anchor_restore": _config_value(payload, "truth.return.anchor_restore"),
    }


def _frontend_refinement(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "frontend_renderer": _config_value(payload, "refinement.frontend.renderer"),
        "style_profile": _config_value(payload, "refinement.frontend.style_profile"),
        "script_profile": _config_value(payload, "refinement.frontend.script_profile"),
    }


def _backend_refinement(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "renderer": _config_value(payload, "refinement.backend.renderer"),
        "transport": _config_value(payload, "refinement.backend.transport"),
        "retrieval_strategy": _config_value(payload, "refinement.backend.retrieval_strategy"),
    }


def _evidence_refinement(payload: PackageCompileInput) -> dict[str, Any]:
    return {
        "project_config_endpoint": _config_value(payload, "refinement.evidence.project_config_endpoint"),
    }


def _visual_tokens(
    *,
    contract: KnowledgeBaseRuntimeProfile,
    surface: dict[str, Any],
    visual: dict[str, Any],
    preview_variant: str,
) -> dict[str, str]:
    return contract.style_profiles.resolve_visual_tokens(
        surface_preset=str(visual["surface_preset"]),
        radius_scale=str(visual["radius_scale"]),
        shadow_level=str(visual["shadow_level"]),
        font_scale=str(visual["font_scale"]),
        sidebar_width=str(surface["sidebar_width"]),
        density=str(surface["density"]),
        accent=str(visual["accent"]),
        brand=str(visual["brand"]),
        preview_mode=str(surface["preview_mode"]),
        preview_variant=preview_variant,
    )


def _ui_pages(
    *,
    surface: dict[str, Any],
    route: RouteConfig,
    showcase_page: dict[str, Any],
    paths: UiSpecPaths,
    contract: KnowledgeBaseRuntimeProfile,
    ) -> dict[str, Any]:
    return {
        "chat_home": {
            "path": route.workbench,
            "title": surface["copy"]["hero_title"],
            "slots": list(contract.chat_home_slots),
            "entry_state": "welcome_prompts",
        },
        "basketball_showcase": {
            "path": paths.basketball_showcase_path,
            "title": showcase_page["title"],
            "kicker": showcase_page["kicker"],
            "headline": showcase_page["headline"],
            "intro": showcase_page["intro"],
            "back_to_chat_label": showcase_page["back_to_chat_label"],
            "browse_knowledge_label": showcase_page["browse_knowledge_label"],
            "slots": ["aux_sidebar", "page_header", "showcase_stage"],
        },
        "knowledge_list": {
            "path": route.knowledge_list,
            "title": surface["copy"]["library_title"],
            "subtitle": "聊天是主入口，知识库页用于切换上下文和确认可用来源。",
            "primary_action_label": "返回聊天",
            "rationale_title": "为什么这页是二级入口",
            "rationale_copy": (
                "主界面保持 ChatGPT 风格：左侧历史会话，中央聊天区，底部输入框。"
                "知识库管理和文档浏览退到二级页面，只在需要验证来源时展开。"
            ),
            "chat_action_label": "用此知识库开始聊天",
            "detail_action_label": "查看知识库详情",
            "slots": ["aux_sidebar", "page_header", "knowledge_cards"],
        },
        "knowledge_detail": {
            "path": paths.knowledge_base_detail_path,
            "chat_action_label": "用此知识库开始聊天",
            "overview_title": "知识库概况",
            "return_chat_with_document_label": "回到聊天并聚焦此文档",
            "document_detail_action_label": "查看文档详情",
            "slots": ["aux_sidebar", "page_header", "document_cards"],
        },
        "document_detail": {
            "path": paths.document_detail_path,
            "title": "文档详情",
            "subtitle": "从引用抽屉进入完整文档上下文，再返回聊天继续提问。",
            "return_chat_label": "返回聊天",
            "return_knowledge_detail_label": "返回知识库详情",
            "slots": ["aux_sidebar", "page_header", "document_sections"],
        },
    }


def _require_page_path(pages: dict[str, Any], page_id: str) -> str:
    value = pages.get(page_id)
    if not isinstance(value, dict):
        raise ValueError(f"frontend_app_spec.ui.pages.{page_id} must be a dict")
    path = value.get("path")
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError(f"frontend_app_spec.ui.pages.{page_id}.path must be a routable string")
    return path

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from review_workbench_runtime.frontend import compose_review_workbench_page
from rule_validation_models import RuleValidationOutcome, RuleValidationSummary

if TYPE_CHECKING:
    from project_runtime import ProjectRuntimeAssembly


def _outcome(
    rule_id: str,
    name: str,
    passed: bool,
    reasons: list[str],
    evidence: dict[str, object],
) -> RuleValidationOutcome:
    return RuleValidationOutcome(
        rule_id=rule_id,
        name=name,
        passed=passed,
        reasons=tuple(reasons),
        evidence=evidence,
    )


def validate_review_workbench_rules(project: "ProjectRuntimeAssembly") -> tuple[RuleValidationOutcome, ...]:
    frontend_spec = project.require_runtime_export("frontend_app_spec")
    domain_spec = project.require_runtime_export("review_workbench_domain_spec")
    backend_spec = project.require_runtime_export("backend_service_spec")
    if not isinstance(frontend_spec, dict):
        raise ValueError("frontend_app_spec export must be a dict")
    if not isinstance(domain_spec, dict):
        raise ValueError("review_workbench_domain_spec export must be a dict")
    if not isinstance(backend_spec, dict):
        raise ValueError("backend_service_spec export must be a dict")

    contract = frontend_spec.get("contract")
    ui = frontend_spec.get("ui")
    platform = domain_spec.get("platform")
    workbench = domain_spec.get("workbench")
    transport = backend_spec.get("transport")
    contracts = backend_spec.get("contracts")
    routes = backend_spec.get("routes")
    if not isinstance(contract, dict):
        raise ValueError("frontend_app_spec.contract must be a dict")
    if not isinstance(ui, dict):
        raise ValueError("frontend_app_spec.ui must be a dict")
    if not isinstance(platform, dict):
        raise ValueError("review_workbench_domain_spec.platform must be a dict")
    if not isinstance(workbench, dict):
        raise ValueError("review_workbench_domain_spec.workbench must be a dict")
    if not isinstance(transport, dict):
        raise ValueError("backend_service_spec.transport must be a dict")
    if not isinstance(contracts, dict):
        raise ValueError("backend_service_spec.contracts must be a dict")
    if not isinstance(routes, dict):
        raise ValueError("backend_service_spec.routes must be a dict")

    pages = ui.get("pages")
    extend_slots = contract.get("extend_slots")
    route_contract = contract.get("route_contract")
    surface_regions = contract.get("surface_regions")
    interaction_actions = contract.get("interaction_actions")
    scenes = workbench.get("scenes")
    scene_ids = workbench.get("scene_ids")
    if not isinstance(pages, dict):
        raise ValueError("frontend_app_spec.ui.pages must be a dict")
    if not isinstance(extend_slots, list):
        raise ValueError("frontend_app_spec.contract.extend_slots must be a list")
    if not isinstance(route_contract, dict):
        raise ValueError("frontend_app_spec.contract.route_contract must be a dict")
    if not isinstance(surface_regions, list):
        raise ValueError("frontend_app_spec.contract.surface_regions must be a list")
    if not isinstance(interaction_actions, list):
        raise ValueError("frontend_app_spec.contract.interaction_actions must be a list")
    if not isinstance(scenes, list):
        raise ValueError("review_workbench_domain_spec.workbench.scenes must be a list")
    if not isinstance(scene_ids, list):
        raise ValueError("review_workbench_domain_spec.workbench.scene_ids must be a list")

    r1_reasons: list[str] = []
    required_regions = {"platform_sidebar", "scene_workspace", "scene_feedback"}
    region_ids = {
        str(item.get("region_id"))
        for item in surface_regions
        if isinstance(item, dict)
    }
    missing_regions = required_regions - region_ids
    for region_id in sorted(missing_regions):
        r1_reasons.append(f"missing surface region: {region_id}")
    default_scene_id = str(platform.get("default_scene_id", ""))
    if default_scene_id not in {str(item) for item in scene_ids}:
        r1_reasons.append("platform.default_scene_id must exist in workbench.scene_ids")
    if len(scenes) < 2:
        r1_reasons.append("multi-scene review_workbench instance must expose at least two scenes")
    scene_id_set = {str(item) for item in scene_ids}
    scene_payload_ids = {
        str(item.get("scene_id"))
        for item in scenes
        if isinstance(item, dict)
    }
    if scene_payload_ids != scene_id_set:
        r1_reasons.append("workbench.scenes must align one-to-one with workbench.scene_ids")
    if not pages.get("workbench", {}).get("path", "").startswith("/"):
        r1_reasons.append("frontend workbench path must stay routable")

    r2_reasons: list[str] = []
    if len(extend_slots) < 2:
        r2_reasons.append("frontend extend slots must expose domain and backend modules")
    else:
        if extend_slots[0].get("module_id") != project.root_module_ids.get("review_workbench"):
            r2_reasons.append("domain workbench slot must point to the selected review_workbench module")
        if extend_slots[1].get("module_id") != project.root_module_ids.get("review_workbench_backend"):
            r2_reasons.append("backend contract slot must point to the selected review_workbench_backend module")
    required_actions = {"switch_scene", "refresh_scope", "open_processing_tab", "open_source_trace"}
    action_ids = {
        str(item.get("action_id"))
        for item in interaction_actions
        if isinstance(item, dict)
    }
    missing_actions = required_actions - action_ids
    for action_id in sorted(missing_actions):
        r2_reasons.append(f"missing interaction action: {action_id}")

    r3_reasons: list[str] = []
    if transport.get("api_prefix") != route_contract.get("api_prefix"):
        r3_reasons.append("backend_service_spec.transport.api_prefix must match frontend route_contract.api_prefix")
    if routes.get("workbench") != route_contract.get("workbench"):
        r3_reasons.append("backend_service_spec.routes.workbench must match frontend route_contract.workbench")
    required_contract_keys = {
        "tree_query",
        "filter_options",
        "list_query",
        "stats_summary",
        "tab_context",
        "query",
        "processing_open",
        "mutation",
        "source_trace",
    }
    missing_contracts = required_contract_keys - {str(key) for key in contracts.keys()}
    for key in sorted(missing_contracts):
        r3_reasons.append(f"missing backend contract: {key}")
    if not str(transport.get("project_config_endpoint", "")).startswith("/"):
        r3_reasons.append("project_config_endpoint must stay routable")

    r4_reasons: list[str] = []
    default_html = compose_review_workbench_page(project)
    if f"active scene: {default_scene_id}" not in default_html:
        r4_reasons.append("default workbench page must render the default active scene marker")
    for raw_scene in scenes:
        if not isinstance(raw_scene, dict):
            continue
        scene_id = str(raw_scene.get("scene_id", ""))
        scene_title = str(raw_scene.get("scene_title", ""))
        current_scope_id = str(raw_scene.get("current_scope_id", ""))
        current_scope_label = str(raw_scene.get("current_scope_label", ""))
        scope_action_title = str(raw_scene.get("scope_action_title", ""))
        scope_action_copy = str(raw_scene.get("scope_action_copy", ""))
        scope_feedback_title = str(raw_scene.get("scope_feedback_title", ""))
        scope_feedback_copy = str(raw_scene.get("scope_feedback_copy", ""))
        scope_tree = raw_scene.get("scope_tree", [])
        scope_stats = raw_scene.get("scope_stats", [])
        open_tabs = raw_scene.get("open_tabs", [])
        filter_fields = raw_scene.get("filter_fields", [])
        table_columns = raw_scene.get("table_columns", [])
        table_rows = raw_scene.get("table_rows", [])
        list_title = str(raw_scene.get("list_title", ""))
        processing_title = str(raw_scene.get("processing_title", ""))
        empty_result_title = str(raw_scene.get("empty_result_title", ""))
        empty_result_copy = str(raw_scene.get("empty_result_copy", ""))
        empty_processing_copy = str(raw_scene.get("empty_processing_copy", ""))
        sample_feedback = str(raw_scene.get("sample_feedback", ""))
        sample_items = raw_scene.get("sample_items", [])
        sample_operations = raw_scene.get("sample_operations", [])
        html = compose_review_workbench_page(project, requested_scene_id=scene_id)
        if f"active scene: {scene_id}" not in html:
            r4_reasons.append(f"scene page must expose active scene marker for {scene_id}")
        if scene_title not in html:
            r4_reasons.append(f"scene page must expose scene title for {scene_id}")
        if current_scope_id and f"scope: {current_scope_id}" not in html:
            r4_reasons.append(f"scene page must expose current scope marker for {scene_id}")
        if current_scope_label not in html:
            r4_reasons.append(f"scene page must expose current scope label for {scene_id}")
        if list_title not in html:
            r4_reasons.append(f"scene page must expose list title for {scene_id}")
        if processing_title not in html:
            r4_reasons.append(f"scene page must expose processing title for {scene_id}")
        if "result mode: results" not in html:
            r4_reasons.append(f"scene page must expose results mode marker for {scene_id}")
        if current_scope_id and f"action scope: {current_scope_id}" not in html:
            r4_reasons.append(f"scene page must expose action scope marker for {scene_id}")
        if current_scope_id and f"feedback scope: {current_scope_id}" not in html:
            r4_reasons.append(f"scene page must expose feedback scope marker for {scene_id}")
        if scope_action_title and scope_action_title not in html:
            r4_reasons.append(f"scene page must expose configured scope action title for {scene_id}")
        if scope_action_copy and scope_action_copy not in html:
            r4_reasons.append(f"scene page must expose configured scope action copy for {scene_id}")
        if scope_feedback_title and scope_feedback_title not in html:
            r4_reasons.append(f"scene page must expose configured scope feedback title for {scene_id}")
        if scope_feedback_copy and scope_feedback_copy not in html:
            r4_reasons.append(f"scene page must expose configured scope feedback copy for {scene_id}")
        if isinstance(scope_tree, list):
            for node in scope_tree:
                if not isinstance(node, dict):
                    continue
                node_id = str(node.get("node_id", ""))
                label = str(node.get("label", ""))
                if label and label not in html:
                    r4_reasons.append(f"scene page must expose configured scope tree label for {scene_id}")
                scoped_html = compose_review_workbench_page(
                    project,
                    requested_scene_id=scene_id,
                    requested_scope_id=node_id or None,
                )
                if node_id and f"scope: {node_id}" not in scoped_html:
                    r4_reasons.append(f"scene page must expose selected scope marker for {scene_id}:{node_id}")
                if label and label not in scoped_html:
                    r4_reasons.append(f"scene page must preserve selected scope label for {scene_id}:{node_id}")
        if isinstance(open_tabs, list):
            for tab in open_tabs:
                if not isinstance(tab, dict):
                    continue
                tab_id = str(tab.get("tab_id", ""))
                item_id = str(tab.get("item_id", ""))
                title = str(tab.get("title", ""))
                if title and title not in html:
                    r4_reasons.append(f"scene page must expose configured open tab title for {scene_id}")
                tab_html = compose_review_workbench_page(
                    project,
                    requested_scene_id=scene_id,
                    requested_scope_id=current_scope_id or None,
                    requested_tab_id=tab_id or None,
                )
                if title and f"active tab: {title}" not in tab_html:
                    r4_reasons.append(f"scene page must expose selected tab marker for {scene_id}:{tab_id}")
                if tab_id and f"tab id: {tab_id}" not in tab_html:
                    r4_reasons.append(f"scene page must expose selected tab id marker for {scene_id}:{tab_id}")
                if item_id and f"item: {item_id}" not in tab_html:
                    r4_reasons.append(f"scene page must align active item with selected tab for {scene_id}:{tab_id}")
        if isinstance(filter_fields, list):
            for field in filter_fields:
                if not isinstance(field, dict):
                    continue
                label = str(field.get("label", ""))
                if label and label not in html:
                    r4_reasons.append(f"scene page must expose configured filter field label for {scene_id}")
        if isinstance(table_columns, list):
            for column in table_columns:
                column_text = str(column)
                if column_text and column_text not in html:
                    r4_reasons.append(f"scene page must expose configured table column for {scene_id}")
        if isinstance(table_rows, list):
            for row in table_rows:
                if not isinstance(row, dict):
                    continue
                row_title = str(row.get("文件名称", ""))
                if row_title and row_title not in html:
                    r4_reasons.append(f"scene page must expose configured table row title for {scene_id}")
            if scene_id == "file_library_processing":
                scoped_row_map: dict[str, str] = {}
                for row in table_rows:
                    if not isinstance(row, dict):
                        continue
                    scope_id = str(row.get("scope_id", ""))
                    row_title = str(row.get("文件名称", ""))
                    if scope_id and row_title and scope_id not in scoped_row_map:
                        scoped_row_map[scope_id] = row_title
                for scope_id, row_title in scoped_row_map.items():
                    scoped_html = compose_review_workbench_page(
                        project,
                        requested_scene_id=scene_id,
                        requested_scope_id=scope_id,
                    )
                    if row_title not in scoped_html:
                        r4_reasons.append(
                            f"scope selection must expose scoped table row for {scene_id}:{scope_id}"
                        )
        if isinstance(scope_stats, list):
            for stat in scope_stats:
                if not isinstance(stat, dict):
                    continue
                label = str(stat.get("label", ""))
                value = str(stat.get("value", ""))
                if label and label not in html:
                    r4_reasons.append(f"scene page must expose configured scope stat label for {scene_id}")
                if value and value not in html:
                    r4_reasons.append(f"scene page must expose configured scope stat value for {scene_id}")
        if sample_feedback and sample_feedback not in html:
            r4_reasons.append(f"scene page must expose sample feedback for {scene_id}")
        if isinstance(sample_items, list):
            for item in sample_items:
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get("item_id", ""))
                title = str(item.get("title", ""))
                status = str(item.get("status", ""))
                if title and title not in html:
                    r4_reasons.append(f"scene page must expose sample item title for {scene_id}")
                if status and status not in html:
                    r4_reasons.append(f"scene page must expose sample item status for {scene_id}")
                if item_id:
                    item_html = compose_review_workbench_page(
                        project,
                        requested_scene_id=scene_id,
                        requested_item_id=item_id,
                    )
                    if f"item: {item_id}" not in item_html:
                        r4_reasons.append(f"scene detail panel must expose selected item marker for {scene_id}")
                    if title and title not in item_html:
                        r4_reasons.append(f"scene detail panel must expose selected item title for {scene_id}")
            if sample_items:
                first_item = sample_items[0]
                if isinstance(first_item, dict):
                    fallback_item_id = str(first_item.get("item_id", ""))
                    fallback_title = str(first_item.get("title", ""))
                    fallback_html = compose_review_workbench_page(
                        project,
                        requested_scene_id=scene_id,
                        requested_item_id="__invalid_item__",
                    )
                    if fallback_item_id and f"item: {fallback_item_id}" not in fallback_html:
                        r4_reasons.append(
                            f"invalid requested item must fall back to the first sample item for {scene_id}"
                        )
                    if fallback_title and fallback_title not in fallback_html:
                        r4_reasons.append(
                            f"invalid requested item fallback must preserve the first sample item title for {scene_id}"
                        )
        if isinstance(sample_operations, list):
            for operation in sample_operations:
                if not isinstance(operation, dict):
                    continue
                action_id = str(operation.get("action_id", ""))
                result = str(operation.get("result", ""))
                impact = str(operation.get("impact", ""))
                if action_id and action_id not in html:
                    r4_reasons.append(f"scene page must expose sample operation id for {scene_id}")
                if result and result not in html:
                    r4_reasons.append(f"scene page must expose sample operation result for {scene_id}")
                if impact and impact not in html:
                    r4_reasons.append(f"scene page must expose sample operation impact for {scene_id}")
        empty_html = compose_review_workbench_page(
            project,
            requested_scene_id=scene_id,
            requested_result_mode="empty",
        )
        if "result mode: empty" not in empty_html:
            r4_reasons.append(f"scene empty state must expose empty result marker for {scene_id}")
        if empty_result_title and empty_result_title not in empty_html:
            r4_reasons.append(f"scene empty state must expose configured empty result title for {scene_id}")
        if empty_result_copy and empty_result_copy not in empty_html:
            r4_reasons.append(f"scene empty state must expose configured empty result copy for {scene_id}")
        if empty_processing_copy and empty_processing_copy not in empty_html:
            r4_reasons.append(f"scene empty state must expose configured empty processing copy for {scene_id}")
        if "item: n/a" not in empty_html:
            r4_reasons.append(f"scene empty state must clear the active item marker for {scene_id}")
    fallback_html = compose_review_workbench_page(project, requested_scene_id="__invalid_scene__")
    if f"active scene: {default_scene_id}" not in fallback_html:
        r4_reasons.append("invalid requested scene must fall back to the default active scene")
    file_library_html = compose_review_workbench_page(project, requested_scene_id="file_library_processing")
    submission_review_html = compose_review_workbench_page(project, requested_scene_id="submission_review")
    if "打开处理页签" not in file_library_html or "查看来源回看" not in file_library_html:
        r4_reasons.append("file_library_processing page must expose file-library action labels")
    if "打开审核对象" not in submission_review_html or "查看审核上下文" not in submission_review_html:
        r4_reasons.append("submission_review page must expose review action labels")
    if "query:" not in file_library_html or "source_trace:" not in file_library_html:
        r4_reasons.append("file_library_processing page must expose file-library contract group")
    if "tree_query:" not in file_library_html or "tab_context:" not in file_library_html:
        r4_reasons.append("file_library_processing page must expose extended file-library contract group")
    if "review_queue:" not in submission_review_html or "review_submit:" not in submission_review_html:
        r4_reasons.append("submission_review page must expose review contract group")

    return (
        _outcome(
            "R1",
            "统一平台与多场景实例成立",
            not r1_reasons,
            r1_reasons,
            {
                "default_scene_id": default_scene_id,
                "scene_ids": list(scene_ids),
                "surface_regions": list(surface_regions),
            },
        ),
        _outcome(
            "R2",
            "前端承接链稳定",
            not r2_reasons,
            r2_reasons,
            {
                "extend_slots": list(extend_slots),
                "interaction_actions": list(interaction_actions),
            },
        ),
        _outcome(
            "R3",
            "后端契约对齐",
            not r3_reasons,
            r3_reasons,
            {
                "transport": dict(transport),
                "contracts": dict(contracts),
                "routes": dict(routes),
            },
        ),
        _outcome(
            "R4",
            "当前范围驱动链有效",
            not r4_reasons,
            r4_reasons,
            {
                "default_scene_id": default_scene_id,
                "scene_ids": list(scene_ids),
                "fallback_scene_id": default_scene_id,
            },
        ),
    )


def summarize_review_workbench_rules(
    results: tuple[RuleValidationOutcome, ...],
) -> RuleValidationSummary:
    return RuleValidationSummary(module_id="review_workbench.L3.M0", rules=results)

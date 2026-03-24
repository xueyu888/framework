from __future__ import annotations

from html import escape
from typing import Any

from project_runtime import ProjectRuntimeAssembly, load_project_runtime
from review_workbench_runtime.runtime_exports import (
    resolve_backend_service_spec,
    resolve_frontend_app_spec,
    resolve_review_workbench_domain_spec,
)


def _resolve_project(project: ProjectRuntimeAssembly | None) -> ProjectRuntimeAssembly:
    return project or load_project_runtime()


def _select_scene(
    workbench: dict[str, Any],
    *,
    requested_scene_id: str | None,
) -> tuple[dict[str, Any], str]:
    scenes = workbench["scenes"]
    scene_lookup = {
        str(item["scene_id"]): item
        for item in scenes
        if isinstance(item, dict) and "scene_id" in item
    }
    default_scene_id = str(workbench["default_scene_id"])
    active_scene_id = requested_scene_id or default_scene_id
    scene = scene_lookup.get(active_scene_id)
    if scene is None:
        active_scene_id = default_scene_id
        scene = scene_lookup.get(active_scene_id)
    if scene is None:
        raise ValueError("default scene must resolve to a scene payload")
    return scene, active_scene_id


def _scene_action_labels(scene: dict[str, Any]) -> tuple[str, str]:
    if str(scene["scene_id"]) == "submission_review":
        return ("打开审核对象", "查看审核上下文")
    return ("打开处理页签", "查看来源回看")


def _scene_mode_summary(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        return "当前场景强调审核工作栏、待审对象和结论回流。"
    return "当前场景强调文件清单、处理页签和来源回看。"


def _scene_feedback_summary(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        return "审核场景的回流重点是队列摘要、审核提示和结论回执。"
    return "文件库场景的回流重点是范围摘要、查询刷新和工作面提示。"


def _scene_contract_items(scene: dict[str, Any], backend_contracts: dict[str, Any]) -> list[tuple[str, str]]:
    preferred_keys: tuple[str, ...]
    if str(scene["scene_id"]) == "submission_review":
        preferred_keys = ("review_queue", "review_open", "review_submit", "review_feedback")
    else:
        preferred_keys = (
            "tree_query",
            "filter_options",
            "list_query",
            "stats_summary",
            "tab_context",
            "query",
            "processing_open",
            "mutation",
            "source_trace",
        )
    return [
        (key, str(backend_contracts[key]))
        for key in preferred_keys
        if key in backend_contracts
    ]


def _sample_items(scene: dict[str, Any]) -> list[dict[str, str]]:
    raw_items = scene.get("sample_items", [])
    if not isinstance(raw_items, list):
        return []
    items: list[dict[str, str]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        items.append(
            {
                "item_id": str(raw.get("item_id", "")),
                "title": str(raw.get("title", "")),
                "status": str(raw.get("status", "")),
                "note": str(raw.get("note", "")),
            }
        )
    return items


def _sample_feedback(scene: dict[str, Any]) -> str:
    return str(scene.get("sample_feedback", ""))


def _sample_operations(scene: dict[str, Any]) -> list[dict[str, str]]:
    raw_operations = scene.get("sample_operations", [])
    if not isinstance(raw_operations, list):
        return []
    operations: list[dict[str, str]] = []
    for raw in raw_operations:
        if not isinstance(raw, dict):
            continue
        operations.append(
            {
                "action_id": str(raw.get("action_id", "")),
                "result": str(raw.get("result", "")),
                "impact": str(raw.get("impact", "")),
            }
        )
    return operations


def _scene_scope_tree(scene: dict[str, Any]) -> list[dict[str, str]]:
    raw_nodes = scene.get("scope_tree", [])
    if not isinstance(raw_nodes, list):
        return []
    nodes: list[dict[str, str]] = []
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            continue
        nodes.append(
            {
                "node_id": str(raw.get("node_id", "")),
                "label": str(raw.get("label", "")),
                "depth": str(raw.get("depth", "0")),
                "active": "true" if bool(raw.get("active")) else "false",
            }
        )
    return nodes


def _scene_scope_stats(scene: dict[str, Any]) -> list[dict[str, str]]:
    raw_stats = scene.get("scope_stats", [])
    if not isinstance(raw_stats, list):
        return []
    stats: list[dict[str, str]] = []
    for raw in raw_stats:
        if not isinstance(raw, dict):
            continue
        stats.append(
            {
                "stat_id": str(raw.get("stat_id", "")),
                "label": str(raw.get("label", "")),
                "value": str(raw.get("value", "")),
            }
        )
    return stats


def _scene_open_tabs(scene: dict[str, Any]) -> list[dict[str, str]]:
    raw_tabs = scene.get("open_tabs", [])
    if not isinstance(raw_tabs, list):
        return []
    tabs: list[dict[str, str]] = []
    for raw in raw_tabs:
        if not isinstance(raw, dict):
            continue
        tabs.append(
            {
                "tab_id": str(raw.get("tab_id", "")),
                "title": str(raw.get("title", "")),
                "active": "true" if bool(raw.get("active")) else "false",
                "item_id": str(raw.get("item_id", "")),
            }
        )
    return tabs


def _scene_filter_fields(scene: dict[str, Any]) -> list[dict[str, str]]:
    raw_fields = scene.get("filter_fields", [])
    if not isinstance(raw_fields, list):
        return []
    fields: list[dict[str, str]] = []
    for raw in raw_fields:
        if not isinstance(raw, dict):
            continue
        fields.append(
            {
                "field_id": str(raw.get("field_id", "")),
                "label": str(raw.get("label", "")),
                "value": str(raw.get("value", "")),
                "placeholder": str(raw.get("placeholder", "")),
            }
        )
    return fields


def _scene_table_columns(scene: dict[str, Any]) -> list[str]:
    raw_columns = scene.get("table_columns", [])
    if not isinstance(raw_columns, list):
        return []
    return [str(item) for item in raw_columns]


def _scene_table_rows(scene: dict[str, Any], columns: list[str], *, result_mode: str) -> list[dict[str, str]]:
    if result_mode == "empty":
        return []
    raw_rows = scene.get("table_rows", [])
    if not isinstance(raw_rows, list):
        return []
    rows: list[dict[str, str]] = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            continue
        row: dict[str, str] = {"row_id": str(raw.get("row_id", ""))}
        row["scope_id"] = str(raw.get("scope_id", ""))
        for column in columns:
            row[column] = str(raw.get(column, ""))
        rows.append(row)
    return rows


def _select_scope_tree(
    scope_tree: list[dict[str, str]],
    *,
    default_scope_id: str,
    requested_scope_id: str | None,
) -> tuple[list[dict[str, str]], str, str]:
    node_lookup = {node["node_id"]: node for node in scope_tree if node.get("node_id")}
    active_scope_id = requested_scope_id or default_scope_id
    active_node = node_lookup.get(active_scope_id)
    if active_node is None:
        active_scope_id = default_scope_id
        active_node = node_lookup.get(active_scope_id)
    if active_node is None and scope_tree:
        active_node = scope_tree[0]
        active_scope_id = active_node["node_id"]
    if active_node is None:
        return scope_tree, default_scope_id, ""
    normalized_tree = [
        {
            **node,
            "active": "true" if node["node_id"] == active_scope_id else "false",
        }
        for node in scope_tree
    ]
    return normalized_tree, active_scope_id, active_node["label"]


def _filter_rows_for_scope(
    table_rows: list[dict[str, str]],
    *,
    active_scope_id: str,
) -> list[dict[str, str]]:
    if active_scope_id == "scope_current_repository":
        return table_rows
    return [
        row
        for row in table_rows
        if row.get("scope_id") == active_scope_id
    ]


def _select_open_tabs(
    open_tabs: list[dict[str, str]],
    *,
    requested_tab_id: str | None,
) -> tuple[list[dict[str, str]], dict[str, str] | None]:
    if not open_tabs:
        return open_tabs, None
    tab_lookup = {tab["tab_id"]: tab for tab in open_tabs if tab.get("tab_id")}
    active_tab_id = requested_tab_id
    active_tab = tab_lookup.get(active_tab_id or "")
    if active_tab is None:
        active_tab = next((tab for tab in open_tabs if tab.get("active") == "true"), open_tabs[0])
        active_tab_id = active_tab["tab_id"]
    normalized_tabs = [
        {
            **tab,
            "active": "true" if tab["tab_id"] == active_tab_id else "false",
        }
        for tab in open_tabs
    ]
    return normalized_tabs, active_tab


def _scene_empty_result_title(scene: dict[str, Any], fallback_title: str) -> str:
    return str(scene.get("empty_result_title", fallback_title))


def _scene_empty_result_copy(scene: dict[str, Any], fallback_copy: str) -> str:
    return str(scene.get("empty_result_copy", fallback_copy))


def _scene_empty_processing_copy(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        fallback = "当前审核队列下无匹配对象，审核工作栏保持空态并等待新的队列结果。"
    else:
        fallback = "当前范围下无匹配对象，处理工作面保持空态并等待新的查询结果。"
    return str(scene.get("empty_processing_copy", fallback))


def _scene_scope_action_title(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        fallback = "当前队列局部动作"
    else:
        fallback = "当前范围局部动作"
    return str(scene.get("scope_action_title", fallback))


def _scene_scope_action_copy(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        fallback = "刷新队列、审核动作与局部反馈都附着当前审核队列成立，不脱离当前队列单独存在。"
    else:
        fallback = "刷新范围、结构维护与局部反馈都附着当前文件库范围成立，不脱离当前范围单独存在。"
    return str(scene.get("scope_action_copy", fallback))


def _scene_scope_feedback_title(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        fallback = "当前队列反馈通道"
    else:
        fallback = "当前范围反馈通道"
    return str(scene.get("scope_feedback_title", fallback))


def _scene_scope_feedback_copy(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        fallback = "队列摘要、审核提示与结论回执都必须继续追溯到当前审核队列。"
    else:
        fallback = "范围摘要、查询刷新与工作面提示都必须继续追溯到当前文件库范围。"
    return str(scene.get("scope_feedback_copy", fallback))


def _resolve_result_mode(requested_result_mode: str | None) -> str:
    if requested_result_mode == "empty":
        return "empty"
    return "results"


def _active_sample_item(
    sample_items: list[dict[str, str]],
    *,
    requested_item_id: str | None,
) -> dict[str, str] | None:
    if not sample_items:
        return None
    item_lookup = {
        item["item_id"]: item
        for item in sample_items
        if item.get("item_id")
    }
    if requested_item_id and requested_item_id in item_lookup:
        return item_lookup[requested_item_id]
    return sample_items[0]


def _scene_detail_title(scene: dict[str, Any]) -> str:
    if str(scene["scene_id"]) == "submission_review":
        return "当前审核对象"
    return "当前处理对象"


def _scene_detail_copy(scene: dict[str, Any], active_item: dict[str, str] | None) -> str:
    if active_item is None:
        return "当前没有示例对象。"
    if str(scene["scene_id"]) == "submission_review":
        return f"审核工作栏当前聚焦 {active_item['title']}，可据此查看审核上下文、给出结论并观察回流。"
    return f"处理页签当前聚焦 {active_item['title']}，可据此查看来源、处理状态并继续回到文件清单。"


def compose_review_workbench_page(
    project: ProjectRuntimeAssembly | None = None,
    *,
    requested_scene_id: str | None = None,
    requested_scope_id: str | None = None,
    requested_tab_id: str | None = None,
    requested_item_id: str | None = None,
    requested_result_mode: str | None = None,
) -> str:
    resolved = _resolve_project(project)
    frontend_spec = resolve_frontend_app_spec(resolved)
    domain_spec = resolve_review_workbench_domain_spec(resolved)
    backend_spec = resolve_backend_service_spec(resolved)

    ui = frontend_spec["ui"]
    shell = ui["shell"]
    visual = ui["visual"]["tokens"]
    sidebar = ui["components"]["platform_sidebar"]
    header = ui["components"]["workspace_header"]
    summary = ui["components"]["scene_summary"]
    page = ui["pages"]["workbench"]
    workbench = domain_spec["workbench"]
    platform = domain_spec["platform"]
    scenes = workbench["scenes"]
    scene, active_scene_id = _select_scene(
        workbench,
        requested_scene_id=requested_scene_id,
    )
    backend_contracts = backend_spec["contracts"]
    workbench_path = str(page["path"])

    primary_action_label, secondary_action_label = _scene_action_labels(scene)
    mode_summary = _scene_mode_summary(scene)
    feedback_summary = _scene_feedback_summary(scene)
    scene_contract_items = _scene_contract_items(scene, backend_contracts)
    sample_items = _sample_items(scene)
    sample_feedback = _sample_feedback(scene)
    sample_operations = _sample_operations(scene)
    scope_tree = _scene_scope_tree(scene)
    scope_stats = _scene_scope_stats(scene)
    open_tabs = _scene_open_tabs(scene)
    filter_fields = _scene_filter_fields(scene)
    table_columns = _scene_table_columns(scene)
    result_mode = _resolve_result_mode(requested_result_mode)
    scope_tree, active_scope_id, active_scope_label = _select_scope_tree(
        scope_tree,
        default_scope_id=str(scene["current_scope_id"]),
        requested_scope_id=requested_scope_id,
    )
    table_rows = _scene_table_rows(scene, table_columns, result_mode=result_mode)
    table_rows = _filter_rows_for_scope(table_rows, active_scope_id=active_scope_id)
    normalized_tabs, active_tab = _select_open_tabs(open_tabs, requested_tab_id=requested_tab_id)
    open_tabs = normalized_tabs
    visible_sample_items = [] if result_mode == "empty" else sample_items
    requested_item = requested_item_id or (active_tab.get("item_id") if active_tab else None)
    active_item = _active_sample_item(sample_items, requested_item_id=requested_item)
    if result_mode == "empty":
        active_item = None
    empty_result_title = _scene_empty_result_title(scene, str(summary["empty_state_title"]))
    empty_result_copy = _scene_empty_result_copy(scene, str(summary["empty_state_copy"]))
    empty_processing_copy = _scene_empty_processing_copy(scene)
    scope_action_title = _scene_scope_action_title(scene)
    scope_action_copy = _scene_scope_action_copy(scene)
    scope_feedback_title = _scene_scope_feedback_title(scene)
    scope_feedback_copy = _scene_scope_feedback_copy(scene)

    style = f"""
body {{
  margin: 0;
  font-family: 'Segoe UI', 'PingFang SC', sans-serif;
  background:
    radial-gradient(circle at top left, rgba(15, 118, 110, 0.14), transparent 24%),
    linear-gradient(180deg, #f5f7f4, #eef4f1 60%, #e8efeb);
  color: #1f2937;
}}
.shell {{
  min-height: 100vh;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
}}
.sidebar {{
  padding: 28px 24px;
  background: rgba(255, 255, 255, 0.74);
  border-right: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18px);
}}
.eyebrow {{
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.sidebar h1 {{
  margin: 16px 0 10px;
  font-size: 28px;
  line-height: 1.05;
}}
.sidebar p {{
  margin: 0;
  color: #4b5563;
  line-height: 1.7;
}}
.scene-list {{
  margin-top: 28px;
  display: grid;
  gap: 12px;
}}
.scene-card {{
  display: block;
  padding: 14px 16px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
  color: inherit;
  text-decoration: none;
}}
.scene-card.active {{
  border-color: rgba(15, 118, 110, 0.38);
  box-shadow: 0 12px 28px rgba(15, 118, 110, 0.12);
}}
.scene-card strong {{
  display: block;
  margin-bottom: 8px;
}}
.meta {{
  display: inline-flex;
  margin-top: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  font-size: 13px;
}}
.main {{
  padding: 28px;
}}
.hero {{
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 24px;
  margin-bottom: 24px;
}}
.hero h2 {{
  margin: 10px 0 6px;
  font-size: clamp(34px, 5vw, 52px);
  line-height: 0.95;
}}
.hero p {{
  margin: 0;
  color: #4b5563;
  max-width: 44rem;
}}
.button-row {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}
.button {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  border-radius: 14px;
  text-decoration: none;
  font-weight: 600;
  border: 1px solid rgba(15, 23, 42, 0.08);
}}
.button.primary {{
  background: {escape(str(visual["accent"]))};
  color: white;
}}
.button.secondary {{
  background: white;
  color: #1f2937;
}}
.grid {{
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}}
.panel {{
  padding: 22px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
}}
.panel h3 {{
  margin: 0 0 10px;
  font-size: 20px;
}}
.panel p {{
  margin: 0;
  color: #4b5563;
  line-height: 1.7;
}}
.chip-row {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
}}
.chip {{
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  font-size: 13px;
}}
.contract-list {{
  margin: 16px 0 0;
  padding-left: 18px;
  color: #374151;
}}
.contract-list li + li {{
  margin-top: 8px;
}}
.sample-list {{
  display: grid;
  gap: 12px;
  margin-top: 16px;
}}
.sample-item {{
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.06);
}}
.sample-item strong {{
  display: block;
  margin-bottom: 6px;
}}
.sample-item p {{
  margin: 8px 0 0;
}}
.sample-item.active {{
  border-color: rgba(15, 118, 110, 0.26);
  background: rgba(15, 118, 110, 0.08);
}}
.tree-list {{
  display: grid;
  gap: 8px;
  margin-top: 16px;
}}
.tree-node {{
  display: block;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.05);
  color: inherit;
  text-decoration: none;
}}
.tree-node.active {{
  border-color: rgba(15, 118, 110, 0.26);
  background: rgba(15, 118, 110, 0.08);
}}
.field-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}}
.field-card {{
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.05);
}}
.field-card strong {{
  display: block;
  margin-bottom: 6px;
}}
.tab-row {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
}}
.tab-chip {{
  display: inline-flex;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.05);
  color: inherit;
  text-decoration: none;
}}
.tab-chip.active {{
  border-color: rgba(15, 118, 110, 0.26);
  background: rgba(15, 118, 110, 0.08);
}}
.table-scroll {{
  overflow-x: auto;
  margin-top: 16px;
}}
.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}}
.data-table th,
.data-table td {{
  padding: 12px 10px;
  text-align: left;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  white-space: nowrap;
}}
.stat-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}}
.stat-card {{
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.05);
}}
.stat-card strong {{
  display: block;
  font-size: 20px;
  margin-top: 6px;
}}
.operation-list {{
  display: grid;
  gap: 12px;
  margin-top: 16px;
}}
.operation-item {{
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(37, 99, 235, 0.05);
  border: 1px solid rgba(37, 99, 235, 0.08);
}}
.operation-item strong {{
  display: block;
  margin-bottom: 8px;
}}
.operation-item p {{
  margin: 8px 0 0;
}}
@media (max-width: 900px) {{
  .shell {{
    grid-template-columns: 1fr;
  }}
  .grid {{
    grid-template-columns: 1fr;
  }}
}}
"""

    body = f"""
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(page['title'])}</title>
    <style>{style}</style>
  </head>
  <body>
    <div class="shell" data-shell="{escape(shell['id'])}" data-layout="{escape(shell['layout_variant'])}">
      <aside class="sidebar">
        <span class="eyebrow">{escape(sidebar['scene_switch_label'])}</span>
        <h1>{escape(platform['platform_title'])}</h1>
        <p>{escape(sidebar['current_scope_label'])}: {escape(active_scope_label or scene['current_scope_label'])}</p>
        <div class="scene-list">
          {''.join(
              f'''
          <a class="scene-card{" active" if str(item["scene_id"]) == active_scene_id else ""}" href="{escape(workbench_path)}?scene={escape(str(item["scene_id"]))}&result=results">
            <strong>{escape(str(item["scene_title"]))}</strong>
            <div>{escape(str(item["list_title"]))}</div>
            <span class="meta">{escape(str(item["scene_id"]))}</span>
          </a>
          '''
              for item in scenes
              if isinstance(item, dict)
          )}
        </div>
      </aside>
      <main class="main">
        <header class="hero">
          <div>
            <span class="eyebrow">{escape(header['refresh_label'])}</span>
            <h2>{escape(header['title'])}</h2>
            <p>{escape(mode_summary)} {escape(summary['ready_text'])}</p>
          </div>
          <div class="button-row">
            <a class="button primary" href="{escape(workbench_path)}?scene={escape(active_scene_id)}">{escape(primary_action_label)}</a>
            <a class="button secondary" href="{escape(workbench_path)}?scene={escape(active_scene_id)}#source-trace">{escape(secondary_action_label)}</a>
          </div>
        </header>

        <section class="grid">
          <article class="panel">
            <h3>当前范围树</h3>
            <p>目录树、当前范围与局部动作入口共同说明文件仓库当前工作上下文。</p>
            <div class="tree-list">
              {''.join(
                  f'<a class="tree-node{" active" if node["active"] == "true" else ""}" data-node="{escape(node["node_id"])}" data-depth="{escape(node["depth"])}" href="{escape(workbench_path)}?scene={escape(active_scene_id)}&scope={escape(node["node_id"])}&result=results">{escape(node["label"])}</a>'
                  for node in scope_tree
              )}
            </div>
          </article>
          <article class="panel">
            <h3>已打开工作集</h3>
            <p>当前工作集证明文件仓库不仅有列表，还能保持多个已打开对象与一个当前激活对象。</p>
            <div class="tab-row">
              {''.join(
                  f'<a class="tab-chip{" active" if tab["active"] == "true" else ""}" data-tab="{escape(tab["tab_id"])}" href="{escape(workbench_path)}?scene={escape(active_scene_id)}&scope={escape(active_scope_id)}&tab={escape(tab["tab_id"])}&item={escape(tab["item_id"])}&result=results">{escape(tab["title"])}</a>'
                  for tab in open_tabs
              )}
            </div>
          </article>
          <article class="panel">
            <h3>查询条件集合</h3>
            <p>这些筛选项附着当前范围成立，用于驱动文件清单结果区的结果态或空态。</p>
            <div class="field-grid">
              {''.join(
                  f'''
              <article class="field-card" data-field="{escape(field["field_id"])}">
                <strong>{escape(field["label"])}</strong>
                <div>{escape(field["value"]) if field["value"] else escape(field["placeholder"])}</div>
              </article>
              '''
                  for field in filter_fields
              )}
            </div>
          </article>
          <article class="panel">
            <h3>{escape(str(scene['list_title']))}</h3>
            <p>{escape(empty_result_copy if result_mode == 'empty' else str(summary['empty_state_copy']))}</p>
            <div class="chip-row">
              <span class="chip">active scene: {escape(active_scene_id)}</span>
              <span class="chip">default scene: {escape(str(workbench['default_scene_id']))}</span>
              <span class="chip">scope: {escape(active_scope_id)}</span>
              <span class="chip">workset: {escape(str(scene['workset_mode']))}</span>
              <span class="chip">result mode: {escape(result_mode)}</span>
            </div>
            {
              (
                  f'''
            <div class="sample-list">
              {''.join(
              f"""
              <article class=\"sample-item{' active' if active_item and item['item_id'] == active_item['item_id'] else ''}\">
                <strong>{escape(item['title'])}</strong>
                <span class=\"chip\">{escape(item['item_id'])}</span>
                <span class=\"chip\">{escape(item['status'])}</span>
                <p>{escape(item['note'])}</p>
              </article>
              """
                  for item in visible_sample_items
              )}
            </div>
                  '''
              )
              if visible_sample_items
              else f'''
            <div class="sample-list">
              <article class="sample-item active">
                <strong>{escape(str(summary['empty_state_title']))}</strong>
                <span class="chip">{escape(empty_result_title)}</span>
                <span class="chip">result mode: empty</span>
                <p>{escape(empty_result_copy)}</p>
              </article>
            </div>
              '''
            }
            {
              (
                  f'''
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    {''.join(f"<th>{escape(column)}</th>" for column in table_columns)}
                  </tr>
                </thead>
                <tbody>
                  {''.join(
                      "<tr>" + ''.join(f"<td>{escape(row.get(column, ''))}</td>" for column in table_columns) + "</tr>"
                      for row in table_rows
                  )}
                </tbody>
              </table>
            </div>
                  '''
              )
              if table_columns
              else ""
            }
          </article>
          <article class="panel">
            <h3>{escape(str(scene['processing_title']))}</h3>
            <p>{escape(str(summary['loading_text'])) if result_mode == 'results' else escape(empty_processing_copy)}</p>
            <div class="chip-row">
              <span class="chip">active tab: {escape(active_tab["title"]) if active_tab else 'n/a'}</span>
              <span class="chip">tab id: {escape(active_tab["tab_id"]) if active_tab else 'n/a'}</span>
              <span class="chip">supports source trace: {escape(str(scene['supports_source_trace']))}</span>
              <span class="chip">supports mutation: {escape(str(scene['supports_mutation']))}</span>
            </div>
          </article>
          <article class="panel">
            <h3>{escape(_scene_detail_title(scene))}</h3>
            <p>{escape(_scene_detail_copy(scene, active_item))}</p>
            <div class="chip-row">
              <span class="chip">item: {escape(active_item['item_id']) if active_item else 'n/a'}</span>
              <span class="chip">status: {escape(active_item['status']) if active_item else 'n/a'}</span>
            </div>
            <div class="chip-row">
              {''.join(
                  f'<a class="button secondary" href="{escape(workbench_path)}?scene={escape(active_scene_id)}&scope={escape(active_scope_id)}&tab={escape(active_tab["tab_id"]) if active_tab else ""}&item={escape(item["item_id"])}&result=results">{escape(item["title"])}</a>'
                  for item in visible_sample_items
              )}
            </div>
            <p>{escape(active_item['note']) if active_item else ''}</p>
          </article>
          <article class="panel">
            <h3>平台中的可切换场景</h3>
            <p>这组场景卡证明统一平台承接的是合法场景实例集合，而不是某一个固定页面。</p>
            <div class="chip-row">
              {''.join(f'<span class="chip">{escape(str(item))}</span>' for item in workbench['scene_ids'])}
            </div>
          </article>
          <article class="panel" id="source-trace">
            <h3>{escape(scope_feedback_title)}</h3>
            <p>{escape(feedback_summary)} {escape(scope_feedback_copy)}</p>
            <p>{escape(sample_feedback)}</p>
            <div class="chip-row">
              <span class="chip">feedback scope: {escape(active_scope_id)}</span>
              {''.join(f'<span class="chip">{escape(str(item))}</span>' for item in scene['mutation_actions'])}
              {''.join(f'<span class="chip">{escape(str(item))}</span>' for item in scene['feedback_channels'])}
            </div>
          </article>
          <article class="panel">
            <h3>当前范围统计概览</h3>
            <p>这些统计项与当前范围一起变化，用来说明局部摘要不是孤立数字，而是范围驱动结果的一部分。</p>
            <div class="stat-grid">
              {''.join(
                  f'''
              <article class="stat-card" data-stat="{escape(stat["stat_id"])}">
                <div>{escape(stat["label"])}</div>
                <strong>{escape(stat["value"])}</strong>
              </article>
              '''
                  for stat in scope_stats
              )}
            </div>
          </article>
          <article class="panel">
            <h3>{escape(scope_action_title)}</h3>
            <p>{escape(scope_action_copy)}</p>
            <div class="chip-row">
              <span class="chip">action scope: {escape(active_scope_id)}</span>
              <span class="chip">{escape(header['refresh_label'])}</span>
              {''.join(f'<span class="chip">{escape(str(item))}</span>' for item in scene['mutation_actions'])}
            </div>
          </article>
          <article class="panel">
            <h3>当前场景最小契约组</h3>
            <p>这里只展示与当前场景直接相关的最小后端契约分组，证明同一平台可以承接不同场景的不同消费面。</p>
            <ul class="contract-list">
              {''.join(f'<li>{escape(key)}: {escape(value)}</li>' for key, value in scene_contract_items)}
            </ul>
          </article>
          <article class="panel">
            <h3>示例操作结果</h3>
            <p>这一组回执用来证明当前场景不仅能承接对象，还能承接该场景特有的结果回流语义。</p>
            <div class="operation-list">
              {''.join(
                  f'''
              <article class="operation-item">
                <strong>{escape(operation["action_id"])}</strong>
                <span class="chip">{escape(operation["result"])}</span>
                <p>{escape(operation["impact"])}</p>
              </article>
              '''
                  for operation in sample_operations
              )}
            </div>
          </article>
        </section>
      </main>
    </div>
  </body>
</html>
"""
    return body


def build_review_workbench_page_handler(
    project: ProjectRuntimeAssembly,
    repository: Any | None = None,
) -> Any:
    def handler(
        scene: str | None = None,
        scope: str | None = None,
        tab: str | None = None,
        item: str | None = None,
        result: str | None = None,
    ) -> str:
        return compose_review_workbench_page(
            project,
            requested_scene_id=scene,
            requested_scope_id=scope,
            requested_tab_id=tab,
            requested_item_id=item,
            requested_result_mode=result,
        )

    return handler

from __future__ import annotations

import json
import os
import stat
import shutil
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any

from project_runtime.models import ProjectRuntimeAssembly


SUPPORTED_REVIEW_WORKBENCH_RENDERERS = {
    "review_workbench_react_vite_tailwind_ts_strict_v1",
}


@dataclass(frozen=True)
class FrontendImplementationProfile:
    frontend_renderer: str
    framework: str
    bundler: str
    styling: str
    language: str
    typescript_strict: bool
    package_manager: str
    icon_library: str
    component_library: str
    component_mapping_profile: str
    primitive_strategy: str

    @classmethod
    def from_frontend_spec(cls, frontend_spec: dict[str, Any]) -> "FrontendImplementationProfile":
        implementation = frontend_spec["ui"]["implementation"]
        return cls(
            frontend_renderer=str(implementation["frontend_renderer"]),
            framework=str(implementation.get("framework", "react")),
            bundler=str(implementation.get("bundler", "vite")),
            styling=str(implementation.get("styling", "tailwindcss")),
            language=str(implementation.get("language", "typescript")),
            typescript_strict=bool(implementation.get("typescript_strict", True)),
            package_manager=str(implementation.get("package_manager", "pnpm")),
            icon_library=str(implementation.get("icon_library", "lucide-react")),
            component_library=str(implementation.get("component_library", "plain_html")),
            component_mapping_profile=str(implementation.get("component_mapping_profile", "default")),
            primitive_strategy=str(implementation.get("primitive_strategy", "semantic_adapter")),
        )


def materialize_frontend_scaffold(assembly: ProjectRuntimeAssembly, output_dir: Path) -> None:
    frontend_spec = assembly.require_runtime_export("frontend_app_spec")
    implementation = frontend_spec.get("ui", {}).get("implementation", {})
    renderer = str(implementation.get("frontend_renderer", "")).strip()
    if not renderer:
        raise ValueError("frontend_app_spec.ui.implementation.frontend_renderer must be a non-empty string")
    if "review_workbench_domain_spec" not in assembly.runtime_exports:
        return
    if renderer not in SUPPORTED_REVIEW_WORKBENCH_RENDERERS:
        return
    _materialize_review_workbench_react_app(assembly, output_dir)


def _materialize_review_workbench_react_app(assembly: ProjectRuntimeAssembly, output_dir: Path) -> None:
    frontend_spec = assembly.require_runtime_export("frontend_app_spec")
    implementation = FrontendImplementationProfile.from_frontend_spec(frontend_spec)

    if implementation.component_library == "shadcn_ui":
        _materialize_review_workbench_react_shadcn_app(assembly, output_dir, implementation)
        return
    _materialize_review_workbench_react_plain_app(assembly, output_dir, implementation)


def _materialize_review_workbench_react_plain_app(
    assembly: ProjectRuntimeAssembly,
    output_dir: Path,
    implementation: FrontendImplementationProfile,
) -> None:
    frontend_spec = assembly.require_runtime_export("frontend_app_spec")
    review_workbench = assembly.require_runtime_export("review_workbench_domain_spec")
    backend_spec = assembly.require_runtime_export("backend_service_spec")
    visual = frontend_spec["ui"]["visual"]["tokens"]
    route_contract = frontend_spec["contract"]["route_contract"]

    if output_dir.exists():
        _clear_managed_frontend_outputs(output_dir)
    src_dir = output_dir / "src"
    generated_dir = src_dir / "generated"
    src_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    runtime_data = {
        "project": assembly.metadata.to_dict(),
        "frontend_app_spec": frontend_spec,
        "review_workbench_domain_spec": review_workbench,
        "backend_service_spec": backend_spec,
    }
    (generated_dir / "runtime-data.json").write_text(
        json.dumps(runtime_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    files = {
        "package.json": _package_json(
            assembly.metadata.project_id,
            package_manager=implementation.package_manager,
            icon_library=implementation.icon_library,
            component_library=implementation.component_library,
        ),
        "tsconfig.json": _tsconfig_json(),
        "tsconfig.node.json": _tsconfig_node_json(),
        "vite.config.ts": _vite_config_ts(),
        "tailwind.config.ts": _tailwind_config_ts(),
        "postcss.config.js": _postcss_config_js(),
        "index.html": _index_html(frontend_spec["ui"]["components"]["platform_sidebar"]["title"]),
        "src/main.tsx": _main_tsx(),
        "src/styles.css": _styles_css(
            accent=str(visual["accent"]),
            brand=str(visual["brand"]),
        ),
        "src/vite-env.d.ts": "/// <reference types=\"vite/client\" />\n",
        "src/App.tsx": _app_tsx_plain(route_contract["workbench"], icon_library=implementation.icon_library),
        "src/types.ts": _types_ts(),
        "README.md": _frontend_app_readme(package_manager=implementation.package_manager),
    }
    for relative_path, content in files.items():
        path = output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _validate_generated_frontend_app(output_dir)


def _materialize_review_workbench_react_shadcn_app(
    assembly: ProjectRuntimeAssembly,
    output_dir: Path,
    implementation: FrontendImplementationProfile,
) -> None:
    frontend_spec = assembly.require_runtime_export("frontend_app_spec")
    review_workbench = assembly.require_runtime_export("review_workbench_domain_spec")
    backend_spec = assembly.require_runtime_export("backend_service_spec")
    visual = frontend_spec["ui"]["visual"]["tokens"]
    route_contract = frontend_spec["contract"]["route_contract"]

    if output_dir.exists():
        _clear_managed_frontend_outputs(output_dir)
    src_dir = output_dir / "src"
    generated_dir = src_dir / "generated"
    src_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    runtime_data = {
        "project": assembly.metadata.to_dict(),
        "frontend_app_spec": frontend_spec,
        "review_workbench_domain_spec": review_workbench,
        "backend_service_spec": backend_spec,
    }
    (generated_dir / "runtime-data.json").write_text(
        json.dumps(runtime_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    files = {
        "package.json": _package_json(
            assembly.metadata.project_id,
            package_manager=implementation.package_manager,
            icon_library=implementation.icon_library,
            component_library=implementation.component_library,
        ),
        "tsconfig.json": _tsconfig_json(),
        "tsconfig.node.json": _tsconfig_node_json(),
        "vite.config.ts": _vite_config_ts(),
        "tailwind.config.ts": _tailwind_config_ts(),
        "postcss.config.js": _postcss_config_js(),
        "index.html": _index_html(frontend_spec["ui"]["components"]["platform_sidebar"]["title"]),
        "src/main.tsx": _main_tsx(),
        "src/styles.css": _styles_css(
            accent=str(visual["accent"]),
            brand=str(visual["brand"]),
        ),
        "src/vite-env.d.ts": "/// <reference types=\"vite/client\" />\n",
        "src/App.tsx": _app_tsx_shadcn_v3(route_contract["workbench"], icon_library=implementation.icon_library),
        "src/types.ts": _types_ts(),
        "src/components/ui/input.tsx": _ui_input_tsx(),
        "src/components/ui/select.tsx": _ui_select_tsx(),
        "src/components/semantic/select.tsx": _semantic_select_tsx(),
        "src/components/semantic/tabs.tsx": _semantic_tabs_tsx(),
        "README.md": _frontend_app_readme(package_manager=implementation.package_manager),
    }
    for relative_path, content in files.items():
        path = output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _validate_generated_frontend_app(output_dir)


def _package_json(project_id: str, *, package_manager: str, icon_library: str, component_library: str) -> str:
    dependencies = {
        "react": "^19.1.0",
        "react-dom": "^19.1.0",
        icon_library: "^0.542.0",
    }
    if component_library == "shadcn_ui":
        dependencies["@radix-ui/react-select"] = "^2.2.6"
    payload = {
        "name": f"{project_id}-frontend",
        "private": True,
        "version": "0.1.0",
        "type": "module",
        "packageManager": f"{package_manager}@10.8.0" if package_manager == "pnpm" else package_manager,
        "scripts": {
            "dev": "vite",
            "build": "tsc -b && vite build",
            "preview": "vite preview",
        },
        "dependencies": dependencies,
        "devDependencies": {
            "@types/react": "^19.1.2",
            "@types/react-dom": "^19.1.2",
            "@vitejs/plugin-react": "^5.0.4",
            "autoprefixer": "^10.4.21",
            "postcss": "^8.5.6",
            "tailwindcss": "^3.4.17",
            "typescript": "^5.9.3",
            "vite": "^7.1.7",
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _tsconfig_json() -> str:
    payload = {
        "files": [],
        "references": [{"path": "./tsconfig.node.json"}],
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "Bundler",
            "allowImportingTsExtensions": False,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True,
        },
        "include": ["src"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _tsconfig_node_json() -> str:
    payload = {
        "compilerOptions": {
            "composite": True,
            "skipLibCheck": True,
            "module": "ESNext",
            "moduleResolution": "Bundler",
            "allowSyntheticDefaultImports": True,
        },
        "include": ["vite.config.ts", "tailwind.config.ts"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _vite_config_ts() -> str:
    return """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
});
"""


def _tailwind_config_ts() -> str:
    return """import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
"""


def _postcss_config_js() -> str:
    return """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""


def _index_html(title: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <script>
      (() => {{
        const storageKey = 'review-workbench-theme';
        const storedTheme = window.localStorage.getItem(storageKey);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const resolvedTheme = storedTheme === 'dark' || storedTheme === 'light'
          ? storedTheme
          : (prefersDark ? 'dark' : 'light');
        document.documentElement.dataset.theme = resolvedTheme;
      }})();
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""


def _main_tsx() -> str:
    return """import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
"""


def _types_ts() -> str:
    return """export type StatItem = {
  stat_id: string;
  label: string;
  value: string;
  order?: number;
};

export type ScopeNode = {
  node_id: string;
  label: string;
  depth: number;
  active: boolean | string;
};

export type OpenTab = {
  tab_id: string;
  title: string;
  active: boolean | string;
  item_id: string;
};

export type FilterField = {
  field_id: string;
  label: string;
  value: string;
  placeholder: string;
};

export type SemanticSelectOption = {
  label: string;
  value: string;
};

export type SampleItem = {
  item_id: string;
  title: string;
  status: string;
  note: string;
};

export type SampleOperation = {
  action_id: string;
  result: string;
  impact: string;
};

export type SceneSpec = {
  scene_id: string;
  scene_title: string;
  current_scope_id: string;
  current_scope_label: string;
  scope_tree: ScopeNode[];
  scope_stats: StatItem[];
  open_tabs: OpenTab[];
  filter_fields: FilterField[];
  table_columns: string[];
  table_rows: Record<string, string>[];
  scope_action_title: string;
  scope_action_copy: string;
  scope_feedback_title: string;
  scope_feedback_copy: string;
  list_title: string;
  processing_title: string;
  empty_result_title: string;
  empty_result_copy: string;
  empty_processing_copy: string;
  supports_source_trace: boolean;
  supports_mutation: boolean;
  mutation_actions: string[];
  feedback_channels: string[];
  workset_mode: string;
  sample_items: SampleItem[];
  sample_feedback: string;
  sample_operations: SampleOperation[];
};

export type ReviewWorkbenchDomainSpec = {
  platform: {
    platform_id: string;
    platform_title: string;
    default_scene_id: string;
    scene_ids: string[];
    sidebar_title?: string;
    global_search_placeholder?: string;
    theme_toggle_enabled?: boolean;
    fullscreen_action_enabled?: boolean;
    platform_stats?: StatItem[];
  };
  workbench: {
    default_scene_id: string;
    scene_ids: string[];
    scenes: SceneSpec[];
  };
};

export type FrontendAppSpec = {
  ui: {
    visual: {
      tokens: {
        accent: string;
        brand: string;
      };
    };
  };
  contract: {
    route_contract: {
      workbench: string;
    };
  };
};

export type RuntimeData = {
  frontend_app_spec: FrontendAppSpec;
  review_workbench_domain_spec: ReviewWorkbenchDomainSpec;
};
"""


def _app_tsx_plain(workbench_path: str, *, icon_library: str) -> str:
    if icon_library != "lucide-react":
        raise ValueError(f"unsupported review_workbench icon library: {icon_library}")
    return """import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  BookOpen,
  FileText,
  FolderTree,
  GitBranch,
  History,
  Maximize2,
  Minimize2,
  Moon,
  RefreshCw,
  Search,
  Sun,
  Upload,
  UserRound,
  X,
} from 'lucide-react';

import runtimeData from './generated/runtime-data.json';
import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField } from './types';

const data = runtimeData as RuntimeData;
const themeStorageKey = 'review-workbench-theme';
const sidebarDirectoryMinHeight = 156;
const sidebarOverviewMinHeight = 188;
const sidebarMinWidth = 220;
const workspaceMinWidth = 720;
const shellDividerSize = 8;
const selectLikeFieldIds = new Set(['vendor', 'category', 'is_classified', 'status']);
const optionMap: Record<string, string[]> = {
  vendor: ['全部', 'TI', 'MPS', 'ADI'],
  category: ['全部', '电源', '接口', '传感'],
  is_classified: ['全部', '已分类', '未分类'],
  status: ['全部', '待审核', '已审核', '未解决'],
};

function asBool(value: boolean | string | undefined): boolean {
  return value === true || value === 'true';
}

function sceneById(sceneId: string): SceneSpec {
  const scene = data.review_workbench_domain_spec.workbench.scenes.find((item) => item.scene_id === sceneId);
  return scene ?? data.review_workbench_domain_spec.workbench.scenes[0];
}

function isFullscreenSupported(): boolean {
  return typeof document.fullscreenEnabled === 'boolean'
    ? document.fullscreenEnabled
    : typeof document.documentElement.requestFullscreen === 'function';
}

type InspectionBlock = {
  block_id: string;
  title: string;
  summary: string;
  detail: string;
  status: 'ready' | 'focus' | 'pending';
};

function buildInspectionBlocks(item: { title: string; status: string; note: string }): InspectionBlock[] {
  return [
    {
      block_id: 'overview',
      title: '文件概览',
      summary: `${item.title} 当前处于 ${item.status} 状态`,
      detail: item.note,
      status: 'focus',
    },
    {
      block_id: 'classification',
      title: '分类检查',
      summary: '核对分类名称、型号映射与归档位置是否一致',
      detail: '用于检查分类、型号、目录路径和结构字段是否已经满足归档与审核要求。',
      status: item.status === '已分类' ? 'ready' : 'pending',
    },
    {
      block_id: 'trace',
      title: '来源回看',
      summary: '校验来源路径、历史动作与处理记录',
      detail: '用于确认来源回看路径、历史动作回执和当前工作页签之间的对应关系。',
      status: 'ready',
    },
  ];
}

function StatList({ items }: { items: StatItem[] }) {
  return (
    <div className="stat-list">
      {items.map((item) => (
        <div className="stat-item" data-stat-kind={item.stat_id} key={item.stat_id}>
          <span className="stat-label">{item.label}</span>
          <strong className="stat-value">{item.value}</strong>
        </div>
      ))}
    </div>
  );
}

function ScopeTree({ nodes }: { nodes: ScopeNode[] }) {
  return (
    <div className="scope-tree">
      {nodes.map((node) => (
        <button className={`scope-node ${asBool(node.active) ? 'scope-node-active' : ''}`} key={node.node_id} type="button">
          <FolderTree className="scope-node-icon" strokeWidth={1.7} />
          <span className="scope-node-label">{node.label}</span>
        </button>
      ))}
    </div>
  );
}

function TabBar({
  tabs,
  activeTabId,
  onActivate,
  onClose,
}: {
  tabs: OpenTab[];
  activeTabId: string;
  onActivate: (tabId: string) => void;
  onClose: (tabId: string) => void;
}) {
  return (
    <div className="tab-bar">
      {tabs.map((tab) => {
        const active = tab.tab_id === activeTabId;
        const closable = Boolean(tab.item_id);
        return (
          <div className={`tab-chip ${active ? 'tab-chip-active' : ''}`} key={tab.tab_id}>
            <button className="tab-chip-main" type="button" onClick={() => onActivate(tab.tab_id)}>
              <FileText className="tab-chip-icon" strokeWidth={1.7} />
              <span className="tab-chip-text">{tab.title}</span>
            </button>
            {closable ? (
              <button
                aria-label={`关闭 ${tab.title}`}
                className="tab-chip-closer"
                type="button"
                onClick={() => onClose(tab.tab_id)}
              >
                <X className="tab-chip-close-icon" strokeWidth={1.9} />
              </button>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function FilterGrid({ fields, values, onChange }: { fields: FilterField[]; values: Record<string, string>; onChange: (fieldId: string, value: string) => void }) {
  return (
    <div className="filter-grid">
      {fields.map((field) => {
        const value = values[field.field_id] ?? '';
        const isSelect = selectLikeFieldIds.has(field.field_id);
        return (
          <label className="filter-field" key={field.field_id}>
            <span className="filter-label">{field.label}</span>
            {isSelect ? (
              <div className="filter-select-wrap">
                <select className="filter-control filter-select" value={value || '全部'} onChange={(event) => onChange(field.field_id, event.target.value)}>
                  {(optionMap[field.field_id] ?? ['全部']).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <input className="filter-control" type="text" value={value} placeholder={field.placeholder} onChange={(event) => onChange(field.field_id, event.target.value)} />
            )}
          </label>
        );
      })}
    </div>
  );
}

function EmptyTable({ columns, title, copy }: { columns: string[]; title: string; copy: string }) {
  return (
    <div className="table-shell">
      <table className="result-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="empty-cell" colSpan={columns.length}>
              <div className="empty-state">
                <div className="empty-icon">
                  <FileText className="empty-icon-file" strokeWidth={1.8} />
                  <span className="empty-icon-badge" />
                </div>
                <strong>{title}</strong>
                <p>{copy}</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function LibraryWorkspaceHeader({
  filterFields,
  filterValues,
  onChangeFilter,
  scopeLabel,
  onClearFilters,
}: {
  filterFields: FilterField[];
  filterValues: Record<string, string>;
  onChangeFilter: (fieldId: string, value: string) => void;
  scopeLabel: string;
  onClearFilters: () => void;
}) {
  return (
    <div className="filter-panel">
      <FilterGrid fields={filterFields} values={filterValues} onChange={onChangeFilter} />
      <div className="scope-summary-row">
        <span className="scope-summary-text">{`范围: ${scopeLabel}`}</span>
        <button className="link-button" type="button" onClick={onClearFilters}>清空筛选</button>
      </div>
    </div>
  );
}

function InspectionWorkspaceHeader({ item }: { item: { title: string; status: string; note: string } }) {
  return (
    <section className="inspection-header">
      <div className="inspection-title-row">
        <h2 className="inspection-title">{item.title}</h2>
        <span className="inspection-status">{item.status}</span>
      </div>
      <p className="inspection-note">{item.note}</p>
    </section>
  );
}

function LibraryTopbarMain({
  searchText,
  onSearchChange,
  placeholder,
}: {
  searchText: string;
  onSearchChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div className="topbar-search-wrap">
      <label className="topbar-search">
        <Search className="topbar-search-icon" strokeWidth={1.8} />
        <input
          className="topbar-search-input"
          type="text"
          value={searchText}
          placeholder={placeholder}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </label>
    </div>
  );
}

function InspectionTopbarMain({
  searchText,
  onSearchChange,
  placeholder,
}: {
  searchText: string;
  onSearchChange: (value: string) => void;
  placeholder: string;
}) {
  return <LibraryTopbarMain searchText={searchText} onSearchChange={onSearchChange} placeholder={placeholder} />;
}

function LibraryWorkspace({
  tabs,
  activeTabId,
  onActivateTab,
  onCloseTab,
  filterFields,
  filterValues,
  onChangeFilter,
  scopeLabel,
  onClearFilters,
  tableColumns,
  emptyTitle,
  emptyCopy,
}: {
  tabs: OpenTab[];
  activeTabId: string;
  onActivateTab: (tabId: string) => void;
  onCloseTab: (tabId: string) => void;
  filterFields: FilterField[];
  filterValues: Record<string, string>;
  onChangeFilter: (fieldId: string, value: string) => void;
  scopeLabel: string;
  onClearFilters: () => void;
  tableColumns: string[];
  emptyTitle: string;
  emptyCopy: string;
}) {
  return (
    <section className="workspace-card">
      <TabBar tabs={tabs} activeTabId={activeTabId} onActivate={onActivateTab} onClose={onCloseTab} />

      <LibraryWorkspaceHeader
        filterFields={filterFields}
        filterValues={filterValues}
        onChangeFilter={onChangeFilter}
        scopeLabel={scopeLabel}
        onClearFilters={onClearFilters}
      />

      <div className="result-panel">
        <EmptyTable columns={tableColumns} title={emptyTitle} copy={emptyCopy} />
      </div>
    </section>
  );
}

function InspectionWorkspace({
  tabs,
  activeTabId,
  onActivateTab,
  onCloseTab,
  item,
  blocks,
  activeBlockId,
  onSelectBlock,
  actions,
  feedback,
  onRunAction,
}: {
  tabs: OpenTab[];
  activeTabId: string;
  onActivateTab: (tabId: string) => void;
  onCloseTab: (tabId: string) => void;
  item: { title: string; status: string; note: string };
  blocks: InspectionBlock[];
  activeBlockId: string;
  onSelectBlock: (blockId: string) => void;
  actions: string[];
  feedback: string;
  onRunAction: (actionId: string) => void;
}) {
  return (
    <section className="workspace-card">
      <TabBar tabs={tabs} activeTabId={activeTabId} onActivate={onActivateTab} onClose={onCloseTab} />

      <InspectionWorkspaceHeader item={item} />

      <div className="result-panel">
        <FileInspectionWorkbench
          blocks={blocks}
          activeBlockId={activeBlockId}
          onSelectBlock={onSelectBlock}
          actions={actions}
          feedback={feedback}
          onRunAction={onRunAction}
        />
      </div>
    </section>
  );
}

export default function App() {
  const platform = data.review_workbench_domain_spec.platform;
  const activeScene = sceneById(platform.default_scene_id);
  const activeScope = activeScene.scope_tree.find((node) => asBool(node.active));
  const bottomStats = platform.platform_stats ?? activeScene.scope_stats;
  const themeToggleEnabled = asBool(platform.theme_toggle_enabled);
  const fullscreenActionEnabled = asBool(platform.fullscreen_action_enabled);

  const initialFilters = useMemo<Record<string, string>>(
    () => Object.fromEntries(activeScene.filter_fields.map((field) => [field.field_id, field.value ?? ''])),
    [activeScene.filter_fields],
  );
  const defaultTabs = useMemo<OpenTab[]>(
    () => activeScene.open_tabs.map((tab) => ({ ...tab })),
    [activeScene.open_tabs],
  );
  const defaultActiveTabId = defaultTabs.find((tab) => asBool(tab.active))?.tab_id ?? defaultTabs[0]?.tab_id ?? 'tab-file-library';

  const [activeRail, setActiveRail] = useState<'library' | 'graph' | 'history'>('library');
  const [openTabs, setOpenTabs] = useState<OpenTab[]>(defaultTabs);
  const [activeTabId, setActiveTabId] = useState<string>(defaultActiveTabId);
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>(initialFilters);
  const [darkMode, setDarkMode] = useState(() => document.documentElement.dataset.theme === 'dark');
  const [isFullscreen, setIsFullscreen] = useState<boolean>(() => Boolean(document.fullscreenElement));
  const [canFullscreen, setCanFullscreen] = useState<boolean>(() => isFullscreenSupported());
  const [directoryPanelHeight, setDirectoryPanelHeight] = useState<number | null>(null);
  const [isSidebarDividerHovered, setIsSidebarDividerHovered] = useState(false);
  const [isSidebarResizing, setIsSidebarResizing] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState<number | null>(null);
  const [isShellDividerHovered, setIsShellDividerHovered] = useState(false);
  const [isShellResizing, setIsShellResizing] = useState(false);
  const [isCompactLayout, setIsCompactLayout] = useState<boolean>(() => window.innerWidth <= 900);
  const [activeInspectionBlockId, setActiveInspectionBlockId] = useState<string>('overview');
  const [interactionFeedback, setInteractionFeedback] = useState<string>(activeScene.sample_feedback);
  const [refreshTick, setRefreshTick] = useState(0);
  const hasMountedTheme = useRef(false);
  const platformShellRef = useRef<HTMLDivElement | null>(null);
  const sidebarPanelRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    const root = document.documentElement;
    if (hasMountedTheme.current) {
      root.dataset.themeSwitching = 'true';
    }
    root.dataset.theme = darkMode ? 'dark' : 'light';
    window.localStorage.setItem(themeStorageKey, darkMode ? 'dark' : 'light');
    const frame = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        delete root.dataset.themeSwitching;
      });
    });
    hasMountedTheme.current = true;
    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [darkMode]);

  useEffect(() => {
    setOpenTabs(defaultTabs);
    setActiveTabId(defaultActiveTabId);
  }, [defaultActiveTabId, defaultTabs]);

  useEffect(() => {
    setActiveInspectionBlockId('overview');
    setInteractionFeedback(activeScene.sample_feedback);
  }, [activeScene.sample_feedback, activeTabId]);

  useEffect(() => {
    function syncFullscreenState() {
      setIsFullscreen(Boolean(document.fullscreenElement));
      setCanFullscreen(isFullscreenSupported());
    }

    syncFullscreenState();
    document.addEventListener('fullscreenchange', syncFullscreenState);
    return () => {
      document.removeEventListener('fullscreenchange', syncFullscreenState);
    };
  }, []);

  useEffect(() => {
    function syncCompactLayout() {
      setIsCompactLayout(window.innerWidth <= 900);
    }

    syncCompactLayout();
    window.addEventListener('resize', syncCompactLayout);
    return () => {
      window.removeEventListener('resize', syncCompactLayout);
    };
  }, []);

  useEffect(() => {
    function syncSidebarLayout() {
      const panel = sidebarPanelRef.current;
      if (!panel) {
        return;
      }
      const availableHeight = panel.clientHeight;
      const maxDirectoryHeight = Math.max(
        sidebarDirectoryMinHeight,
        availableHeight - sidebarOverviewMinHeight - 8,
      );
      setDirectoryPanelHeight((currentHeight) => {
        if (currentHeight === null) {
          const preferredHeight = Math.round(availableHeight * 0.68);
          return Math.min(Math.max(preferredHeight, sidebarDirectoryMinHeight), maxDirectoryHeight);
        }
        return Math.min(Math.max(currentHeight, sidebarDirectoryMinHeight), maxDirectoryHeight);
      });
    }

    syncSidebarLayout();
    window.addEventListener('resize', syncSidebarLayout);
    return () => {
      window.removeEventListener('resize', syncSidebarLayout);
    };
  }, []);

  useEffect(() => {
    function syncShellLayout() {
      const shell = platformShellRef.current;
      if (!shell) {
        return;
      }
      const availableWidth = shell.clientWidth;
      const maxSidebarWidth = Math.max(
        sidebarMinWidth,
        availableWidth - workspaceMinWidth - shellDividerSize,
      );
      setSidebarWidth((currentWidth) => {
        if (currentWidth === null) {
          const preferredWidth = 274;
          return Math.min(Math.max(preferredWidth, sidebarMinWidth), maxSidebarWidth);
        }
        return Math.min(Math.max(currentWidth, sidebarMinWidth), maxSidebarWidth);
      });
    }

    syncShellLayout();
    window.addEventListener('resize', syncShellLayout);
    return () => {
      window.removeEventListener('resize', syncShellLayout);
    };
  }, []);

  useEffect(() => {
    if (!isSidebarResizing) {
      return;
    }

    function handlePointerMove(event: PointerEvent) {
      const panel = sidebarPanelRef.current;
      if (!panel) {
        return;
      }
      const bounds = panel.getBoundingClientRect();
      const availableHeight = bounds.height;
      const maxDirectoryHeight = Math.max(
        sidebarDirectoryMinHeight,
        availableHeight - sidebarOverviewMinHeight - 8,
      );
      const nextHeight = event.clientY - bounds.top;
      setDirectoryPanelHeight(
        Math.min(Math.max(nextHeight, sidebarDirectoryMinHeight), maxDirectoryHeight),
      );
    }

    function handlePointerUp() {
      setIsSidebarResizing(false);
    }

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [isSidebarResizing]);

  useEffect(() => {
    if (!isShellResizing) {
      return;
    }

    function handlePointerMove(event: PointerEvent) {
      const shell = platformShellRef.current;
      if (!shell) {
        return;
      }
      const bounds = shell.getBoundingClientRect();
      const availableWidth = bounds.width;
      const maxSidebarWidth = Math.max(
        sidebarMinWidth,
        availableWidth - workspaceMinWidth - shellDividerSize,
      );
      const nextWidth = event.clientX - bounds.left;
      setSidebarWidth(
        Math.min(Math.max(nextWidth, sidebarMinWidth), maxSidebarWidth),
      );
    }

    function handlePointerUp() {
      setIsShellResizing(false);
    }

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };
  }, [isShellResizing]);

  function handleFilterChange(fieldId: string, value: string) {
    setFilters((current) => ({ ...current, [fieldId]: value }));
  }

  function handleClearFilters() {
    setFilters(initialFilters);
    setSearchText('');
  }

  function handleRefresh() {
    setRefreshTick((current) => current + 1);
  }

  function handleSidebarDividerPointerDown() {
    setIsSidebarResizing(true);
  }

  function handleShellDividerPointerDown() {
    setIsShellResizing(true);
  }

  async function handleToggleFullscreen(): Promise<void> {
    if (!canFullscreen) {
      return;
    }
    if (document.fullscreenElement) {
      await document.exitFullscreen();
      return;
    }
    await document.documentElement.requestFullscreen();
  }

  function handleCloseTab(tabId: string) {
    setOpenTabs((currentTabs) => {
      const closeIndex = currentTabs.findIndex((tab) => tab.tab_id === tabId);
      if (closeIndex < 0) {
        return currentTabs;
      }
      const nextTabs = currentTabs.filter((tab) => tab.tab_id !== tabId);
      if (nextTabs.length === 0) {
        return currentTabs;
      }
      if (tabId === activeTabId) {
        const fallbackTab = nextTabs[Math.max(0, closeIndex - 1)] ?? nextTabs[0];
        setActiveTabId(fallbackTab.tab_id);
      }
      return nextTabs;
    });
  }

  function handleRunInspectionAction(actionId: string) {
    const operation = activeScene.sample_operations.find((item) => item.action_id === actionId);
    setInteractionFeedback(operation ? `${operation.result} ${operation.impact}` : `已触发 ${actionId} 操作。`);
  }

  const sidebarPanelStyle =
    directoryPanelHeight === null
      ? undefined
      : {
          gridTemplateRows: `${directoryPanelHeight}px 8px minmax(${sidebarOverviewMinHeight}px, 1fr)`,
        };
  const resolvedSidebarWidth = sidebarWidth ?? 274;
  const platformShellStyle = isCompactLayout
    ? undefined
    : {
        gridTemplateColumns: `${resolvedSidebarWidth}px ${shellDividerSize}px minmax(${workspaceMinWidth}px, 1fr)`,
      };
  const activeTab = openTabs.find((tab) => tab.tab_id === activeTabId) ?? openTabs[0];
  const isLibraryTabActive = !activeTab?.item_id;
  const activeWorkItem =
    activeTab && activeTab.item_id
      ? activeScene.sample_items.find((item) => item.item_id === activeTab.item_id) ?? null
      : null;
  const inspectionBlocks = activeWorkItem ? buildInspectionBlocks(activeWorkItem) : [];

  return (
    <div className="platform-app">
      <div className="platform-shell">
        <header className="platform-topbar">
          <div className="platform-topbar-brand">
            <div className="sidebar-brand-mark" aria-hidden="true">
              <span className="sidebar-brand-orbit" />
              <span className="sidebar-brand-wave" />
            </div>
            <div className="sidebar-brand-copy">
              <strong>{platform.platform_title}</strong>
            </div>
          </div>
          <div className="platform-topbar-main">
            {isLibraryTabActive ? (
              <LibraryTopbarMain
                searchText={searchText}
                onSearchChange={setSearchText}
                placeholder={platform.global_search_placeholder ?? '搜索文件...'}
              />
            ) : activeWorkItem ? (
              <InspectionTopbarMain
                searchText={searchText}
                onSearchChange={setSearchText}
                placeholder={platform.global_search_placeholder ?? '搜索文件...'}
              />
            ) : null}
            <div className="topbar-tools">
              {themeToggleEnabled ? (
                <button className="toggle-pill" type="button" aria-label="Theme Toggle" onClick={() => setDarkMode((current) => !current)}>
                  <span className="toggle-pill-track">
                    <span className={`toggle-pill-thumb ${darkMode ? 'toggle-pill-thumb-active' : ''}`} />
                  </span>
                  {darkMode ? <Moon className="toggle-pill-icon" strokeWidth={1.8} /> : <Sun className="toggle-pill-icon" strokeWidth={1.8} />}
                </button>
              ) : null}
              <button className="square-tool" type="button" aria-label="Refresh" onClick={handleRefresh}>
                <RefreshCw className={`square-tool-icon ${refreshTick > 0 ? 'panel-icon-rotate' : ''}`} strokeWidth={1.8} />
              </button>
              {fullscreenActionEnabled && canFullscreen ? (
                <button
                  className="square-tool"
                  type="button"
                  aria-label={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
                  onClick={() => {
                    void handleToggleFullscreen();
                  }}
                >
                  {isFullscreen ? <Minimize2 className="square-tool-icon" strokeWidth={1.8} /> : <Maximize2 className="square-tool-icon" strokeWidth={1.8} />}
                </button>
              ) : null}
            </div>
          </div>
        </header>

        <div className="platform-body" ref={platformShellRef} style={platformShellStyle}>
        <aside className="sidebar-shell">
          <nav className="icon-rail" aria-label="Platform Tools">
            <button className={`rail-button ${activeRail === 'library' ? 'rail-button-active' : ''}`} type="button" aria-label="File Library" onClick={() => setActiveRail('library')}>
              <BookOpen className="rail-icon" strokeWidth={1.9} />
            </button>
            <button className={`rail-button ${activeRail === 'graph' ? 'rail-button-active' : ''}`} type="button" aria-label="Connections" onClick={() => setActiveRail('graph')}>
              <GitBranch className="rail-icon" strokeWidth={1.9} />
            </button>
            <button className={`rail-button ${activeRail === 'history' ? 'rail-button-active' : ''}`} type="button" aria-label="History" onClick={() => setActiveRail('history')}>
              <History className="rail-icon" strokeWidth={1.9} />
            </button>
            <div className="rail-spacer" />
            <button className="rail-avatar" type="button" aria-label="User Profile">
              <UserRound className="rail-avatar-icon" strokeWidth={1.8} />
            </button>
          </nav>

          <section className="sidebar-panel" ref={sidebarPanelRef} style={sidebarPanelStyle}>
            <div className="sidebar-directory">
              <div className="sidebar-directory-head">
                <strong>{platform.sidebar_title ?? '文件目录'}</strong>
                <div className="sidebar-head-actions">
                  <button className="panel-icon-button" type="button" aria-label="Upload">
                    <Upload className="panel-icon" strokeWidth={1.9} />
                  </button>
                  <button className="panel-icon-button" type="button" aria-label="Refresh" onClick={handleRefresh}>
                    <RefreshCw className={`panel-icon ${refreshTick > 0 ? 'panel-icon-rotate' : ''}`} strokeWidth={1.9} />
                  </button>
                </div>
              </div>
              <ScopeTree nodes={activeScene.scope_tree} />
            </div>

            <button
              aria-label="Resize sidebar sections"
              className={`sidebar-divider ${isSidebarDividerHovered || isSidebarResizing ? 'sidebar-divider-active' : ''}`}
              type="button"
              onPointerDown={handleSidebarDividerPointerDown}
              onMouseEnter={() => setIsSidebarDividerHovered(true)}
              onMouseLeave={() => setIsSidebarDividerHovered(false)}
            >
              <span className="sidebar-divider-line" />
            </button>

            <div className="sidebar-overview">
              <div className="overview-title">概览</div>
              <StatList items={bottomStats} />
            </div>
          </section>
        </aside>

        <button
          aria-label="Resize navigation and workspace"
          className={`shell-divider ${isShellDividerHovered || isShellResizing ? 'shell-divider-active' : ''}`}
          type="button"
          onPointerDown={handleShellDividerPointerDown}
          onMouseEnter={() => setIsShellDividerHovered(true)}
          onMouseLeave={() => setIsShellDividerHovered(false)}
        >
          <span className="shell-divider-line" />
        </button>

        <main className="workspace-shell">
          {isLibraryTabActive ? (
            <LibraryWorkspace
              tabs={openTabs}
              activeTabId={activeTabId}
              onActivateTab={setActiveTabId}
              onCloseTab={handleCloseTab}
              filterFields={activeScene.filter_fields}
              filterValues={filters}
              onChangeFilter={handleFilterChange}
              scopeLabel={activeScope?.label ?? activeScene.current_scope_label}
              onClearFilters={handleClearFilters}
              tableColumns={activeScene.table_columns}
              emptyTitle={activeScene.empty_result_title}
              emptyCopy={activeScene.empty_result_copy}
            />
          ) : activeWorkItem ? (
            <InspectionWorkspace
              tabs={openTabs}
              activeTabId={activeTabId}
              onActivateTab={setActiveTabId}
              onCloseTab={handleCloseTab}
              item={activeWorkItem}
              blocks={inspectionBlocks}
              activeBlockId={activeInspectionBlockId}
              onSelectBlock={setActiveInspectionBlockId}
              actions={activeScene.mutation_actions}
              feedback={interactionFeedback}
              onRunAction={handleRunInspectionAction}
            />
          ) : null}
        </main>

        </div>

        <footer className="platform-footer">
          <div className="workspace-footer">
            {bottomStats.map((item) => (
              <div className="footer-stat" data-stat-kind={item.stat_id} key={item.stat_id}>
                <span className="footer-stat-label">{item.label}</span>
                <span className="footer-stat-separator">:</span>
                <strong className="footer-stat-value">{item.value}</strong>
              </div>
            ))}
          </div>
        </footer>
      </div>
    </div>
  );
}

function FileInspectionWorkbench({
  blocks,
  activeBlockId,
  onSelectBlock,
  actions,
  feedback,
  onRunAction,
}: {
  blocks: InspectionBlock[];
  activeBlockId: string;
  onSelectBlock: (blockId: string) => void;
  actions: string[];
  feedback: string;
  onRunAction: (actionId: string) => void;
}) {
  const activeBlock = blocks.find((block) => block.block_id === activeBlockId) ?? blocks[0];
  return (
    <div className="inspection-shell">
      <div className="inspection-body">
        <aside className="inspection-block-list" aria-label="文件检查块">
          {blocks.map((block) => (
            <button
              key={block.block_id}
              className={`inspection-block ${block.block_id === activeBlock.block_id ? 'inspection-block-active' : ''}`}
              type="button"
              onClick={() => onSelectBlock(block.block_id)}
            >
              <span className={`inspection-block-indicator inspection-block-indicator-${block.status}`} />
              <span className="inspection-block-copy">
                <strong>{block.title}</strong>
                <span>{block.summary}</span>
              </span>
            </button>
          ))}
        </aside>

        <section className="inspection-detail">
          <div className="inspection-detail-card">
            <div className="inspection-detail-head">
              <strong>{activeBlock.title}</strong>
              <span>{activeBlock.summary}</span>
            </div>
            <p className="inspection-detail-copy">{activeBlock.detail}</p>
          </div>

          <div className="inspection-action-row">
            {actions.map((actionId) => (
              <button key={actionId} className="inspection-action-button" type="button" onClick={() => onRunAction(actionId)}>
                {actionId}
              </button>
            ))}
          </div>

          <div className="inspection-feedback">
            <strong>交互反馈</strong>
            <p>{feedback}</p>
          </div>
        </section>
      </div>
    </div>
  );
}
"""

def _app_tsx_shadcn(workbench_path: str, *, icon_library: str) -> str:
    if icon_library != "lucide-react":
        raise ValueError(f"unsupported review_workbench icon library: {icon_library}")
    base = _app_tsx_plain(workbench_path, icon_library=icon_library)
    base = base.replace(
        "import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField } from './types';",
        "import { Input } from './components/ui/input';\n"
        "import { SemanticSelect } from './components/semantic/select';\n"
        "import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField, SemanticSelectOption } from './types';",
    )
    old_filter = """function FilterGrid({ fields, values, onChange }: { fields: FilterField[]; values: Record<string, string>; onChange: (fieldId: string, value: string) => void }) {
  return (
    <div className="filter-grid">
      {fields.map((field) => {
        const value = values[field.field_id] ?? '';
        const isSelect = selectLikeFieldIds.has(field.field_id);
        return (
          <label className="filter-field" key={field.field_id}>
            <span className="filter-label">{field.label}</span>
            {isSelect ? (
              <div className="filter-select-wrap">
                <select className="filter-control filter-select" value={value || '鍏ㄩ儴'} onChange={(event) => onChange(field.field_id, event.target.value)}>
                  {(optionMap[field.field_id] ?? ['鍏ㄩ儴']).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <input className="filter-control" type="text" value={value} placeholder={field.placeholder} onChange={(event) => onChange(field.field_id, event.target.value)} />
            )}
          </label>
        );
      })}
    </div>
  );
}
"""
    new_filter = """function FilterGrid({ fields, values, onChange }: { fields: FilterField[]; values: Record<string, string>; onChange: (fieldId: string, value: string) => void }) {
  return (
    <div className="filter-grid">
      {fields.map((field) => {
        const value = values[field.field_id] ?? '';
        const isSelect = selectLikeFieldIds.has(field.field_id);
        if (isSelect) {
          const options: SemanticSelectOption[] = (optionMap[field.field_id] ?? ['鍏ㄩ儴']).map((option) => ({
            label: option,
            value: option,
          }));
          return (
            <SemanticSelect
              key={field.field_id}
              label={field.label}
              value={value || '鍏ㄩ儴'}
              placeholder={field.placeholder}
              options={options}
              onValueChange={(nextValue) => onChange(field.field_id, nextValue)}
            />
          );
        }
        return (
          <label className="filter-field" key={field.field_id}>
            <span className="filter-label">{field.label}</span>
            <Input className="filter-control shadcn-input" type="text" value={value} placeholder={field.placeholder} onChange={(event) => onChange(field.field_id, event.target.value)} />
          </label>
        );
      })}
    </div>
  );
}
"""
    return base.replace(old_filter, new_filter)


def _app_tsx_shadcn_v2(workbench_path: str, *, icon_library: str) -> str:
    if icon_library != "lucide-react":
        raise ValueError(f"unsupported review_workbench icon library: {icon_library}")
    base = _app_tsx_plain(workbench_path, icon_library=icon_library)
    base = base.replace(
        "import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField } from './types';",
        "import { Input } from './components/ui/input';\n"
        "import { SemanticSelect } from './components/semantic/select';\n"
        "import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField, SemanticSelectOption } from './types';",
    )
    filter_start = base.index("function FilterGrid(")
    filter_end = base.index("\n\nfunction EmptyTable(")
    filter_block = """function FilterGrid({ fields, values, onChange }: { fields: FilterField[]; values: Record<string, string>; onChange: (fieldId: string, value: string) => void }) {
  return (
    <div className="filter-grid">
      {fields.map((field) => {
        const value = values[field.field_id] ?? '';
        const isSelect = selectLikeFieldIds.has(field.field_id);
        if (isSelect) {
          const options: SemanticSelectOption[] = (optionMap[field.field_id] ?? ['鍏ㄩ儴']).map((option) => ({
            label: option,
            value: option,
          }));
          return (
            <SemanticSelect
              key={field.field_id}
              label={field.label}
              value={value || '鍏ㄩ儴'}
              placeholder={field.placeholder}
              options={options}
              onValueChange={(nextValue) => onChange(field.field_id, nextValue)}
            />
          );
        }
        return (
          <label className="filter-field" key={field.field_id}>
            <span className="filter-label">{field.label}</span>
            <Input className="filter-control shadcn-input" type="text" value={value} placeholder={field.placeholder} onChange={(event) => onChange(field.field_id, event.target.value)} />
          </label>
        );
      })}
    </div>
  );
}
"""
    return base[:filter_start] + filter_block + base[filter_end:]


def _app_tsx_shadcn_v3(workbench_path: str, *, icon_library: str) -> str:
    if icon_library != "lucide-react":
        raise ValueError(f"unsupported review_workbench icon library: {icon_library}")
    base = _app_tsx_plain(workbench_path, icon_library=icon_library)
    base = base.replace("  X,\r\n", "")
    base = base.replace("  X,\n", "")
    base = base.replace(
        "import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField } from './types';",
        "import { Input } from './components/ui/input';\n"
        "import { SemanticSelect } from './components/semantic/select';\n"
        "import { SemanticTabs } from './components/semantic/tabs';\n"
        "import type { RuntimeData, SceneSpec, StatItem, ScopeNode, OpenTab, FilterField, SemanticSelectOption } from './types';",
    )
    tab_start = base.index("function TabBar(")
    tab_end = base.index("\n\nfunction FilterGrid(")
    tab_block = """function TabBar({
  tabs,
  activeTabId,
  onActivate,
  onClose,
}: {
  tabs: OpenTab[];
  activeTabId: string;
  onActivate: (tabId: string) => void;
  onClose: (tabId: string) => void;
}) {
  return <SemanticTabs tabs={tabs} activeTabId={activeTabId} onActivate={onActivate} onClose={onClose} />;
}
"""
    base = base[:tab_start] + tab_block + base[tab_end:]
    filter_start = base.index("function FilterGrid(")
    filter_end = base.index("\n\nfunction EmptyTable(")
    filter_block = """function FilterGrid({ fields, values, onChange }: { fields: FilterField[]; values: Record<string, string>; onChange: (fieldId: string, value: string) => void }) {
  return (
    <div className="filter-grid">
      {fields.map((field) => {
        const value = values[field.field_id] ?? '';
        const isSelect = selectLikeFieldIds.has(field.field_id);
        if (isSelect) {
          const options: SemanticSelectOption[] = (optionMap[field.field_id] ?? ['鍏ㄩ儴']).map((option) => ({
            label: option,
            value: option,
          }));
          return (
            <SemanticSelect
              key={field.field_id}
              label={field.label}
              value={value || '鍏ㄩ儴'}
              placeholder={field.placeholder}
              options={options}
              onValueChange={(nextValue) => onChange(field.field_id, nextValue)}
            />
          );
        }
        return (
          <label className="filter-field" key={field.field_id}>
            <span className="filter-label">{field.label}</span>
            <Input className="filter-control shadcn-input" type="text" value={value} placeholder={field.placeholder} onChange={(event) => onChange(field.field_id, event.target.value)} />
          </label>
        );
      })}
    </div>
  );
}
"""
    base = base[:filter_start] + filter_block + base[filter_end:]
    return base


def _ui_input_tsx() -> str:
    return """import * as React from 'react';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { className = '', type = 'text', ...props },
  ref,
) {
  const classes = [className].filter(Boolean).join(' ');
  return <input ref={ref} type={type} className={classes} {...props} />;
});
"""


def _ui_select_tsx() -> str:
    return """import * as SelectPrimitive from '@radix-ui/react-select';
import { Check, ChevronDown } from 'lucide-react';

export const Select = SelectPrimitive.Root;
export const SelectValue = SelectPrimitive.Value;

export function SelectTrigger({
  className = '',
  children,
  ...props
}: SelectPrimitive.SelectTriggerProps & { className?: string }) {
  const classes = ['semantic-select-trigger', className].filter(Boolean).join(' ');
  return (
    <SelectPrimitive.Trigger className={classes} {...props}>
      {children}
      <SelectPrimitive.Icon asChild>
        <ChevronDown className="semantic-select-chevron" strokeWidth={1.8} />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
}

export function SelectContent({
  className = '',
  children,
  position = 'popper',
  ...props
}: SelectPrimitive.SelectContentProps & { className?: string }) {
  const classes = ['semantic-select-content', className].filter(Boolean).join(' ');
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content className={classes} position={position} {...props}>
        <SelectPrimitive.Viewport className="semantic-select-viewport">{children}</SelectPrimitive.Viewport>
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

export function SelectItem({
  className = '',
  children,
  ...props
}: SelectPrimitive.SelectItemProps & { className?: string }) {
  const classes = ['semantic-select-item', className].filter(Boolean).join(' ');
  return (
    <SelectPrimitive.Item className={classes} {...props}>
      <span className="semantic-select-item-indicator">
        <SelectPrimitive.ItemIndicator>
          <Check className="semantic-select-check" strokeWidth={2} />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}
"""


def _semantic_select_tsx() -> str:
    return """import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import type { SemanticSelectOption } from '../../types';

type SemanticSelectProps = {
  label: string;
  value: string;
  placeholder: string;
  options: SemanticSelectOption[];
  onValueChange?: (value: string) => void;
};

export function SemanticSelect({
  label,
  value,
  placeholder,
  options,
  onValueChange,
}: SemanticSelectProps) {
  return (
    <label className="filter-field">
      <span className="filter-label">{label}</span>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger aria-label={label}>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
"""


def _semantic_tabs_tsx() -> str:
    return """import { FileText, X } from 'lucide-react';
import type { OpenTab } from '../../types';

type SemanticTabsProps = {
  tabs: OpenTab[];
  activeTabId: string;
  onActivate: (tabId: string) => void;
  onClose: (tabId: string) => void;
};

export function SemanticTabs({
  tabs,
  activeTabId,
  onActivate,
  onClose,
}: SemanticTabsProps) {
  return (
    <div className="tab-bar">
      {tabs.map((tab) => {
        const active = tab.tab_id === activeTabId;
        const closable = Boolean(tab.item_id);
        return (
          <div className={`tab-chip ${active ? 'tab-chip-active' : ''}`} key={tab.tab_id}>
            <button className="tab-chip-main" type="button" onClick={() => onActivate(tab.tab_id)}>
              <FileText className="tab-chip-icon" strokeWidth={1.7} />
              <span className="tab-chip-text">{tab.title}</span>
            </button>
            {closable ? (
              <button
                aria-label={`关闭 ${tab.title}`}
                className="tab-chip-closer"
                type="button"
                onClick={() => onClose(tab.tab_id)}
              >
                <X className="tab-chip-close-icon" strokeWidth={1.9} />
              </button>
            ) : null}
          </div>
        );
      })}
      <div aria-hidden="true" className="tab-bar-spacer" />
    </div>
  );
}
"""


def _styles_css(accent: str, brand: str) -> str:
    return """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --accent: __ACCENT__;
  --brand-text: __BRAND__;
  --surface: #f4f6fa;
  --panel: #ffffff;
  --panel-soft: #f6f8fb;
  --line: #dde4ef;
  --line-soft: #edf2f7;
  --text: #1f2937;
  --muted: #6b7280;
  --muted-soft: #94a3b8;
  --shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

:root[data-theme='dark'] {
  --surface: #1e1e1e;
  --panel: #252526;
  --panel-soft: #2d2d30;
  --line: #3b3b3b;
  --line-soft: #333333;
  --text: #e7edf5;
  --muted: #a3adba;
  --muted-soft: #7f8a98;
  --shadow: 0 18px 42px rgba(0, 0, 0, 0.28);
}

* {
  box-sizing: border-box;
}

html,
body,
#root {
  margin: 0;
  min-height: 100%;
  height: 100%;
  overflow: hidden;
}

body {
  background: linear-gradient(180deg, #f7f9fc 0%, #f2f5f9 48%, #eef2f6 100%);
  color: var(--text);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

:root[data-theme='dark'] body {
  background: #1e1e1e;
}

button,
input,
select {
  font: inherit;
}

html {
  color-scheme: light;
}

:root[data-theme='dark'] html {
  color-scheme: dark;
}

:root[data-theme-switching='true'] *,
:root[data-theme-switching='true'] *::before,
:root[data-theme-switching='true'] *::after {
  transition: none !important;
  animation: none !important;
}

button {
  -webkit-tap-highlight-color: transparent;
}

.platform-app {
  height: 100vh;
  padding: 8px;
  overflow: hidden;
}

.platform-shell {
  height: calc(100vh - 16px);
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: 48px minmax(0, 1fr) 31px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(221, 229, 239, 0.9);
  border-radius: 18px;
  overflow: hidden;
}

:root[data-theme='dark'] .platform-shell {
  background: #232427;
  border-color: #32353a;
}

.platform-topbar {
  grid-column: 1;
  grid-row: 1;
  display: grid;
  grid-template-columns: 274px minmax(0, 1fr);
  min-height: 48px;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 252, 0.96));
}

:root[data-theme='dark'] .platform-topbar {
  border-bottom-color: #34383d;
  background: linear-gradient(180deg, #24262a, #212327);
}

.platform-topbar-brand {
  grid-column: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 0 14px 0 12px;
}

.platform-topbar-main {
  grid-column: 2;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  min-width: 0;
  padding: 0 10px 0 14px;
}

.platform-body {
  grid-column: 1;
  grid-row: 2;
  min-height: 0;
  display: grid;
  grid-template-columns: 274px 8px minmax(720px, 1fr);
}


.sidebar-shell {
  grid-column: 1;
  grid-row: 1;
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  min-height: 0;
  overflow: hidden;
  background: var(--panel);
}

:root[data-theme='dark'] .sidebar-shell {
  background: #242529;
}

.shell-divider {
  grid-column: 2;
  grid-row: 1;
  border: 0;
  background: transparent;
  padding: 0;
  margin: 0;
  cursor: col-resize;
  position: relative;
  transition: background-color 140ms ease;
}

.shell-divider-line {
  position: absolute;
  inset: 0 auto 0 50%;
  width: 1px;
  transform: translateX(-50%);
  border-radius: 999px;
  background: #dfe7f2;
  transition: background-color 140ms ease, width 140ms ease;
}

.shell-divider:hover,
.shell-divider-active {
  background: rgba(37, 99, 235, 0.04);
}

.shell-divider:hover .shell-divider-line,
.shell-divider-active .shell-divider-line {
  width: 3px;
  background: rgba(37, 99, 235, 0.56);
}

:root[data-theme='dark'] .shell-divider {
  background: transparent;
}

:root[data-theme='dark'] .shell-divider-line {
  background: #39424e;
}

:root[data-theme='dark'] .shell-divider:hover,
:root[data-theme='dark'] .shell-divider-active {
  background: rgba(96, 165, 250, 0.04);
}

:root[data-theme='dark'] .shell-divider:hover .shell-divider-line,
:root[data-theme='dark'] .shell-divider-active .shell-divider-line {
  background: rgba(96, 165, 250, 0.68);
}

.icon-rail {
  border-right: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 6px 10px;
  background: rgba(248, 250, 252, 0.85);
}

:root[data-theme='dark'] .icon-rail {
  background: #222428;
}

.rail-button,
.rail-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  display: grid;
  place-items: center;
  cursor: pointer;
}

.rail-button-active,
.rail-button:hover,
.rail-avatar:hover {
  border-color: rgba(37, 99, 235, 0.18);
  background: rgba(37, 99, 235, 0.08);
  color: var(--accent);
}

:root[data-theme='dark'] .rail-button-active,
:root[data-theme='dark'] .rail-button:hover,
:root[data-theme='dark'] .rail-avatar:hover {
  border-color: #4f93eb;
  background: rgba(37, 99, 235, 0.22);
  color: #8fc0ff;
}

.rail-icon,
.rail-avatar-icon,
.panel-icon,
.square-tool-icon,
.topbar-search-icon,
.toggle-pill-icon,
.scope-node-icon,
.tab-chip-icon,
.tab-chip-close,
.empty-icon-file {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.rail-spacer {
  flex: 1;
}

.rail-avatar {
  border-radius: 999px;
  border-color: var(--line);
  background: var(--panel);
}

:root[data-theme='dark'] .rail-avatar {
  background: #252526;
  border-color: #3f444c;
}

.sidebar-panel {
  display: grid;
  height: 100%;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  grid-template-rows: minmax(156px, 1fr) 8px minmax(188px, 1fr);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px 9px;
}

.sidebar-brand-mark {
  position: relative;
  width: 24px;
  height: 16px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: linear-gradient(135deg, #0b63ce, #2877dd);
}

.sidebar-brand-orbit {
  position: absolute;
  inset: 3px 5px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.92);
}

.sidebar-brand-wave {
  position: absolute;
  width: 16px;
  height: 16px;
  right: -4px;
  top: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
}

.sidebar-brand-copy strong {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

:root[data-theme='dark'] .sidebar-brand-copy strong {
  color: #f4f7fb;
}

.sidebar-directory {
  flex: 1;
  padding: 8px 0 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.sidebar-directory-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px 8px;
  margin-bottom: 0;
  font-size: 14px;
}

:root[data-theme='dark'] .sidebar-directory-head {
  color: #f3f6fb;
}

.sidebar-head-actions {
  display: flex;
  gap: 6px;
}

.panel-icon-button,
.square-tool {
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--muted);
  border-radius: 7px;
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  cursor: pointer;
  padding: 0;
}

:root[data-theme='dark'] .panel-icon-button,
:root[data-theme='dark'] .square-tool {
  background: #2d2d30;
  border-color: #45474d;
  color: #acb6c3;
}

.panel-icon-button:hover,
.square-tool:hover {
  border-color: var(--accent);
  color: var(--accent);
}

:root[data-theme='dark'] .panel-icon-button:hover,
:root[data-theme='dark'] .square-tool:hover {
  background: #33373d;
  border-color: #5b95ee;
  color: #8ab8ff;
}

.panel-icon-rotate {
  animation: icon-spin 0.8s linear;
}

.scope-tree {
  display: grid;
  gap: 2px;
  padding: 0 6px 6px;
  overflow: auto;
}

.scope-node {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334155;
  font-size: 13px;
  padding: 7px 8px;
  border-radius: 7px;
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
  transition: background-color 120ms ease, color 120ms ease;
}

:root[data-theme='dark'] .scope-node {
  color: #bcc6d3;
}

.scope-node:hover {
  background: rgba(37, 99, 235, 0.06);
  color: #1d4ed8;
}

:root[data-theme='dark'] .scope-node:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #86b6ff;
}

.scope-node-active {
  background: rgba(37, 99, 235, 0.06);
  color: var(--accent);
  font-weight: 600;
}

:root[data-theme='dark'] .scope-node-active {
  background: rgba(59, 130, 246, 0.18);
  color: #98c2ff;
  box-shadow: inset 0 0 0 1px rgba(125, 179, 255, 0.24);
}

.scope-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-divider {
  border: 0;
  background: transparent;
  padding: 0;
  margin: 0;
  cursor: row-resize;
  position: relative;
  transition: background-color 140ms ease;
}

.sidebar-divider-line {
  position: absolute;
  inset: 50% 0 auto;
  height: 1px;
  transform: translateY(-50%);
  border-radius: 999px;
  background: #dfe7f2;
  transition: background-color 140ms ease, height 140ms ease;
}

.sidebar-divider:hover,
.sidebar-divider-active {
  background: rgba(37, 99, 235, 0.04);
}

.sidebar-divider:hover .sidebar-divider-line,
.sidebar-divider-active .sidebar-divider-line {
  height: 3px;
  background: rgba(37, 99, 235, 0.56);
}

:root[data-theme='dark'] .sidebar-divider {
  background: transparent;
}

:root[data-theme='dark'] .sidebar-divider:hover,
:root[data-theme='dark'] .sidebar-divider-active {
  background: rgba(96, 165, 250, 0.04);
}

:root[data-theme='dark'] .sidebar-divider-line {
  background: #39424e;
}

:root[data-theme='dark'] .sidebar-divider:hover .sidebar-divider-line,
:root[data-theme='dark'] .sidebar-divider-active .sidebar-divider-line {
  background: rgba(96, 165, 250, 0.68);
}

.sidebar-overview {
  background: rgba(248, 250, 252, 0.74);
  padding: 12px 10px 14px;
  min-height: 0;
  overflow: auto;
}

:root[data-theme='dark'] .sidebar-overview {
  background: #2a2a2c;
}

.overview-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}

.stat-list {
  display: grid;
  gap: 6px;
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 13px;
  gap: 10px;
}

.stat-label {
  color: var(--muted);
}

.stat-value {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  font-size: 13px;
  line-height: 1;
  background: #f8fafc;
  border: 1px solid #d9e2ec;
  color: #64748b;
}

:root[data-theme='dark'] .stat-value {
  background: #232428;
  border-color: #40444c;
  color: #d5ddeb;
}

.stat-item[data-stat-kind='classified_files'] .stat-value,
.footer-stat[data-stat-kind='classified_files'] .footer-stat-value {
  color: #0f766e;
}

.stat-item[data-stat-kind='unclassified_files'] .stat-value,
.footer-stat[data-stat-kind='unclassified_files'] .footer-stat-value {
  color: #4f46e5;
}

.stat-item[data-stat-kind='pending_review'] .stat-value,
.footer-stat[data-stat-kind='pending_review'] .footer-stat-value {
  color: #ea580c;
}

.stat-item[data-stat-kind='reviewed'] .stat-value,
.footer-stat[data-stat-kind='reviewed'] .footer-stat-value {
  color: #0284c7;
}

.stat-item[data-stat-kind='unresolved'] .stat-value,
.footer-stat[data-stat-kind='unresolved'] .footer-stat-value {
  color: #e11d48;
}

.workspace-shell {
  grid-column: 3;
  grid-row: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: #f5f7fb;
}

:root[data-theme='dark'] .workspace-shell {
  background: #222427;
}

.platform-footer {
  grid-column: 1;
  grid-row: 3;
  height: 31px;
  min-width: 0;
  min-height: 31px;
  border-top: 1px solid rgba(219, 227, 239, 0.9);
  background: #ffffff;
  overflow: hidden;
}

:root[data-theme='dark'] .platform-footer {
  background: #252526;
  border-top-color: #3a3a3a;
}

.workspace-card {
  margin: 0;
}

.topbar-search-wrap {
  display: flex;
  justify-content: center;
  min-width: 0;
}

.topbar-search {
  width: min(100%, 640px);
  height: 32px;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff, #fcfdff);
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92);
  transition: border-color 120ms ease, box-shadow 120ms ease;
}

:root[data-theme='dark'] .topbar-search {
  border-color: #4a4a4a;
  background: linear-gradient(180deg, #323236, #2c2c30);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03), 0 1px 0 rgba(0, 0, 0, 0.18);
}

.topbar-search:focus-within {
  border-color: #b8cbef;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

:root[data-theme='dark'] .topbar-search:focus-within {
  border-color: #5b95ee;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
}

.topbar-search-input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text);
  font-size: 13px;
}

.topbar-search-input::placeholder {
  color: var(--muted-soft);
}

.topbar-tools {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  align-items: center;
  min-width: 0;
}

.toggle-pill {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 999px;
  height: 24px;
  min-width: 48px;
  padding: 0 5px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
  transition: border-color 120ms ease, background-color 120ms ease;
}

:root[data-theme='dark'] .toggle-pill {
  background: #2d2d30;
  border-color: #45474d;
}

.toggle-pill:hover {
  border-color: #bfd3f8;
  background: #f8fbff;
}

:root[data-theme='dark'] .toggle-pill:hover {
  border-color: #5b95ee;
  background: #33373d;
}

.toggle-pill-track {
  width: 28px;
  height: 12px;
  display: flex;
  align-items: center;
  padding: 0 2px;
  border-radius: 999px;
  background: #eef2f7;
}

:root[data-theme='dark'] .toggle-pill-track {
  background: #51555d;
}

.toggle-pill-thumb {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #cbd5e1;
  transition: transform 160ms ease;
}

:root[data-theme='dark'] .toggle-pill-thumb {
  background: #d1d5db;
}

.toggle-pill-thumb-active {
  transform: translateX(14px);
  background: var(--accent);
}

.toggle-pill-icon {
  width: 12px;
  height: 12px;
  color: var(--muted);
}

.tab-bar {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0;
  min-height: 34px;
  border: 0;
  border-radius: 0;
  scrollbar-width: thin;
  position: relative;
  background: linear-gradient(180deg, #fbfcfe, #f7f9fc);
  z-index: 2;
}

:root[data-theme='dark'] .tab-bar {
  background: linear-gradient(180deg, #2b2e33, #282b30);
}

.tab-bar::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 1px;
  background: rgba(255, 255, 255, 0.72);
  pointer-events: none;
}

:root[data-theme='dark'] .tab-bar::before {
  background: rgba(255, 255, 255, 0.04);
}

.tab-bar::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background: #e4ebf5;
  pointer-events: none;
}

:root[data-theme='dark'] .tab-bar::after {
  background: #343940;
}

.tab-chip {
  border: 0;
  border-right: 1px solid #edf2f8;
  background: transparent;
  color: #5b6b80;
  border-radius: 0;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 0;
  min-width: 0;
  min-height: 33px;
  margin-right: 0;
  position: relative;
  box-shadow: none;
  transition: background-color 120ms ease, color 120ms ease, border-color 120ms ease;
}

:root[data-theme='dark'] .tab-chip {
  color: #b8c3d1;
  border-right-color: #31363d;
  min-height: 33px;
}

.tab-chip:first-child {
  border-top-left-radius: 0;
}

.tab-bar > .tab-chip:last-of-type {
  border-right: 0;
}

.tab-bar-spacer {
  flex: 1 0 36px;
  min-height: 33px;
  background: transparent;
}

.tab-chip:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #1d4ed8;
}

:root[data-theme='dark'] .tab-chip:hover {
  background: rgba(255, 255, 255, 0.03);
  color: #eef5ff;
}

.tab-chip-main {
  border: 0;
  background: transparent;
  color: inherit;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  height: 100%;
  padding: 6px 10px 5px 12px;
  cursor: pointer;
  outline: none;
}

:root[data-theme='dark'] .tab-chip-main {
  padding: 6px 10px 5px 12px;
}

.tab-chip-active {
  background: rgba(255, 255, 255, 0.9);
  color: #2563eb;
  border-left: 1px solid #dfe7f3;
  border-right: 1px solid #dfe7f3;
  border-top: 0;
  margin-left: -1px;
  margin-top: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
  z-index: 3;
}

:root[data-theme='dark'] .tab-chip-active {
  background: #30343a;
  color: #94c0ff;
  border-left-color: #404851;
  border-right-color: #404851;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.tab-chip:first-child.tab-chip-active {
  margin-left: 0;
  border-left: 0;
}

.tab-chip-active::after {
  content: '';
  position: absolute;
  left: -1px;
  right: -1px;
  top: 0;
  height: 2px;
  border-radius: 0;
  background: #2563eb;
}

:root[data-theme='dark'] .tab-chip-active::after {
  background: #7eb6ff;
}

.tab-chip-active::before {
  content: '';
  position: absolute;
  left: -1px;
  right: -1px;
  bottom: -1px;
  height: 3px;
  background: #ffffff;
}

:root[data-theme='dark'] .tab-chip-active::before {
  background: #2f3338;
}

.tab-chip-active:hover {
  background: rgba(255, 255, 255, 0.94);
  border-left-color: #d5e1f3;
  border-right-color: #d5e1f3;
  color: #2563eb;
}

:root[data-theme='dark'] .tab-chip-active:hover {
  background: #32363d;
  color: #a2c9ff;
  border-left-color: #475362;
  border-right-color: #475362;
}

.tab-chip-text {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 126px;
  font-size: 13px;
}

.tab-chip-closer {
  width: 24px;
  height: 24px;
  margin-right: 5px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: currentColor;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
  opacity: 0.84;
  transition: background-color 120ms ease, color 120ms ease, opacity 120ms ease;
}

.tab-chip-closer:hover {
  background: rgba(37, 99, 235, 0.16);
  color: #1d4ed8;
  opacity: 1;
}

:root[data-theme='dark'] .tab-chip-closer:hover {
  background: rgba(59, 130, 246, 0.24);
  color: #a8cdff;
}

.tab-chip-close-icon {
  width: 13px;
  height: 13px;
}

.workspace-card {
  background: #ffffff;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  display: grid;
  gap: 0;
  grid-template-rows: auto auto minmax(0, 1fr);
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

:root[data-theme='dark'] .workspace-card {
  background: #2a2d32;
  box-shadow: none;
}

.filter-panel {
  border: 0;
  border-bottom: 1px solid #e5ecf5;
  border-radius: 0;
  background: transparent;
  padding: 8px 12px 6px;
  box-shadow: none;
}

:root[data-theme='dark'] .filter-panel {
  background: transparent;
  border-bottom-color: #343941;
  box-shadow: none;
}

.filter-grid {
  display: grid;
  grid-template-columns: 1.12fr 1fr 1.12fr 1fr 1fr 1fr 1.16fr;
  gap: 5px 8px;
}

.filter-field {
  display: grid;
  gap: 5px;
}

.filter-label {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.2;
}

:root[data-theme='dark'] .filter-label {
  color: #afb8c4;
}

.filter-control {
  min-height: 28px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  padding: 0 8px;
  color: var(--text);
  outline: none;
  transition: border-color 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
}

:root[data-theme='dark'] .filter-control {
  background: linear-gradient(180deg, #31343a, #2d3035);
  border-color: #3e434b;
  color: #edf2f8;
}

.filter-control::placeholder {
  color: #9ca3af;
}

:root[data-theme='dark'] .filter-control::placeholder {
  color: #8a94a2;
}

.filter-control:focus {
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

:root[data-theme='dark'] .filter-control:focus {
  border-color: rgba(96, 165, 250, 0.82);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
}

.shadcn-input {
  min-height: 28px;
}

.semantic-select-trigger {
  min-height: 28px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  padding: 0 10px;
  color: var(--text);
  outline: none;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  transition: border-color 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
}

:root[data-theme='dark'] .semantic-select-trigger {
  background: linear-gradient(180deg, #31343a, #2d3035);
  border-color: #3e434b;
  color: #edf2f8;
}

.semantic-select-trigger[data-placeholder] {
  color: #9ca3af;
}

:root[data-theme='dark'] .semantic-select-trigger[data-placeholder] {
  color: #8a94a2;
}

.semantic-select-trigger:focus-visible {
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

:root[data-theme='dark'] .semantic-select-trigger:focus-visible {
  border-color: rgba(96, 165, 250, 0.82);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
}

.semantic-select-chevron {
  width: 14px;
  height: 14px;
  color: #94a3b8;
  flex: 0 0 auto;
}

:root[data-theme='dark'] .semantic-select-chevron {
  color: #94a2b8;
}

.semantic-select-content {
  z-index: 50;
  min-width: var(--radix-select-trigger-width);
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--panel);
  color: var(--text);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.14);
}

:root[data-theme='dark'] .semantic-select-content {
  border-color: #4a4d53;
  background: #2d2d30;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.32);
}

.semantic-select-viewport {
  padding: 6px;
}

.semantic-select-item {
  position: relative;
  min-height: 32px;
  display: flex;
  align-items: center;
  border-radius: 8px;
  padding: 0 10px 0 32px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  user-select: none;
  outline: none;
}

.semantic-select-item[data-highlighted] {
  background: rgba(37, 99, 235, 0.08);
  color: var(--accent);
}

:root[data-theme='dark'] .semantic-select-item[data-highlighted] {
  background: rgba(59, 130, 246, 0.2);
  color: #9bc4ff;
}

.semantic-select-item-indicator {
  position: absolute;
  left: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.semantic-select-check {
  width: 14px;
  height: 14px;
}

.filter-select-wrap {
  position: relative;
}

.filter-select {
  appearance: none;
  padding-right: 28px;
}

.filter-select option,
.filter-select optgroup {
  background: #ffffff;
  color: #1f2937;
}

:root[data-theme='dark'] .filter-select {
  color-scheme: dark;
}

:root[data-theme='dark'] .filter-select option,
:root[data-theme='dark'] .filter-select optgroup {
  background: #2f3136;
  color: #eef3fa;
}

.filter-select-wrap::after {
  content: '';
  position: absolute;
  right: 12px;
  top: 50%;
  width: 7px;
  height: 7px;
  border-right: 1.5px solid #9ca3af;
  border-bottom: 1.5px solid #9ca3af;
  transform: translateY(-65%) rotate(45deg);
  pointer-events: none;
}

:root[data-theme='dark'] .filter-select-wrap::after {
  border-right-color: #8b95a3;
  border-bottom-color: #8b95a3;
}

.scope-summary-row {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #64748b;
  font-size: 13px;
  min-height: 18px;
}

:root[data-theme='dark'] .scope-summary-row,
:root[data-theme='dark'] .scope-summary-text {
  color: #a7b0bc;
}

.scope-summary-text {
  color: #6b7280;
}

.link-button {
  border: 0;
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  padding: 0 2px;
  min-height: 18px;
  border-radius: 0;
  font-size: 13px;
  transition: border-color 120ms ease, background-color 120ms ease, color 120ms ease;
}

:root[data-theme='dark'] .link-button {
  color: #7fb3ff;
}

.link-button:hover {
  background: transparent;
  color: #1d4ed8;
}

:root[data-theme='dark'] .link-button:hover {
  background: transparent;
  color: #9bc4ff;
}

.result-panel {
  border: 0;
  border-radius: 0;
  background: transparent;
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
  box-shadow: none;
  padding: 8px 12px 12px;
}

:root[data-theme='dark'] .result-panel {
  background: transparent;
  box-shadow: none;
}

.table-shell {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  min-height: 0;
  border: 1px solid #e3eaf4;
  border-radius: 8px;
  background: #ffffff;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
}

.result-table th {
  text-align: left;
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 12px;
  border-bottom: 1px solid var(--line);
  font-weight: 600;
  height: 30px;
}

:root[data-theme='dark'] .result-table th {
  color: #aeb7c2;
  background: #31343a;
  border-bottom-color: #3c424a;
}

:root[data-theme='dark'] .table-shell {
  border-color: #353a42;
  background: #2c2f34;
}

.result-table td {
  padding: 11px 12px;
}

.empty-cell {
  height: auto;
  vertical-align: middle;
}

.empty-state {
  min-height: 300px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 6px;
  color: #64748b;
  text-align: center;
}

:root[data-theme='dark'] .empty-state {
  color: #9da9b8;
}

.empty-icon {
  position: relative;
  width: 70px;
  height: 70px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: radial-gradient(circle at top, rgba(37, 99, 235, 0.16), rgba(37, 99, 235, 0.06));
}

:root[data-theme='dark'] .empty-icon {
  background: radial-gradient(circle at top, rgba(59, 130, 246, 0.22), rgba(37, 99, 235, 0.08));
}

.empty-icon-file {
  width: 22px;
  height: 22px;
  color: #60a5fa;
}

.empty-icon-badge {
  position: absolute;
  top: 10px;
  right: 8px;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #4f46e5;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.95);
}

.empty-state strong {
  font-size: 16px;
  color: #334155;
}

:root[data-theme='dark'] .empty-state strong {
  color: #e5edf8;
}

.empty-state p {
  max-width: 360px;
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
}

:root[data-theme='dark'] .empty-state p {
  color: #a7b3c0;
}

.inspection-shell {
  display: grid;
  gap: 14px;
  min-height: 100%;
}

.inspection-header {
  display: grid;
  gap: 8px;
  padding: 4px 0 0;
}

.inspection-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.inspection-title {
  margin: 0;
  font-size: 16px;
  line-height: 1.3;
  color: #1f2937;
}

.inspection-status {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
}

.inspection-note {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.inspection-body {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 14px;
  min-height: 320px;
}

.inspection-block-list {
  display: grid;
  gap: 8px;
  align-content: start;
}

.inspection-block {
  border: 1px solid #dfe7f2;
  border-radius: 10px;
  background: #ffffff;
  padding: 10px 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
  cursor: pointer;
  transition: border-color 120ms ease, background-color 120ms ease, box-shadow 120ms ease;
}

.inspection-block:hover {
  border-color: rgba(37, 99, 235, 0.32);
  background: #f8fbff;
}

.inspection-block-active {
  border-color: rgba(37, 99, 235, 0.44);
  background: #eff6ff;
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.12);
}

.inspection-block-indicator {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  margin-top: 4px;
  flex: 0 0 auto;
}

.inspection-block-indicator-ready {
  background: #10b981;
}

.inspection-block-indicator-focus {
  background: #2563eb;
}

.inspection-block-indicator-pending {
  background: #f59e0b;
}

.inspection-block-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.inspection-block-copy strong {
  font-size: 13px;
  color: #1f2937;
}

.inspection-block-copy span {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.inspection-detail {
  display: grid;
  grid-template-rows: auto auto auto;
  align-content: start;
  gap: 12px;
}

.inspection-detail-card,
.inspection-feedback {
  border: 1px solid #e3eaf4;
  border-radius: 10px;
  background: #ffffff;
  padding: 14px 16px;
}

.inspection-detail-head {
  display: grid;
  gap: 4px;
  margin-bottom: 10px;
}

.inspection-detail-head strong,
.inspection-feedback strong {
  font-size: 14px;
  color: #1f2937;
}

.inspection-detail-head span {
  font-size: 12px;
  color: #64748b;
}

.inspection-detail-copy,
.inspection-feedback p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #475569;
}

.inspection-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.inspection-action-button {
  border: 1px solid #cfe0ff;
  border-radius: 8px;
  background: #f8fbff;
  color: #1d4ed8;
  min-height: 32px;
  padding: 0 12px;
  cursor: pointer;
}

.inspection-action-button:hover {
  border-color: #93c5fd;
  background: #eff6ff;
}

:root[data-theme='dark'] .inspection-title {
  color: #e5edf8;
}

:root[data-theme='dark'] .inspection-status {
  background: rgba(59, 130, 246, 0.18);
  color: #9bc4ff;
}

:root[data-theme='dark'] .inspection-note {
  color: #a7b3c0;
}

:root[data-theme='dark'] .inspection-block {
  border-color: #3b434c;
  background: #2d3035;
}

:root[data-theme='dark'] .inspection-block:hover {
  border-color: #4b6b95;
  background: #30343a;
}

:root[data-theme='dark'] .inspection-block-active {
  border-color: #53739e;
  background: #313743;
  box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.16);
}

:root[data-theme='dark'] .inspection-block-copy strong {
  color: #e5edf8;
}

:root[data-theme='dark'] .inspection-block-copy span {
  color: #a7b3c0;
}

:root[data-theme='dark'] .inspection-detail-card,
:root[data-theme='dark'] .inspection-feedback {
  border-color: #39414a;
  background: #2c2f34;
}

:root[data-theme='dark'] .inspection-detail-head strong,
:root[data-theme='dark'] .inspection-feedback strong {
  color: #e5edf8;
}

:root[data-theme='dark'] .inspection-detail-head span {
  color: #a7b3c0;
}

:root[data-theme='dark'] .inspection-detail-copy,
:root[data-theme='dark'] .inspection-feedback p {
  color: #c0cad6;
}

:root[data-theme='dark'] .inspection-action-button {
  border-color: #42536b;
  background: #2f3742;
  color: #a7cbff;
}

:root[data-theme='dark'] .inspection-action-button:hover {
  border-color: #5a7ca8;
  background: #354153;
}

.workspace-footer {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-start;
  height: 30px;
  min-height: 30px;
  padding: 0 8px 1px;
  width: 100%;
  overflow: hidden;
  color: #71717a;
  font-size: 12px;
  line-height: 1;
}

:root[data-theme='dark'] .workspace-footer {
  color: #a8b0bb;
  background: #252526;
}

.footer-stat {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  flex: 0 0 auto;
  white-space: nowrap;
}

.footer-stat-label {
  color: #71717a;
  font-weight: 400;
}

:root[data-theme='dark'] .footer-stat-label {
  color: #b4bcc7;
}

.footer-stat-separator {
  color: #a1a1aa;
}

:root[data-theme='dark'] .footer-stat-separator {
  color: #7d8691;
}

.footer-stat-value {
  color: #52525b;
  font-weight: 600;
}

:root[data-theme='dark'] .footer-stat-value {
  color: #eef3fa;
}

:root[data-theme='dark'] .footer-stat[data-stat-kind='classified_files'] .footer-stat-value {
  color: #63d7a2;
}

:root[data-theme='dark'] .footer-stat[data-stat-kind='unclassified_files'] .footer-stat-value {
  color: #9a8cff;
}

:root[data-theme='dark'] .footer-stat[data-stat-kind='pending_review'] .footer-stat-value {
  color: #ffb454;
}

:root[data-theme='dark'] .footer-stat[data-stat-kind='reviewed'] .footer-stat-value {
  color: #7cc7ff;
}

:root[data-theme='dark'] .footer-stat[data-stat-kind='unresolved'] .footer-stat-value {
  color: #ff7aa2;
}

@keyframes icon-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(180deg); }
}

@media (max-width: 1200px) {
  .filter-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .platform-app {
    padding: 0;
  }

  .platform-shell {
    min-height: 100vh;
    border-radius: 0;
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr) auto;
  }

  .sidebar-shell {
    grid-column: 1;
    grid-row: 2;
    width: 100%;
    grid-template-columns: 44px minmax(0, 1fr);
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .platform-body {
    grid-column: 1;
    grid-row: 2;
    grid-template-columns: 1fr;
  }

  .shell-divider {
    display: none;
  }

  .workspace-shell {
    grid-column: 1;
    grid-row: 2;
  }

  .platform-footer {
    grid-column: 1;
    grid-row: 3;
  }

  .platform-topbar {
    grid-column: 1;
    grid-template-columns: minmax(0, 1fr);
  }

  .platform-topbar-brand {
    display: none;
  }

  .platform-topbar-main {
    grid-column: 1;
    padding: 0 8px;
  }

  .workspace-card {
    margin: 0;
  }

  .topbar-search-wrap {
    justify-content: flex-start;
  }

  .topbar-tools {
    justify-content: flex-end;
  }

  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-footer {
    margin: 0;
    flex-wrap: wrap;
    overflow: auto;
    height: auto;
    min-height: 30px;
  }
}
""".replace("__ACCENT__", accent).replace("__BRAND__", brand)

def _frontend_app_readme(*, package_manager: str) -> str:
    install_command = "pnpm install" if package_manager == "pnpm" else "npm install"
    dev_command = "pnpm dev" if package_manager == "pnpm" else "npm run dev"
    return f"""# Generated Frontend App

This directory is derived from the project's canonical/runtime exports.

Do not treat it as a second source of truth.
Regenerate it via:

```bash
uv run python scripts/materialize_project.py --project-file <project.toml>
```

If rematerialization changes `package.json`, stop any running dev server in this directory
and reinstall dependencies before starting it again. Do not mix package managers in this
generated directory.

Then run it with Node tooling:

```bash
{install_command}
{dev_command}
```
"""


def _clear_managed_frontend_outputs(output_dir: Path) -> None:
    managed_roots = (
        output_dir / "dist",
        output_dir / "index.html",
        output_dir / "package.json",
        output_dir / "package-lock.json",
        output_dir / "pnpm-lock.yaml",
        output_dir / "postcss.config.js",
        output_dir / "README.md",
        output_dir / "tailwind.config.ts",
        output_dir / "tsconfig.json",
        output_dir / "tsconfig.node.json",
        output_dir / "vite.config.ts",
        output_dir / "src",
    )
    for path in managed_roots:
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path, onerror=_remove_readonly)
            continue
        try:
            path.unlink(missing_ok=True)
        except PermissionError:
            _remove_readonly(os.unlink, str(path), (PermissionError, PermissionError(), None))


def _remove_readonly(
    func: Any,
    path: str,
    _: tuple[type[BaseException], BaseException, TracebackType | None],
) -> None:
    if not os.path.exists(path):
        return
    os.chmod(path, stat.S_IWRITE)
    try:
        func(path)
    except FileNotFoundError:
        return


def _validate_generated_frontend_app(output_dir: Path) -> None:
    required_files = (
        output_dir / "package.json",
        output_dir / "tsconfig.json",
        output_dir / "vite.config.ts",
        output_dir / "tailwind.config.ts",
        output_dir / "src" / "main.tsx",
        output_dir / "src" / "App.tsx",
        output_dir / "src" / "generated" / "runtime-data.json",
    )
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"generated frontend app is incomplete: {joined}")

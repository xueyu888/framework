from __future__ import annotations

import json
import os
import stat
import shutil
from pathlib import Path
from types import TracebackType
from typing import Any

from project_runtime.models import ProjectRuntimeAssembly


SUPPORTED_REVIEW_WORKBENCH_RENDERERS = {
    "review_workbench_react_vite_tailwind_ts_strict_v1",
}


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
    review_workbench = assembly.require_runtime_export("review_workbench_domain_spec")
    backend_spec = assembly.require_runtime_export("backend_service_spec")
    implementation = frontend_spec["ui"]["implementation"]
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
            package_manager=str(implementation.get("package_manager", "pnpm")),
            icon_library=str(implementation.get("icon_library", "lucide-react")),
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
        "src/App.tsx": _app_tsx(route_contract["workbench"], icon_library=str(implementation.get("icon_library", "lucide-react"))),
        "src/types.ts": _types_ts(),
        "README.md": _frontend_app_readme(package_manager=str(implementation.get("package_manager", "pnpm"))),
    }
    for relative_path, content in files.items():
        path = output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _validate_generated_frontend_app(output_dir)


def _package_json(project_id: str, *, package_manager: str, icon_library: str) -> str:
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
        "dependencies": {
            "react": "^19.1.0",
            "react-dom": "^19.1.0",
            icon_library: "^0.542.0",
        },
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


def _app_tsx(workbench_path: str, *, icon_library: str) -> str:
    if icon_library != "lucide-react":
        raise ValueError(f"unsupported review_workbench icon library: {icon_library}")
    return """import { useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  FileText,
  FolderTree,
  GitBranch,
  History,
  Maximize2,
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

export default function App() {
  const platform = data.review_workbench_domain_spec.platform;
  const activeScene = sceneById(platform.default_scene_id);
  const activeScope = activeScene.scope_tree.find((node) => asBool(node.active));
  const bottomStats = platform.platform_stats ?? activeScene.scope_stats;

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
  const [darkMode, setDarkMode] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? 'dark' : 'light';
    return () => {
      delete document.documentElement.dataset.theme;
    };
  }, [darkMode]);

  useEffect(() => {
    setOpenTabs(defaultTabs);
    setActiveTabId(defaultActiveTabId);
  }, [defaultActiveTabId, defaultTabs]);

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

  return (
    <div className="platform-app">
      <div className="platform-shell">
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

          <section className="sidebar-panel">
            <div className="sidebar-brand">
              <div className="sidebar-brand-mark" aria-hidden="true">
                <span className="sidebar-brand-orbit" />
                <span className="sidebar-brand-wave" />
              </div>
              <div className="sidebar-brand-copy">
                <strong>{platform.platform_title}</strong>
              </div>
            </div>

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

            <div className="sidebar-overview">
              <div className="overview-title">概览</div>
              <StatList items={bottomStats} />
            </div>
          </section>
        </aside>

        <main className="workspace-shell">
          <header className="workspace-header">
            <div className="topbar">
              <label className="topbar-search">
                <Search className="topbar-search-icon" strokeWidth={1.8} />
                <input className="topbar-search-input" type="text" value={searchText} placeholder={platform.global_search_placeholder ?? '搜索文件...'} onChange={(event) => setSearchText(event.target.value)} />
              </label>
              <div className="topbar-tools">
                <button className="toggle-pill" type="button" aria-label="Theme Toggle" onClick={() => setDarkMode((current) => !current)}>
                  <span className="toggle-pill-track">
                    <span className={`toggle-pill-thumb ${darkMode ? 'toggle-pill-thumb-active' : ''}`} />
                  </span>
                  {darkMode ? <Moon className="toggle-pill-icon" strokeWidth={1.8} /> : <Sun className="toggle-pill-icon" strokeWidth={1.8} />}
                </button>
                <button className="square-tool" type="button" aria-label="Fullscreen">
                  <Maximize2 className="square-tool-icon" strokeWidth={1.8} />
                </button>
              </div>
            </div>

            <TabBar tabs={openTabs} activeTabId={activeTabId} onActivate={setActiveTabId} onClose={handleCloseTab} />
          </header>

          <section className="workspace-card">
            <div className="filter-panel">
              <FilterGrid fields={activeScene.filter_fields} values={filters} onChange={handleFilterChange} />
              <div className="scope-summary-row">
                <span className="scope-summary-text">{`范围: ${activeScope?.label ?? activeScene.current_scope_label}`}</span>
                <button className="link-button" type="button" onClick={handleClearFilters}>清空筛选</button>
              </div>
            </div>

            <div className="result-panel">
              <EmptyTable columns={activeScene.table_columns} title={activeScene.empty_result_title} copy={activeScene.empty_result_copy} />
            </div>
          </section>
        </main>

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
  --surface: #0f172a;
  --panel: #111827;
  --panel-soft: #1f2937;
  --line: #334155;
  --line-soft: #293548;
  --text: #e5eef9;
  --muted: #9fb0c5;
  --muted-soft: #7b8ca5;
  --shadow: 0 22px 54px rgba(2, 6, 23, 0.35);
}

* {
  box-sizing: border-box;
}

html,
body,
#root {
  margin: 0;
  min-height: 100%;
}

body {
  background: linear-gradient(180deg, #f7f9fc 0%, #f2f5f9 48%, #eef2f6 100%);
  color: var(--text);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

:root[data-theme='dark'] body {
  background: linear-gradient(180deg, #0b1220 0%, #101827 48%, #121b2c 100%);
}

button,
input,
select {
  font: inherit;
}

button {
  -webkit-tap-highlight-color: transparent;
}

.platform-app {
  min-height: 100vh;
  padding: 8px;
}

.platform-shell {
  min-height: calc(100vh - 16px);
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr) 20px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(221, 229, 239, 0.9);
  border-radius: 18px;
  overflow: hidden;
}

:root[data-theme='dark'] .platform-shell {
  background: rgba(15, 23, 42, 0.84);
  border-color: rgba(51, 65, 85, 0.88);
}

.sidebar-shell {
  grid-column: 1;
  grid-row: 1;
  width: 274px;
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  border-right: 1px solid var(--line);
  background: var(--panel);
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
  background: rgba(15, 23, 42, 0.45);
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

.sidebar-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
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
  font-size: 13px;
  font-weight: 700;
  color: #111827;
}

.sidebar-directory {
  flex: 1;
  border-top: 1px solid var(--line-soft);
  border-bottom: 1px solid var(--line-soft);
  padding: 8px 0 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.sidebar-directory-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px 8px;
  margin-bottom: 0;
  font-size: 14px;
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

.panel-icon-button:hover,
.square-tool:hover {
  border-color: var(--accent);
  color: var(--accent);
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
  font-size: 12px;
  padding: 7px 8px;
  border-radius: 7px;
  background: transparent;
  border: 0;
  text-align: left;
  cursor: pointer;
  transition: background-color 120ms ease, color 120ms ease;
}

.scope-node:hover {
  background: rgba(37, 99, 235, 0.06);
  color: #1d4ed8;
}

.scope-node-active {
  background: rgba(37, 99, 235, 0.06);
  color: var(--accent);
  font-weight: 600;
}

.scope-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-overview {
  margin-top: auto;
  background: rgba(248, 250, 252, 0.74);
  padding: 12px 10px 14px;
  border-top: 1px solid var(--line-soft);
}

.overview-title {
  font-size: 12px;
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
  font-size: 12px;
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
  font-size: 11px;
  line-height: 1;
  background: #f8fafc;
  border: 1px solid #d9e2ec;
  color: #64748b;
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
  grid-column: 2;
  grid-row: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f7f9fc;
}

.platform-footer {
  grid-column: 1 / span 2;
  grid-row: 2;
  min-width: 0;
  border-top: 1px solid rgba(219, 227, 239, 0.9);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.98));
}

.workspace-header,
.workspace-card {
  margin: 0 8px;
}

.workspace-header {
  display: grid;
  gap: 0;
  padding-top: 5px;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 3px;
}

.topbar-search {
  flex: 1;
  height: 31px;
  border: 1px solid #d9e2ec;
  border-radius: 7px;
  background: linear-gradient(180deg, #ffffff, #fcfdff);
  padding: 0 10px;
  display: flex;
  align-items: center;
  gap: 7px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92);
  transition: border-color 120ms ease, box-shadow 120ms ease;
}

.topbar-search:focus-within {
  border-color: #b8cbef;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.topbar-search-input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text);
  font-size: 12px;
}

.topbar-search-input::placeholder {
  color: var(--muted-soft);
}

.topbar-tools {
  display: flex;
  gap: 5px;
  align-items: center;
}

.toggle-pill {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 999px;
  height: 24px;
  padding: 0 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: border-color 120ms ease, background-color 120ms ease;
}

.toggle-pill:hover {
  border-color: #bfd3f8;
  background: #f8fbff;
}

.toggle-pill-track {
  width: 30px;
  height: 12px;
  display: flex;
  align-items: center;
  padding: 0 2px;
  border-radius: 999px;
  background: #eef2f7;
}

.toggle-pill-thumb {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #cbd5e1;
  transition: transform 160ms ease;
}

.toggle-pill-thumb-active {
  transform: translateX(16px);
  background: var(--accent);
}

.toggle-pill-icon {
  width: 13px;
  height: 13px;
  color: var(--muted);
}

.tab-bar {
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding: 0;
  border-bottom: 1px solid var(--line);
  scrollbar-width: thin;
}

.tab-chip {
  border: 1px solid var(--line);
  border-bottom-color: #d6dee8;
  background: #f9fbfd;
  color: #475569;
  border-radius: 6px 6px 0 0;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 0;
  min-width: 0;
  min-height: 34px;
  margin-right: 2px;
  position: relative;
  transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}

.tab-chip:hover {
  background: #edf4ff;
  color: #1d4ed8;
  border-color: #b8cbef;
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.08);
  transform: translateY(-1px);
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
  padding: 7px 8px 6px 10px;
  cursor: pointer;
  outline: none;
}

.tab-chip-active {
  background: var(--panel);
  color: var(--accent);
  border-bottom-color: var(--panel);
  box-shadow: 0 1px 0 var(--panel);
  z-index: 1;
}

.tab-chip-active:hover {
  background: var(--panel);
  border-color: #c8d6eb;
  color: var(--accent);
  box-shadow: 0 1px 0 var(--panel);
  transform: none;
}

.tab-chip-text {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 126px;
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
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
  opacity: 1;
}

.tab-chip-close-icon {
  width: 13px;
  height: 13px;
}

.workspace-card {
  margin-top: 3px;
  margin-bottom: 6px;
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  display: grid;
  gap: 8px;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
  flex: 1;
}

.filter-panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--panel);
  padding: 10px 9px 8px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.03);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1.12fr 1fr 1.12fr 1fr 1fr 1fr 1.16fr;
  gap: 8px 9px;
}

.filter-field {
  display: grid;
  gap: 5px;
}

.filter-label {
  color: #6b7280;
  font-size: 10px;
  line-height: 1.2;
}

.filter-control {
  min-height: 30px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  padding: 0 8px;
  color: var(--text);
  outline: none;
  transition: border-color 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
}

.filter-control::placeholder {
  color: #9ca3af;
}

.filter-control:focus {
  border-color: rgba(37, 99, 235, 0.45);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.filter-select-wrap {
  position: relative;
}

.filter-select {
  appearance: none;
  padding-right: 28px;
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

.scope-summary-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #64748b;
  font-size: 12px;
  min-height: 24px;
}

.scope-summary-text {
  color: #6b7280;
}

.link-button {
  border: 1px solid rgba(59, 130, 246, 0.22);
  background: rgba(239, 246, 255, 0.92);
  color: var(--accent);
  cursor: pointer;
  padding: 0 9px;
  min-height: 24px;
  border-radius: 999px;
  font-size: 10px;
  transition: border-color 120ms ease, background-color 120ms ease, color 120ms ease;
}

.link-button:hover {
  border-color: rgba(37, 99, 235, 0.32);
  background: #eaf3ff;
  color: #1d4ed8;
}

.result-panel {
  border: 1px solid rgba(219, 227, 239, 0.95);
  border-radius: 12px;
  background: var(--panel);
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
  box-shadow: 0 9px 20px rgba(15, 23, 42, 0.03);
}

.table-shell {
  width: 100%;
  overflow: auto;
  flex: 1;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
}

.result-table th {
  text-align: left;
  font-size: 12px;
  color: #64748b;
  background: #f4f7fb;
  padding: 7px 12px;
  border-bottom: 1px solid var(--line);
  font-weight: 600;
  height: 34px;
}

.result-table td {
  padding: 11px 12px;
}

.empty-cell {
  height: 560px;
  vertical-align: middle;
}

.empty-state {
  min-height: 430px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #64748b;
  text-align: center;
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

.empty-state p {
  max-width: 360px;
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
}

.workspace-footer {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-start;
  min-height: 20px;
  padding: 0 7px;
  width: 100%;
  overflow: hidden;
  color: #64748b;
  font-size: 9px;
}

.footer-stat {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex: 0 0 auto;
  white-space: nowrap;
}

.footer-stat-label {
  color: #64748b;
}

.footer-stat-separator {
  color: #94a3b8;
}

.footer-stat-value {
  color: #64748b;
  font-weight: 700;
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
    grid-row: 1;
    width: 100%;
    grid-template-columns: 44px minmax(0, 1fr);
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .workspace-shell {
    grid-column: 1;
    grid-row: 2;
  }

  .platform-footer {
    grid-column: 1;
    grid-row: 3;
  }

  .workspace-header,
  .workspace-card {
    margin: 0 8px;
  }

  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-footer {
    margin: 0;
    flex-wrap: wrap;
    overflow: auto;
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

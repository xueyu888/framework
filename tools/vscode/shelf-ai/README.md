# Shelf AI (VSCode Extension)

<p align="center">
  <img src="./media/shelf-duck-tight-transparent.png" alt="Shelf AI icon" width="168">
</p>

## What It Does

Authoring-term note:

- framework 作者源中的 `Boundary` 现统一改称 `Parameter`
- 当前 canonical / runtime 为兼容既有主链，仍保留 `boundary_id`、`boundary projection` 等历史机器字段名

- Opens the framework tree and workspace evidence tree from the sidebar.
- Clicks on the Shelf status bar item can open the framework tree directly (configurable).
- Treats the repository mainline as:
  `Framework -> Config -> Code -> Evidence`.
- Treats `projects/*/generated/canonical.json` as the only machine truth.
- Treats framework tree as an author-source runtime projection from `framework/**`.
- Treats evidence tree as a canonical-derived workspace evidence view.
- Supports framework-markdown navigation for `B/C/R/V`, parameters, module refs, and rule refs.
- Maps framework parameters back to `projects/*/project.toml` sections such as `[exact.knowledge_base.chat]` and `[exact.frontend.surface]`.
- Auto-materializes affected projects when `framework/*.md` or `projects/*/project.toml` changes.
- Guards `projects/*/generated/*` from direct edits.
- Treats stale / missing / invalid canonical as non-authoritative: formal config jumps and the evidence tree wait for fresh canonical.
- Runs canonical validation and optionally `mypy` from the extension.
- Adds project-independent framework markdown syntax diagnostics (Problems 波浪线) while typing/saving.
- Adds context-aware framework markdown completion (section-aware + auto-number defaults) and lint Quick Fix actions.
- Adds an experimental `.sf` language preview (`shelf-framework`) with its own semantic highlight, lint, and completion, without replacing formal `framework/*.md` author sources.
- Supports publishing the active `framework_drafts/...` file into the formal `framework/...` tree.
- Keeps ordinary implementation saves unblocked; repository-side validation/hook checks remain the main enforcement boundary.

## Contract

- 插件后续设计与实现的正式契约文档：
  `tools/vscode/shelf-ai/插件设计与实现契约.md`
- 后续凡是插件相关代码变更，都应同步检查并在需要时更新该文档。
- `.sf` 实验语言当前作者规范文档：
  `tools/vscode/shelf-ai/keyword-first-grammar-协议.md`

## Install (Local)

1. Install extension development dependencies:
   `cd tools/vscode/shelf-ai && npm install`
2. Build tree webview bundle:
   `npm run build:webview`
3. Package and install the current source version:
   `bash tools/vscode/shelf-ai/install_local.sh`
4. If your VSCode CLI is not `code`, set it explicitly:
   `CODE_BIN=code-insiders bash tools/vscode/shelf-ai/install_local.sh`

## Commands

- `Shelf: Insert Framework Module Template`
- `Shelf: Install Git Hooks`
- `Shelf: Validate Canonical Now`
- `Shelf: Run Codegen Preflight`
- `Shelf: Publish Current Framework Draft`
- `Shelf: Show Validation Issues`
- `Shelf: Open Framework Tree`
- `Shelf: Refresh Framework Tree`
- `Shelf: Open Evidence Tree`
- `Shelf: Refresh Evidence Tree`

## Configuration

Local workspace overlay file:

- `.shelf/settings.jsonc`
- VSCode `shelf.*` setting has highest priority; `.shelf/settings.jsonc` is used when no explicit VSCode value is set.
- `.shelf/settings.jsonc` can use JSONC comments and is intended for repository-visible local tuning.

- `shelf.guardMode = strict`
- `shelf.showMessagePopups = true`
- `shelf.frameworkTreeNodeHorizontalGap = 8`
- `shelf.frameworkTreeLevelVerticalGap = 80`
- `shelf.frameworkTreeAutoRefreshOnSave = true`
- `shelf.statusBarClickAction = openFrameworkTree`
- `shelf.treeZoomMinScale = 0.68`
- `shelf.treeZoomMaxScale = 2.4`
- `shelf.treeWheelSensitivity = 1`
- `shelf.treeInspectorWidth = 338`
- `shelf.treeInspectorRailWidth = 42`
- `shelf.validationCommandTimeoutMs = 120000`
- `shelf.generatedEventSuppressionMs = 2500`
- `shelf.manualValidationRestartThresholdMs = 15000`
- `shelf.validationDebounceMs = 250`
- `shelf.frameworkLintOnlyOnFrameworkChanges = true`
- `shelf.frameworkLintEnabled = true`
- `shelf.frameworkLintOnType = true`
- `shelf.frameworkLintDebounceMs = 300`
- `shelf.frameworkAutoCompleteEnabled = true`
- `shelf.frameworkAutoTriggerSuggest = true`
- `shelf.frameworkQuickFixEnabled = true`

Changing tree webview settings will re-render the currently open tree panel automatically. If no tree panel is open, the next open/refresh will use the new values. Validation timing settings take effect on the next scheduled or manual validation run without requiring reload. Framework lint/completion/quick-fix settings take effect immediately for currently opened framework markdown files.

Framework lint execution scope:

- Shelf lints every Markdown file under `framework/**` and `framework_drafts/**`.
- Shelf also lints any Markdown file whose content contains `@framework`, even outside those directories.
- Shelf also lints standalone `.sf` files as an editor-only preview language (`shelf-framework`); those files do not participate in canonical, materialize, or publish flows.
- Inside `framework/**` / `framework_drafts/**`, only Markdown attachments that are directly referenced by a framework module are treated as valid authoring files; orphan Markdown files are reported as errors.
- Framework modules may only directly reference Markdown files inside the same controlled framework domain.

Framework-only automation setting:

- `shelf.frameworkLintOnlyOnFrameworkChanges = true`:
  when a framework-controlled Markdown file changes, Shelf only updates framework lint diagnostics.
  save-triggered canonical validation, auto-materialization, and mypy do not run for those framework changes.
  manual `Shelf: Validate Canonical Now` and `Shelf: Run Codegen Preflight` keep their normal full-chain behavior.

Notification popup behavior:

- `shelf.showMessagePopups = true`: keep Shelf right-corner popup messages enabled.
- `shelf.showMessagePopups = false`: suppress popup interruptions while keeping Output logs, status-bar state, and Problems signals available.

Framework tree behavior settings:

- `shelf.frameworkTreeAutoRefreshOnSave = true`:
  after framework markdown is saved, Shelf refreshes an open framework tree in the background.
  if `shelf.frameworkLintOnlyOnFrameworkChanges = false`, Shelf first runs the save-time change validation/materialization pipeline and then refreshes the tree.
  save-time refresh is background-only and will not auto-pop or force-focus the framework tree panel.
  when full materialization fails and the materialize command uses `scripts/materialize_project.py`, Shelf enables `--allow-framework-only-fallback` to refresh `canonical.framework` snapshot first.
- `shelf.statusBarClickAction = openFrameworkTree`:
  clicking Shelf status bar opens the framework tree panel (floating/dockable/resizable webview tab).
- `shelf.statusBarClickAction = quickPick`:
  clicking Shelf status bar first shows two explicit choices: open framework tree or show issues.

## Validation

Default commands:

- `uv run python scripts/validate_canonical.py --check-changes`
- `uv run python scripts/validate_canonical.py`
- `uv run python scripts/materialize_project.py`
- `uv run mypy`

`validate_canonical.py` enforces one-to-one boundary projection at repository guard level. If any boundary still maps to multiple related paths, validation fails with `FRAMEWORK_VIOLATION` and asks for framework updates first.

When the repository currently has no `projects/*/project.toml`, `validate_canonical.py` and `materialize_project.py` return no-op success and explicitly report bootstrap / no-project mode. `src/main.py serve` still requires a real project file before runtime startup.

`Shelf: Run Codegen Preflight` materializes all discovered `projects/*/project.toml` files, then runs full validation. If no project config exists yet, the command reports bootstrap / framework-authoring mode instead of failing.

Framework markdown lint is independent from project selection: syntax diagnostics are computed directly from framework-controlled Markdown and rendered as standard VSCode Problems diagnostics.
The same diagnostics expose Quick Fix actions (lightbulb) for common formatting mistakes, including list marker normalization, missing `@framework`, missing standard sections, and invalid C/P/B/R/V entry formatting.

The `@framework` template entry is a repository-side hard authoring contract and must not be removed without an equally direct replacement.

## Tree Views

The framework tree is the authoring view.
The evidence tree is the canonical-derived workspace evidence view.
No persisted tree artifact is used for these views; both trees are runtime projections.
Both tree views render as interactive webview graphs (dagre layout + d3-zoom runtime interaction), and framework nodes stay layer-fixed with layout-engine auto sorting.
Tree interactions include search, upstream/downstream focus, keyboard navigation (arrow keys + Enter), and viewport/selection state persistence.
The framework tree is parsed directly from `framework/**` modules and their `B*` / `R*` declarations, and does not depend on project config selection.
The canvas renders a module-only author graph: `B*` and rule participation stay available in hover/inspection, while module arrows are collapsed from upstream module refs in base definitions (for example `L0.M0[...]`).
Framework markdown saves should trigger canonical refresh in background so machine-mainline artifacts remain up-to-date, but framework tree rendering itself does not wait for canonical.
When canonical is stale, missing, or invalid, Shelf blocks the formal evidence tree until you materialize again.
When no `projects/*/project.toml` exists yet, Shelf keeps framework authoring features available but treats the evidence tree and formal cross-layer navigation as not yet established.
Framework-only fallback snapshots are marked as degraded materialization state, so evidence tree remains blocked until the next full materialization succeeds.

## Project Config Navigation

Boundary jumps now target unified project config sections, for example:

- `[exact.frontend.surface]`
- `[exact.frontend.visual]`
- `[exact.knowledge_base.chat]`
- `[exact.knowledge_base.library]`
- `[exact.knowledge_base.preview]`
- `[exact.knowledge_base.return]`

The extension no longer treats the removed dual-track config files as live authoring entrypoints.

## Release Notes

Public release notes live at:

- `tools/vscode/shelf-ai/CHANGELOG.md`
- `tools/vscode/shelf-ai/release-notes/0.1.25.md`

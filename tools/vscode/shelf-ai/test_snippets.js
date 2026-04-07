const assert = require("assert");
const fs = require("fs");
const path = require("path");
const frameworkCompletion = require("./framework_completion");

const extensionRoot = __dirname;

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(extensionRoot, relativePath), "utf8"));
}

function readText(relativePath) {
  return fs.readFileSync(path.join(extensionRoot, relativePath), "utf8");
}

function main() {
  const packageJson = readJson("package.json");
  const snippetJson = readJson(path.join("snippets", "markdown.code-snippets"));
  const extensionSource = readText("extension.js");
  const readme = readText("README.md");

  const snippetContribution = (packageJson.contributes?.snippets || []).find(
    (item) => item.language === "markdown" && item.path === "./snippets/markdown.code-snippets"
  );
  assert(snippetContribution, "package.json must contribute markdown snippets");
  assert(
    (packageJson.files || []).includes("framework_completion.js"),
    "package.json must package framework_completion.js"
  );
  assert(
    (packageJson.files || []).includes("guarding.js"),
    "package.json must package guarding.js"
  );
  assert(
    (packageJson.files || []).includes("local_settings.js"),
    "package.json must package local_settings.js"
  );

  const commandContribution = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.insertFrameworkModuleTemplate"
  );
  assert(commandContribution, "package.json must contribute the framework template insert command");
  const installHooksCommand = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.installGitHooks"
  );
  assert(installHooksCommand, "package.json must contribute the git hooks install command");
  const openFrameworkTreeCommand = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.openFrameworkTree"
  );
  assert(openFrameworkTreeCommand, "package.json must contribute the framework tree open command");
  const openEvidenceTreeCommand = (packageJson.contributes?.commands || []).find(
    (item) => item.command === "shelf.openEvidenceTree"
  );
  assert(openEvidenceTreeCommand, "package.json must contribute the evidence tree open command");

  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.insertFrameworkModuleTemplate"),
    "package.json must activate on the framework template insert command"
  );
  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.installGitHooks"),
    "package.json must activate on the git hooks install command"
  );
  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.openFrameworkTree"),
    "package.json must activate on the framework tree open command"
  );
  assert(
    (packageJson.activationEvents || []).includes("onCommand:shelf.openEvidenceTree"),
    "package.json must activate on the evidence tree open command"
  );

  const configuration = packageJson.contributes?.configuration?.properties || {};
  for (const key of [
    "shelf.guardMode",
    "shelf.showMessagePopups",
    "shelf.autoMaterialize",
    "shelf.runMypyOnPythonChanges",
    "shelf.protectGeneratedFiles",
    "shelf.promptInstallGitHooks",
    "shelf.materializeCommand",
    "shelf.typeCheckCommand",
  ]) {
    assert(Object.prototype.hasOwnProperty.call(configuration, key), `package.json must expose ${key}`);
  }
  assert.strictEqual(
    configuration["shelf.changeValidationCommand"]?.default,
    "uv run python scripts/validate_canonical.py --check-changes",
    "package.json must default shelf.changeValidationCommand to the supported canonical validation command"
  );
  assert.strictEqual(
    configuration["shelf.fullValidationCommand"]?.default,
    "uv run python scripts/validate_canonical.py",
    "package.json must default shelf.fullValidationCommand to the supported canonical validation command"
  );
  assert(
    configuration["shelf.frameworkLintOnlyOnFrameworkChanges"]?.default === true,
    "package.json must enable framework-lint-only automation for framework changes by default"
  );
  assert(
    configuration["shelf.frameworkLintEnabled"]?.default === true,
    "package.json must enable framework realtime lint by default"
  );
  assert(
    configuration["shelf.frameworkLintOnType"]?.default === true,
    "package.json must run framework realtime lint while typing by default"
  );
  assert(
    configuration["shelf.frameworkLintDebounceMs"]?.default === 300,
    "package.json must expose framework lint debounce configuration"
  );
  assert(
    configuration["shelf.frameworkAutoCompleteEnabled"]?.default === true,
    "package.json must enable framework auto completion by default"
  );
  assert(
    configuration["shelf.frameworkAutoTriggerSuggest"]?.default === true,
    "package.json must auto trigger framework completion by default"
  );
  assert(
    configuration["shelf.frameworkQuickFixEnabled"]?.default === true,
    "package.json must enable framework lint quick fixes by default"
  );
  assert.strictEqual(
    configuration["shelf.frameworkTreeAutoRefreshOnSave"]?.default,
    true,
    "package.json must auto-refresh framework tree on save by default"
  );
  assert.strictEqual(
    configuration["shelf.statusBarClickAction"]?.default,
    "openFrameworkTree",
    "package.json must default status bar click action to open framework tree"
  );
  assert.strictEqual(
    configuration["shelf.showMessagePopups"]?.default,
    true,
    "package.json must enable popup messages by default"
  );
  assert.strictEqual(
    configuration["shelf.treeZoomMaxScale"]?.default,
    2.4,
    "package.json must allow framework tree zooming beyond the old 155% cap by default"
  );
  assert(
    (configuration["shelf.statusBarClickAction"]?.enum || []).includes("quickPick"),
    "package.json must support quickPick status bar click action"
  );

  const frameworkSnippet = snippetJson["@framework Module Template"];
  assert(frameworkSnippet, "markdown snippets must keep the @framework module template");
  assert.strictEqual(frameworkSnippet.prefix, "@framework");
  assert(Array.isArray(frameworkSnippet.body), "@framework snippet must have a body array");
  assert(frameworkSnippet.body.includes("@framework"), "@framework snippet body must include the directive line");
  assert(
    frameworkSnippet.body.includes("## 0. 目标 (Goal)"),
    "@framework snippet must include goal section"
  );
  assert(
    frameworkSnippet.body.includes("## 1. 最小结构基（Minimal Structural Bases）"),
    "@framework snippet must include base section"
  );
  assert(
    frameworkSnippet.body.includes("## 2. 基排列组合（Base Arrangement / Combination）"),
    "@framework snippet must include base arrangement section"
  );
  assert(
    frameworkSnippet.body.includes("## 3. 边界定义（Boundary）"),
    "@framework snippet must include boundary section"
  );
  assert(
    frameworkSnippet.body.includes("### 3.1 接口定义（IO / Ports）"),
    "@framework snippet must include boundary ports subsection"
  );
  assert(
    frameworkSnippet.body.includes("### 3.2 参数边界（Parameter Constraints）"),
    "@framework snippet must include boundary parameters subsection"
  );
  assert(
    frameworkSnippet.body.includes("## 4. 能力声明（Capability Statement）"),
    "@framework snippet must include capability statement section"
  );

  assert(
    /registerCommand\s*\(\s*"shelf\.insertFrameworkModuleTemplate"/.test(extensionSource),
    "extension.js must register the framework template insert command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.installGitHooks"/.test(extensionSource),
    "extension.js must register the git hooks install command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.openFrameworkTree"/.test(extensionSource),
    "extension.js must register the framework tree open command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.statusBarActionMenu"/.test(extensionSource),
    "extension.js must register the status bar action menu command"
  );
  assert(
    /registerCommand\s*\(\s*"shelf\.openEvidenceTree"/.test(extensionSource),
    "extension.js must register the evidence tree open command"
  );
  assert(
    /registerCompletionItemProvider\s*\(/.test(extensionSource),
    "extension.js must register a markdown completion provider"
  );
  assert(
    /registerCodeActionsProvider\s*\(/.test(extensionSource),
    "extension.js must register framework markdown quick-fix provider"
  );
  assert(
    extensionSource.includes('if (code === "FWL012")'),
    "extension.js must provide a heading-order quick fix for FWL012 diagnostics"
  );
  assert(
    extensionSource.includes("editor.action.triggerSuggest"),
    "extension.js must trigger framework suggestion popup while typing"
  );
  assert(
    /onDidChangeTextDocument\s*\(/.test(extensionSource),
    "extension.js must clear stale shelf diagnostics when watched documents are edited"
  );
  assert(
    extensionSource.includes('openTreeView("framework", { reveal: false })'),
    "extension.js must refresh framework tree in background on save without auto-revealing the panel"
  );
  assert(
    extensionSource.includes('$(close) Shelf 失败'),
    "extension.js must expose a visible cross icon for failing Shelf status"
  );
  assert(
    readme.includes("Shelf: Insert Framework Module Template"),
    "README must document the framework template insert command"
  );
  assert(
    readme.includes("Shelf: Install Git Hooks"),
    "README must document the git hooks install command"
  );
  assert(
    readme.includes("Shelf: Open Framework Tree"),
    "README must document the framework tree open command"
  );
  assert(
    readme.includes("shelf.statusBarClickAction = openFrameworkTree"),
    "README must document status bar click action setting"
  );
  assert(
    readme.includes("shelf.statusBarClickAction = quickPick"),
    "README must document quickPick status bar action mode"
  );
  assert(
    readme.includes("shelf.frameworkLintOnlyOnFrameworkChanges = true"),
    "README must document the framework-lint-only automation setting"
  );
  assert(
    readme.includes("Shelf: Refresh Framework Tree"),
    "README must document the framework tree refresh command"
  );
  assert(
    readme.includes("Shelf: Open Evidence Tree"),
    "README must document the evidence tree open command"
  );
  assert(
    readme.includes("The `@framework` template entry is a repository-side hard authoring contract"),
    "README must document the non-removable @framework authoring contract"
  );
  assert(
    readme.includes("shelf.guardMode = strict"),
    "README must document strict guard mode"
  );
  assert(
    readme.includes("shelf.showMessagePopups = true"),
    "README must document the popup notification toggle setting"
  );
  assert(
    readme.includes(".shelf/settings.jsonc"),
    "README must document the local .shelf settings entrypoint"
  );
  assert(
    readme.includes("VSCode `shelf.*` setting has highest priority"),
    "README must document local settings precedence"
  );
  assert(
    readme.includes("uv run python scripts/validate_canonical.py --check-changes"),
    "README must document the supported save-triggered canonical validation command"
  );
  assert(
    readme.includes("uv run python scripts/validate_canonical.py"),
    "README must document the supported full canonical validation command"
  );
  assert(
    !readme.includes("validate_canonical.py --json"),
    "README must not document the optional --json canonical flag as the default command"
  );
  assert(
    readme.includes("Treats stale / missing / invalid canonical as non-authoritative"),
    "README must document strict canonical freshness behavior"
  );
  assert(
    readme.includes("Shelf blocks the formal evidence tree until you materialize again"),
    "README must explain how the evidence tree behaves when canonical is stale"
  );
  assert(
    readme.includes("No persisted tree artifact"),
    "README must state tree views are runtime projections without persisted artifacts"
  );

  const atEntries = frameworkCompletion.getFrameworkCompletionEntries("@", "@", false);
  assert(
    atEntries.some((entry) => entry.label === "@framework 标准模块模板"),
    "@ completion must include the full framework template"
  );
  assert(
    atEntries.some((entry) => entry.label === "@framework"),
    "@ completion must include the plain @framework directive"
  );

  const sectionEntries = frameworkCompletion.getFrameworkCompletionEntries("## ", "", true);
  assert(
    sectionEntries.some((entry) => entry.label.includes("最小结构基")),
    "section completion must include the Minimal Structural Bases heading"
  );

  const authoringSample = [
    "# 模块:Module",
    "",
    "@framework",
    "",
    "## 0. 目标 (Goal)",
    "",
    "- 目标说明。",
    "",
    "## 1. 最小结构基（Minimal Structural Bases）",
    "",
    "- `B1` 输入基：描述。",
    "",
    "## 2. 基排列组合（Base Arrangement / Combination）",
    "",
    "- `R7` `现有规则`：由 `{B1}` 形成 `结果`，导出 `C1`。",
    "",
    "## 3. 边界定义（Boundary）",
    "",
    "### 3.1 接口定义（IO / Ports）",
    "",
    "- `QUERY_IN`：运行时输入接口。",
    "",
    "### 3.2 参数边界（Parameter Constraints）",
    "",
    "- `P1` 查询长度：描述。",
    "",
    "## 4. 能力声明（Capability Statement）",
    "",
    "- `C1` 现有能力：描述。",
    "- `N1` 非职责声明：描述。",
  ].join("\n");

  const capabilityEntries = frameworkCompletion.getFrameworkCompletionEntries(
      "- ",
      "",
      true,
      {
        documentText: authoringSample,
        lineNumber: 27,
      }
  );
  assert(
    capabilityEntries.some((entry) => entry.label === "C 条目"),
    "capability section completion must include C entry"
  );
  assert(
    !capabilityEntries.some((entry) => entry.label === "参数条目"),
    "capability section completion should not prioritize parameter entry"
  );
  const cEntry = capabilityEntries.find((entry) => entry.label === "C 条目");
  assert(cEntry?.insertText.includes("C${1:2}"), "C completion should infer next index from current document");
  assert(
    capabilityEntries.some((entry) => entry.label === "N 条目"),
    "capability section completion must include non-responsibility entry"
  );
  const templateText = frameworkCompletion.getFrameworkTemplateSnippetText();
  assert(
    !templateText.includes("### 非职责声明（Non-Responsibility Statement）"),
    "framework template text should place N entries directly after C entries"
  );

  const baseEntries = frameworkCompletion.getFrameworkCompletionEntries("- `B", "B", true, {
    documentText: authoringSample,
    lineNumber: 8,
  });
  assert(
    baseEntries.some((entry) => entry.label === "B 条目"),
    "base completion must include the B entry template"
  );

  const ruleEntries = frameworkCompletion.getFrameworkCompletionEntries("- `R", "R", true, {
    documentText: authoringSample,
    lineNumber: 12,
  });
  assert(
    ruleEntries.some((entry) => entry.label === "R 条目"),
    "rule completion must include single-line R entry"
  );
  const ruleEntry = ruleEntries.find((entry) => entry.label === "R 条目");
  assert(
    ruleEntry?.insertText.includes("R${1:8}"),
    "rule completion should infer next rule number"
  );

  const parameterAuthoringSample = [
    "# 模块:Module",
    "",
    "@framework",
    "",
    "## 3. 边界定义（Boundary）",
    "",
    "### 3.1 接口定义（IO / Ports）",
    "",
    "- `QUERY_IN`：描述。",
    "",
    "### 3.2 参数边界（Parameter Constraints）",
    "",
    "- `P1` 现有参数：描述。",
    "",
  ].join("\n");
  const parameterDashAutoExpansion = frameworkCompletion.getFrameworkDashAutoExpansion(
    "-",
    true,
    {
      documentText: parameterAuthoringSample,
      lineNumber: 11,
    }
  );
  assert(
    typeof parameterDashAutoExpansion?.insertText === "string",
    "parameter section dash should auto-expand to parameter entry"
  );
  assert(
    parameterDashAutoExpansion.insertText.includes("${1:P2}"),
    "parameter dash auto-expansion should infer the next P index"
  );
  const nonParameterDashAutoExpansion = frameworkCompletion.getFrameworkDashAutoExpansion(
    "-",
    true,
    {
      documentText: authoringSample,
      lineNumber: 27,
    }
  );
  assert.strictEqual(
    nonParameterDashAutoExpansion,
    null,
    "dash auto-expansion should only apply inside the parameter section"
  );
}

main();

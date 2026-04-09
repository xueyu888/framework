const assert = require("assert");
const fs = require("fs");
const path = require("path");
const frameworkCompletion = require("./framework_completion");
const frameworkGrammar = require("./framework_grammar");

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
    (packageJson.files || []).includes("framework_grammar.js"),
    "package.json must package framework_grammar.js"
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

  const frameworkSnippet = snippetJson["@framework Module Template"];
  assert(frameworkSnippet, "markdown snippets must keep the @framework module template");
  assert.strictEqual(frameworkSnippet.prefix, "@framework");
  assert(Array.isArray(frameworkSnippet.body), "@framework snippet must have a body array");
  assert(frameworkSnippet.body.includes("@framework"), "@framework snippet body must include the directive line");
  assert(
    frameworkSnippet.body.includes("## Goal"),
    "@framework snippet must include Goal section"
  );
  assert(
    frameworkSnippet.body.includes("## Base"),
    "@framework snippet must include Base section"
  );
  assert(
    frameworkSnippet.body.includes("## Combination Principles"),
    "@framework snippet must include Combination Principles section"
  );
  assert(
    frameworkSnippet.body.includes("## Combination Space"),
    "@framework snippet must include Combination Space section"
  );
  assert(
    frameworkSnippet.body.includes("## Boundary"),
    "@framework snippet must include Boundary section"
  );
  assert(
    frameworkSnippet.body.includes("### Input"),
    "@framework snippet must include Input subsection"
  );
  assert(
    frameworkSnippet.body.includes("### Output"),
    "@framework snippet must include Output subsection"
  );
  assert(
    frameworkSnippet.body.includes("### Parameter"),
    "@framework snippet must include Parameter subsection"
  );
  assert.deepStrictEqual(
    frameworkSnippet.body,
    frameworkGrammar.FRAMEWORK_TEMPLATE_SNIPPET_BODY,
    "snippet template must stay aligned with shared framework grammar"
  );

  assert(
    /registerCommand\s*\(\s*"shelf\.insertFrameworkModuleTemplate"/.test(extensionSource),
    "extension.js must register the framework template insert command"
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
    /registerDocumentSemanticTokensProvider\s*\(/.test(extensionSource),
    "extension.js must register framework markdown semantic highlight provider"
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
    readme.includes("Shelf: Insert Framework Module Template"),
    "README must document the framework template insert command"
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
    sectionEntries.some((entry) => entry.label === "## Base"),
    "section completion must include Base heading"
  );

  const authoringSample = [
    "# 模块:Module",
    "",
    "@framework",
    "",
    "## Goal",
    "",
    "goal 文本单元定位 := 目标说明",
    "",
    "## Base",
    "",
    "base 文本索引基 := 描述",
    "",
    "## Combination Principles",
    "",
    "cp.form 文本定位组合 on <base.文本索引基> := 组合描述",
    "",
    "## Combination Space",
    "",
    "cs.可读取文本单元 := <base.文本索引基> by <cp.form.文本定位组合>",
    "",
    "## Boundary",
    "",
    "### Input",
    "",
    "bd.in 查询输入 := payload({query}), cardinality(1), to(cs.可读取文本单元)",
    "",
    "### Output",
    "",
    "bd.out 文本输出 := payload({text}), cardinality(1), from(cs.可读取文本单元)",
    "",
    "### Parameter",
    "",
    "bd.param 查询长度上限 := domain(int), affects(cs.可读取文本单元, bd.in.查询输入)",
  ].join("\n");

  const baseEntries = frameworkCompletion.getFrameworkCompletionEntries("base ", "base", true, {
    documentText: authoringSample,
    lineNumber: 10,
  });
  assert(
    baseEntries.some((entry) => entry.label === "base"),
    "base completion must include base statement template"
  );

  const principlesEntries = frameworkCompletion.getFrameworkCompletionEntries("cp.", "cp", true, {
    documentText: authoringSample,
    lineNumber: 14,
  });
  assert(
    principlesEntries.some((entry) => entry.label === "cp.form"),
    "combination principles completion must include cp.form template"
  );

  const boundaryInputEntries = frameworkCompletion.getFrameworkCompletionEntries("bd.", "bd", true, {
    documentText: authoringSample,
    lineNumber: 24,
  });
  assert(
    boundaryInputEntries.some((entry) => entry.label === "bd.in"),
    "boundary input completion must include bd.in template"
  );

  const templateText = frameworkCompletion.getFrameworkTemplateSnippetText();
  assert(
    templateText.includes("## Combination Space"),
    "framework template text should include Combination Space section"
  );
  assert(
    templateText.includes("bd.param"),
    "framework template text should include bd.param statement"
  );
  assert.strictEqual(
    frameworkCompletion.getFrameworkDashAutoExpansion("-", true, {
      documentText: authoringSample,
      lineNumber: 24,
    }),
    null,
    "dash auto-expansion should be disabled in keyword-first grammar"
  );
}

main();

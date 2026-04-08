const assert = require("assert");
const fs = require("fs");
const path = require("path");

const sfGrammar = require("./sf_grammar");
const sfCompletion = require("./sf_completion");
const sfLint = require("./sf_lint");

const extensionRoot = __dirname;

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(extensionRoot, relativePath), "utf8"));
}

function readText(relativePath) {
  return fs.readFileSync(path.join(extensionRoot, relativePath), "utf8");
}

const VALID_SAMPLE = [
  "module 父子任务状态记录模块:TaskStateRecorder:",
  "    Goal := \"记录父任务及其子任务的状态，并在子任务状态变化后同步更新父任务状态\"",
  "",
  "    Base:",
  "        elem 父任务提交处理逻辑 := [父任务提交处理逻辑](../../docs/back_zrx/父任务提交处理逻辑.md)",
  "        elem 子任务提交处理逻辑 := [子任务提交处理逻辑](../../docs/back_zrx/子任务提交处理逻辑.md)",
  "        attr 父任务状态记录表 := [父任务状态记录表](../../docs/back_zrx/父任务状态记录表.md)",
  "        attr 子任务状态记录表 := [子任务状态记录表](../../docs/back_zrx/子任务状态记录表.md)",
  "",
  "    Principles:",
  "        form 子任务提交 :=",
  "            on(<Base.子任务提交处理逻辑, Base.子任务状态记录表, Base.父任务状态记录表>),",
  "            body(\"接收子任务记录并同步更新父任务状态\")",
  "        sat 子任务提交 :=",
  "            on(<Spaces.comb.子任务提交>),",
  "            body(\"父任务记录必须先存在，子任务提交后父任务状态必须同步更新\")",
  "",
  "    Spaces:",
  "        comb 子任务提交 :=",
  "            from(<Base.子任务提交处理逻辑, Base.子任务状态记录表, Base.父任务状态记录表>),",
  "            by(<Principles.form.子任务提交, Principles.sat.子任务提交>)",
  "",
  "    Boundary:",
  "        in<schema> 子任务记录输入 :=",
  "            payload({子任务id, 父任务id, 子任务状态, 是否初次完成, 子任务附加信息}),",
  "            card(1),",
  "            to(Spaces.comb.子任务提交)",
  "",
  "        out<schema> 父任务记录输出 :=",
  "            payload({父任务id, 子任务总数, 已完成子任务数, 父任务状态, 父任务附加信息}),",
  "            card(0..1),",
  "            from(Spaces.comb.子任务提交)",
  "",
  "        param<enum> 子任务状态集合 :=",
  "            domain({pending, running, success, failed}),",
  "            affects(<Boundary.in.子任务记录输入, Spaces.comb.子任务提交>)",
].join("\n");

function main() {
  const packageJson = readJson("package.json");
  const extensionSource = readText("extension.js");

  const languageContribution = (packageJson.contributes?.languages || []).find(
    (item) => item.id === sfGrammar.SF_LANGUAGE_ID
  );
  assert(languageContribution, "package.json must contribute the .sf language");
  assert(
    Array.isArray(languageContribution.extensions) && languageContribution.extensions.includes(".sf"),
    "the .sf language contribution must own the .sf extension"
  );
  assert.strictEqual(
    languageContribution.configuration,
    "./languages/shelf-framework.json",
    "the .sf language contribution must point at its language configuration"
  );

  for (const packagedFile of ["sf_grammar.js", "sf_completion.js", "sf_lint.js"]) {
    assert(
      (packageJson.files || []).includes(packagedFile),
      `package.json must package ${packagedFile}`
    );
  }
  assert(
    (packageJson.files || []).includes("languages/**") || (packageJson.files || []).includes("languages/shelf-framework.json"),
    "package.json must package the .sf language configuration"
  );

  assert(
    extensionSource.includes('language: sfGrammar.SF_LANGUAGE_ID')
      || extensionSource.includes(`language: "${sfGrammar.SF_LANGUAGE_ID}"`),
    "extension.js must register providers for the .sf language id"
  );

  const issues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/demo.sf",
    text: VALID_SAMPLE,
  });
  assert.strictEqual(issues.length, 0, "valid .sf sample should pass lint");

  const invalidSample = VALID_SAMPLE.replace("            from(Spaces.comb.子任务提交)", "            to(Spaces.comb.子任务提交)");
  const invalidIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/demo.sf",
    text: invalidSample,
  });
  assert(
    invalidIssues.some((issue) => issue.code === "SFL008"),
    "invalid boundary clause ordering should be rejected"
  );

  const tokens = sfGrammar.collectShelfFrameworkSemanticTokens(VALID_SAMPLE);
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.statementKeyword));
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.reference));

  const fileEntries = sfCompletion.getShelfFrameworkCompletionEntries("", "", {
    documentText: "",
    lineNumber: 0,
  });
  assert(
    fileEntries.some((entry) => entry.label === "shelf-framework 标准模板"),
    "empty .sf document should offer the full template"
  );

  const boundaryEntries = sfCompletion.getShelfFrameworkCompletionEntries("        ", "", {
    documentText: VALID_SAMPLE,
    lineNumber: 23,
  });
  assert(
    boundaryEntries.some((entry) => entry.label === "in<schema>"),
    "boundary context must offer in<schema>"
  );
  assert(
    boundaryEntries.some((entry) => entry.label === "param<enum>"),
    "boundary context must offer param<enum>"
  );
}

main();

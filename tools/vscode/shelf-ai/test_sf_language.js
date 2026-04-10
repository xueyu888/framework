const assert = require("assert");
const fs = require("fs");
const path = require("path");

const sfGrammar = require("./sf_grammar");
const sfCompletion = require("./sf_completion");
const sfLint = require("./sf_lint");
const sfTextMateGrammar = require("./sf_textmate_grammar");

const extensionRoot = __dirname;

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(extensionRoot, relativePath), "utf8"));
}

function readText(relativePath) {
  return fs.readFileSync(path.join(extensionRoot, relativePath), "utf8");
}

function lineIndexOf(text, marker) {
  return String(text || "").split("\n").findIndex((line) => line.includes(marker));
}

const VALID_SAMPLE = [
  "MODULE 布尔逻辑模块:BooleanLogicModule:",
  "    Goal := \"定义由 0、1、And、Or、Not 生成的布尔表达式系统；在给定边界下，把全部合法组合按层数与可导出的定律进行分类。\"",
  "",
  "    Base:",
  "        set 变量集合 := \"记作 V；元素写作 x、y、z 等，表示可被赋值的命题变量。\"",
  "        set 常元集合 := \"元素写作 0、1；0 表示恒假，1 表示恒真。\"",
  "        struct 表达式树 := \"记作 Tree；它表示由常元、变量与连接子递归生成的复合结构。\"",
  "        seq 变元序列 := \"记作 <x, y, z>；表示变量的一个有序排列。\"",
  "        map 等价类索引 := \"记作 ClassOf；它把表达式映射到按 Principle.条件同一 划分的结果类。\"",
  "        op[2:1] And := \"记作 And(e, f)；二元连接子，表示 e 与 f 同时取 1。\"",
  "        op[2:1] Or := \"记作 Or(e, f)；二元连接子，表示 e 与 f 至少一侧取 1。\"",
  "        op[1:1] Not := \"记作 Not(e)；一元连接子，表示把 e 的 0/1 取值翻转。\"",
  "        set 表达式集合 := \"记作 T；0、1 与变量属于 T；若 e、f ∈ T，则 And(e, f) 与 Or(e, f) 属于 T；若 e ∈ T，则 Not(e) 属于 T。\"",
  "        op[1:1] 赋值函数 := \"记作 α；它只对变量赋值，即 α: V -> {0, 1}。\"",
  "        set 赋值全体 := \"记作 Ω；它由全部赋值函数 α 构成，即 Ω = { α | α: V -> {0, 1} }。\"",
  "",
  "    Principle:",
  "        sat 成立记号 := \"Sat(e, α) 表示表达式 e 在赋值 α 下的值为 1。\"",
  "        eq 同一记号 := \"e ≈ f 表示 e 与 f 属于同一个结果类；符号 ≈ 读作 等价。\"",
  "        sat 常元成立 := \"对任意 α ∈ Ω，Sat(1, α) 恒成立，Sat(0, α) 恒不成立。\"",
  "        sat 原子成立 := \"对任意变量 x ∈ V 与任意 α ∈ Ω，Sat(x, α) 成立，当且仅当 α(x)=1。\"",
  "        sat And成立 := \"对任意 e、f ∈ T 与任意 α ∈ Ω，Sat(And(e, f), α) 成立，当且仅当 Sat(e, α) 与 Sat(f, α) 同时成立。\"",
  "        sat Or成立 := \"对任意 e、f ∈ T 与任意 α ∈ Ω，Sat(Or(e, f), α) 成立，当且仅当 Sat(e, α) 与 Sat(f, α) 至少有一者成立。\"",
  "        sat Not成立 := \"对任意 e ∈ T 与任意 α ∈ Ω，Sat(Not(e), α) 成立，当且仅当 Sat(e, α) 不成立。\"",
  "        eq 条件同一 := \"对任意 e、f ∈ T，若对所有 α ∈ Ω，Sat(e, α) 与 Sat(f, α) 的结果完全一致，则 e ≈ f。\"",
  "        map 结果归并 := \"把满足 Principle.条件同一 的表达式映射到同一个 Base.等价类索引 项。\"",
  "",
  "    Space:",
  "        set 定律候选集合 := \"记作 R；表示待判定的候选结果集合。\"",
  "        comb 深度零组合 := \"在 Boundary.变量边界 与常元 0、1 下得到的全部 0 层合法组合：(0, 1, x, y, z)。\"",
  "        comb 交换律候选 := \"深度一组合 与 深度二组合 中，一切形如 (And(a, b), And(b, a)) 与 (Or(a, b), Or(b, a)) 的组合。\"",
  "        comb 定律结果分类 := \"对以上各候选分别应用 Principle.条件同一；凡成立条件完全一致者，归入同一结果类。\"",
  "",
  "    Boundary:",
  "        in<set> 输入变量 := Base.变量集合",
  "        out<set> 输出取值 := Boundary.变量取值边界",
  "        param<set> 变量边界 := \"{x, y, z}\"",
  "        param<set> 变量取值边界 := \"{0, 1}\"",
  "        param<range> 最大嵌套层数 := \"[0:2]\"",
].join("\n");

const MULTILINE_ORDERED_COLLECTION_SAMPLE = [
  "MODULE 子任务提交处理逻辑:SubtaskSubmissionHandler:",
  "    Goal := \"根据已有记录、传入状态和历史完成标记决定处理动作。\"",
  "",
  "    Base:",
  "        set 记录存在状态 := {recorded, unrecorded}",
  "        set 传入完成状态 := {finished, unfinished}",
  "        set 首次完成标记 := {yes, no}",
  "",
  "    Principle:",
  "        sat 子任务不可回退 := 已完成的子任务不可回退为未完成。",
  "",
  "    Space:",
  "        seq 情况总表 := <  <recorded, finished, yes>,",
  "                        <recorded, unfinished, no>,",
  "                        <unrecorded, finished, no>>",
  "",
  "    Boundary:",
  "        in<set> 记录存在状态 := Base.记录存在状态",
  "        in<set> 传入完成状态 := Base.传入完成状态",
  "        out<set> 首次完成标记 := Base.首次完成标记",
].join("\n");

const BASE_SEQ_AND_SPACES_SET_SAMPLE = [
  "MODULE 字符串精确匹配判断器:StringExactMatchJudge:",
  "    Goal := \"判断输入字符串与目标字符串是否完全一致，并输出匹配状态。\"",
  "",
  "    Base:",
  "        elem 字符 := \"记作 c，表示一个基本字符。\"",
  "        struct 字符串对 := \"记作 Pair = <s, p>；表示待比较的一对字符串。\"",
  "        seq 字符串 := \"记作 x = <c1, c2, ..., cn>；其中每个 ci 都属于 Base.字符。\"",
  "        op[2:1] 精确匹配算子 := \"记作 M(s, p)；输入为一对 Base.字符串，输出为 Base.匹配状态。\"",
  "        set 匹配状态 := {yes, no}",
  "",
  "    Principle:",
  "        sat 匹配状态定义 := \"对任意 s, p ∈ Base.字符串，M(s, p) = yes <=> s = p；M(s, p) = no <=> s != p。\"",
  "",
  "    Space:",
  "        set 结果空间 := {<s, p, yes> | s ∈ Base.字符串, p ∈ Base.字符串, s = p} ∪ {<s, p, no> | s ∈ Base.字符串, p ∈ Base.字符串, s != p}",
  "",
  "    Boundary:",
  "        in<string> 输入字符串 := Base.字符串",
  "        in<string> 目标字符串 := Base.字符串",
  "        out<set> 匹配状态 := Base.匹配状态",
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
    (packageJson.files || []).includes("sf_textmate_grammar.js"),
    "package.json must package the .sf textmate grammar generator"
  );
  assert(
    (packageJson.activationEvents || []).includes(`onLanguage:${sfGrammar.SF_LANGUAGE_ID}`),
    "package.json must activate the extension when a .sf file is opened"
  );
  const grammarContribution = (packageJson.contributes?.grammars || []).find(
    (item) => item.language === sfGrammar.SF_LANGUAGE_ID
  );
  assert(grammarContribution, "package.json must contribute a TextMate grammar for the .sf language");
  assert.strictEqual(
    grammarContribution.scopeName,
    "source.shelf-framework",
    "the .sf TextMate grammar must use the shared shelf-framework scope"
  );
  assert.strictEqual(
    grammarContribution.path,
    "./languages/shelf-framework.tmLanguage.json",
    "the .sf TextMate grammar must point at the generated tmLanguage file"
  );
  assert.strictEqual(
    packageJson.contributes?.configurationDefaults?.["[shelf-framework]"]?.["editor.semanticHighlighting.enabled"],
    true,
    "package.json must enable semantic highlighting by default for the .sf language"
  );

  assert(
    extensionSource.includes('language: sfGrammar.SF_LANGUAGE_ID')
      || extensionSource.includes(`language: "${sfGrammar.SF_LANGUAGE_ID}"`),
    "extension.js must register providers for the .sf language id"
  );
  const generatedTextMateGrammar = JSON.parse(readText("languages/shelf-framework.tmLanguage.json"));
  assert.deepStrictEqual(
    generatedTextMateGrammar,
    sfTextMateGrammar.buildShelfFrameworkTextMateGrammar(),
    "the checked-in .sf TextMate grammar must stay aligned with the shared grammar generator"
  );

  const issues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/demo.sf",
    text: VALID_SAMPLE,
  });
  assert.strictEqual(issues.length, 0, "valid .sf sample should pass lint");

  const multilineIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/multiline.sf",
    text: MULTILINE_ORDERED_COLLECTION_SAMPLE,
  });
  assert.strictEqual(
    multilineIssues.length,
    0,
    "multi-line ordered collection values should pass lint when the declaration head is valid"
  );

  const crossBlockKindIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/base-seq-spaces-set.sf",
    text: BASE_SEQ_AND_SPACES_SET_SAMPLE,
  });
  assert.strictEqual(
    crossBlockKindIssues.length,
    0,
    "Base.struct, Base.seq, Base.op, Space.set, and Boundary in/out should pass lint"
  );

  const taskRecorderExampleIssues = sfLint.lintShelfFrameworkFile({
    filePath: path.join(extensionRoot, "examples", "父子任务状态记录模块.sf"),
    text: readText("examples/父子任务状态记录模块.sf"),
  });
  assert.strictEqual(
    taskRecorderExampleIssues.length,
    0,
    "the task-recorder example should stay aligned with the current .sf grammar, including map references separated by Chinese punctuation"
  );

  const pluralHeadingIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/plural-headings.sf",
    text: VALID_SAMPLE
      .replace("    Principle:", "    Principles:")
      .replace("    Space:", "    Spaces:"),
  });
  assert(
    pluralHeadingIssues.some((issue) => issue.code === "SFL003"),
    "plural Principle/Space headings should be rejected now that the grammar uses singular block names"
  );

  const invalidBoundarySample = VALID_SAMPLE.replace("param<range> 最大嵌套层数", "param 最大嵌套层数");
  const invalidBoundaryIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/demo.sf",
    text: invalidBoundarySample,
  });
  assert(
    invalidBoundaryIssues.some((issue) => issue.code === "SFL008"),
    "boundary declarations without subtype should be rejected"
  );
  const invalidBoundaryOpSample = VALID_SAMPLE.replace("in<set> 输入变量 := Base.变量集合", "op[2:1] 输入边界 := \"<x> -> y\"");
  const invalidBoundaryOpIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/demo.sf",
    text: invalidBoundaryOpSample,
  });
  assert(
    invalidBoundaryOpIssues.some((issue) => issue.code === "SFL008"),
    "boundary declarations must reject op statements and keep only in/out/param forms"
  );

  const invalidModuleSample = VALID_SAMPLE.replace(/^MODULE/u, "module");
  const invalidModuleIssues = sfLint.lintShelfFrameworkFile({
    filePath: "/tmp/demo.sf",
    text: invalidModuleSample,
  });
  assert(
    invalidModuleIssues.some((issue) => issue.code === "SFL001"),
    "lowercase module headers should be rejected"
  );

  const tokens = sfGrammar.collectShelfFrameworkSemanticTokens(VALID_SAMPLE);
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.statementKeyword));
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.declarationName));
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.reference));
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.shape));
  assert(tokens.some((token) => token.tokenType === sfGrammar.SEMANTIC_TOKEN_TYPES.subtype));

  const fileEntries = sfCompletion.getShelfFrameworkCompletionEntries("", "", {
    documentText: "",
    lineNumber: 0,
  });
  assert(
    fileEntries.some((entry) => entry.label === "MODULE 中文模块名:EnglishName:"),
    "empty .sf document should offer the MODULE declaration"
  );
  assert(
    fileEntries.some((entry) => entry.label === "shelf-framework 标准模板"),
    "empty .sf document should offer the full template"
  );

  const baseEntries = sfCompletion.getShelfFrameworkCompletionEntries("        ", "", {
    documentText: VALID_SAMPLE,
    lineNumber: lineIndexOf(VALID_SAMPLE, "Base:") + 1,
  });
  assert(
    baseEntries.some((entry) => entry.label === "op[2:1]"),
    "base context must offer op[2:1]"
  );
  assert(
    baseEntries.some((entry) => entry.label === "set"),
    "base context must offer set"
  );
  assert(
    baseEntries.some((entry) => entry.label === "struct"),
    "base context must offer struct"
  );
  assert(
    baseEntries.some((entry) => entry.label === "seq"),
    "base context must offer seq"
  );
  assert(
    baseEntries.some((entry) => entry.label === "map"),
    "base context must offer map"
  );

  const principlesEntries = sfCompletion.getShelfFrameworkCompletionEntries("        ", "", {
    documentText: VALID_SAMPLE,
    lineNumber: lineIndexOf(VALID_SAMPLE, "Principle:") + 1,
  });
  assert(
    principlesEntries.some((entry) => entry.label === "map"),
    "principle context must offer map"
  );
  assert(
    !principlesEntries.some((entry) => entry.label === "op[2:1]"),
    "principle context must not offer op[2:1]"
  );

  const spacesEntries = sfCompletion.getShelfFrameworkCompletionEntries("        ", "", {
    documentText: VALID_SAMPLE,
    lineNumber: lineIndexOf(VALID_SAMPLE, "Space:") + 1,
  });
  assert(
    spacesEntries.some((entry) => entry.label === "set"),
    "space context must offer set"
  );
  assert(
    spacesEntries.some((entry) => entry.label === "comb"),
    "space context must offer comb"
  );

  const boundaryEntries = sfCompletion.getShelfFrameworkCompletionEntries("        ", "", {
    documentText: VALID_SAMPLE,
    lineNumber: lineIndexOf(VALID_SAMPLE, "Boundary:") + 1,
  });
  assert(
    !boundaryEntries.some((entry) => entry.label === "op[2:1]"),
    "boundary context must not offer op[2:1]"
  );
  assert(
    boundaryEntries.some((entry) => entry.label === "in<subtype>"),
    "boundary context must offer in<subtype>"
  );
  assert(
    boundaryEntries.some((entry) => entry.label === "out<subtype>"),
    "boundary context must offer out<subtype>"
  );
  assert(
    boundaryEntries.some((entry) => entry.label === "param<set>"),
    "boundary context must offer param<set>"
  );
  assert(
    boundaryEntries.some((entry) => entry.label === "param<range>"),
    "boundary context must offer param<range>"
  );
}

main();

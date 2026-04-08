const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const {
  classifyFrameworkMarkdown,
  isControlledFrameworkPath,
  lintFrameworkMarkdown,
  lintFrameworkWorkspace,
} = require("./framework_lint");

const VALID_FRAMEWORK_TEXT = [
  "# 知识库文本单元模块:KnowledgeBaseTextUnitModule",
  "",
  "@framework",
  "",
  "## Goal",
  "",
  "goal 文本单元定位 := 在给定输入下定位并返回文本单元",
  "",
  "## Base",
  "",
  "base 文本索引基 := 用于索引定位",
  "base 文本载荷基 := 用于承载原文",
  "",
  "## Combination Principles",
  "",
  "cp.form 文本定位组合 on <base.文本索引基, base.文本载荷基> := 同时具备定位与读取能力",
  "cp.sat 文本定位组合 on cs.可读取文本单元 := 输入必须包含可解析查询",
  "cp.id 文本定位组合 on cs.可读取文本单元 := 相同输入产生同一定位结果",
  "cp.norm 文本定位组合 on cs.可读取文本单元 := 标准写法以 cs.可读取文本单元 为准",
  "",
  "## Combination Space",
  "",
  "cs.可读取文本单元 := <base.文本索引基, base.文本载荷基> by <cp.form.文本定位组合, cp.sat.文本定位组合, cp.id.文本定位组合, cp.norm.文本定位组合>",
  "",
  "## Boundary",
  "",
  "### Input",
  "",
  "bd.in 查询输入 := payload({query}), cardinality(1), to(cs.可读取文本单元)",
  "",
  "### Output",
  "",
  "bd.out 文本输出 := payload({text}), cardinality(0..1), from(cs.可读取文本单元)",
  "",
  "### Parameter",
  "",
  "bd.param 查询长度上限 := domain(int), affects(cs.可读取文本单元, bd.in.查询输入)",
].join("\n");

function writeFile(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text, "utf8");
}

function withTempRepo(run) {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-framework-lint-"));
  try {
    run(repoRoot);
  } finally {
    fs.rmSync(repoRoot, { recursive: true, force: true });
  }
}

function runLint(repoRoot, relativePath, text) {
  const filePath = path.join(repoRoot, relativePath);
  writeFile(filePath, text);
  return lintFrameworkMarkdown({
    repoRoot,
    filePath,
    text,
  });
}

function main() {
  assert.strictEqual(isControlledFrameworkPath("framework/demo/L0-M0-示例模块.md"), true);
  assert.strictEqual(isControlledFrameworkPath("framework_drafts/demo/docs/ref.md"), true);
  assert.strictEqual(isControlledFrameworkPath("docs/demo.md"), false);

  withTempRepo((repoRoot) => {
    const validIssues = runLint(repoRoot, "framework/backend/L0-M0-测试模块.md", VALID_FRAMEWORK_TEXT);
    assert.strictEqual(validIssues.length, 0, "valid keyword-first framework should not produce lint issues");

    const oldStyleHeadingText = VALID_FRAMEWORK_TEXT.replace("## Base", "## Capability");
    const oldStyleHeadingIssues = runLint(repoRoot, "framework/backend/L0-M0-测试模块.md", oldStyleHeadingText);
    assert(
      oldStyleHeadingIssues.some((issue) => issue.code === "FWL012"),
      "invalid heading sequence should be rejected by framework lint"
    );

    const missingBoundarySubsectionText = VALID_FRAMEWORK_TEXT.replace(
      "### Output\n\nbd.out 文本输出 := payload({text}), cardinality(0..1), from(cs.可读取文本单元)\n\n",
      ""
    );
    const missingBoundarySubsectionIssues = runLint(
      repoRoot,
      "framework/backend/L0-M0-测试模块.md",
      missingBoundarySubsectionText
    );
    assert(
      missingBoundarySubsectionIssues.some((issue) => issue.code === "FWL006"),
      "missing boundary subsection should be reported"
    );

    const listStyleText = VALID_FRAMEWORK_TEXT.replace(
      "base 文本索引基 := 用于索引定位",
      "- base 文本索引基 := 用于索引定位"
    );
    const listStyleIssues = runLint(repoRoot, "framework/backend/L0-M0-测试模块.md", listStyleText);
    assert(
      listStyleIssues.some((issue) => issue.code === "FWL004"),
      "list markers should be rejected by keyword-first lint"
    );

    const invalidCombinationText = VALID_FRAMEWORK_TEXT.replace(
      "cp.form 文本定位组合 on <base.文本索引基, base.文本载荷基> := 同时具备定位与读取能力",
      "cp.form 文本定位组合 := 同时具备定位与读取能力"
    );
    const invalidCombinationIssues = runLint(
      repoRoot,
      "framework/backend/L0-M0-测试模块.md",
      invalidCombinationText
    );
    assert(
      invalidCombinationIssues.some((issue) => issue.code === "FWL008"),
      "cp statements must include `on ... := ...`"
    );

    const missingSymbolText = VALID_FRAMEWORK_TEXT.replace(
      "cs.可读取文本单元 := <base.文本索引基, base.文本载荷基> by <cp.form.文本定位组合, cp.sat.文本定位组合, cp.id.文本定位组合, cp.norm.文本定位组合>",
      "cs.可读取文本单元 := <base.文本索引基, base.不存在基> by <cp.form.文本定位组合, cp.sat.文本定位组合, cp.id.文本定位组合, cp.norm.文本定位组合>"
    );
    const missingSymbolIssues = runLint(repoRoot, "framework/backend/L0-M0-测试模块.md", missingSymbolText);
    assert(
      missingSymbolIssues.some(
        (issue) => issue.code === "FWL011" && String(issue.message || "").includes("base.不存在基")
      ),
      "undefined symbol references should be reported"
    );

    const forbiddenLegacyText = VALID_FRAMEWORK_TEXT.replace(
      "goal 文本单元定位 := 在给定输入下定位并返回文本单元",
      "goal 文本单元定位 := 在给定输入下定位并返回文本单元。详见 projects/demo/project.toml"
    );
    const forbiddenLegacyIssues = runLint(repoRoot, "framework/backend/L0-M0-测试模块.md", forbiddenLegacyText);
    assert(
      forbiddenLegacyIssues.some((issue) => issue.code === "FWL015"),
      "legacy forbidden patterns should be reported"
    );

    const externalFrameworkPath = path.join(repoRoot, "docs", "outside-framework.md");
    const externalFrameworkIssues = lintFrameworkMarkdown({
      repoRoot,
      filePath: externalFrameworkPath,
      text: VALID_FRAMEWORK_TEXT,
    });
    assert(
      externalFrameworkIssues.some((issue) => issue.code === "FWL016"),
      "@framework outside controlled module path should be rejected"
    );

    const classification = classifyFrameworkMarkdown({
      repoRoot,
      filePath: path.join(repoRoot, "framework", "backend", "L0-M0-测试模块.md"),
      text: VALID_FRAMEWORK_TEXT,
    });
    assert.strictEqual(classification.shouldLint, true);
    assert.strictEqual(classification.isModulePath, true);
    assert.strictEqual(classification.isFrameworkModuleDocument, true);
  });

  withTempRepo((repoRoot) => {
    writeFile(
      path.join(repoRoot, "framework", "demo", "L0-M0-示例模块.md"),
      VALID_FRAMEWORK_TEXT.replace(
        "goal 文本单元定位 := 在给定输入下定位并返回文本单元",
        "goal 文本单元定位 := 在给定输入下定位并返回文本单元，参考 [说明](docs/引用.md)"
      )
    );
    writeFile(path.join(repoRoot, "framework", "demo", "docs", "引用.md"), "# 引用\n");
    const workspaceIssues = lintFrameworkWorkspace({ repoRoot });
    assert.strictEqual(workspaceIssues.length, 0, "directly referenced attachment markdown should be accepted");
  });

  withTempRepo((repoRoot) => {
    writeFile(
      path.join(repoRoot, "framework", "demo", "L0-M0-示例模块.md"),
      VALID_FRAMEWORK_TEXT
    );
    writeFile(path.join(repoRoot, "framework", "demo", "docs", "孤立.md"), "# 孤立\n");
    const workspaceIssues = lintFrameworkWorkspace({ repoRoot });
    assert(
      workspaceIssues.some(
        (issue) => issue.code === "FWL018" && String(issue.file || "").endsWith("framework/demo/docs/孤立.md")
      ),
      "unreferenced attachment markdown should be reported"
    );
  });

  withTempRepo((repoRoot) => {
    writeFile(path.join(repoRoot, "docs", "外部.md"), "# 外部\n");
    writeFile(
      path.join(repoRoot, "framework", "demo", "L0-M0-示例模块.md"),
      VALID_FRAMEWORK_TEXT.replace(
        "goal 文本单元定位 := 在给定输入下定位并返回文本单元",
        "goal 文本单元定位 := 在给定输入下定位并返回文本单元，外部引用 [外部](../../docs/外部.md)"
      )
    );
    const workspaceIssues = lintFrameworkWorkspace({ repoRoot });
    assert(
      workspaceIssues.some((issue) => issue.code === "FWL017"),
      "module links to markdown outside the controlled framework scope should be rejected"
    );
  });

  withTempRepo((repoRoot) => {
    writeFile(
      path.join(repoRoot, "framework", "demo", "docs", "错误附件.md"),
      VALID_FRAMEWORK_TEXT
    );
    const workspaceIssues = lintFrameworkWorkspace({ repoRoot });
    assert(
      workspaceIssues.some((issue) => issue.code === "FWL016"),
      "attachment markdown inside framework scope must not declare @framework"
    );
  });
}

main();

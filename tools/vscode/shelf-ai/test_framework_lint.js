const assert = require("assert");
const path = require("path");

const { lintFrameworkMarkdown } = require("./framework_lint");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

const VALID_FRAMEWORK_TEXT = [
  "# 知识库文本单元模块:KnowledgeBaseTextUnitModule",
  "",
  "@framework",
  "",
  "## 0. 目标 (Goal)",
  "",
  "- 目标说明。",
  "",
  "## 1. 最小结构基（Minimal Structural Bases）",
  "",
  "- `B1` 文本索引基：用于索引定位。",
  "- `B2` 文本载荷基：用于承载原文。",
  "",
  "## 2. 基排列组合（Base Arrangement / Combination）",
  "",
  "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`，导出 `C1`。",
  "",
  "## 3. 边界定义（Boundary）",
  "",
  "### 3.1 接口定义（IO / Ports）",
  "",
  "- `QUERY_IN`：运行时输入接口，接收单个查询。",
  "- `TEXT_OUT`：运行时输出接口，导出文本单元。",
  "",
  "### 3.2 参数边界（Parameter Constraints）",
  "",
  "- `P1` 查询长度：约束查询长度上限。",
  "",
  "## 4. 能力声明（Capability Statement）",
  "",
  "- `C1` 文本定位能力：支持定位并读取文本单元。",
  "- `N1` 非职责声明：不负责复杂语义检索。",
].join("\n");

function runLint(text) {
  return lintFrameworkMarkdown({
    repoRoot,
    filePath: path.join(repoRoot, "framework", "backend", "L0-M0-测试模块.md"),
    text,
  });
}

function main() {
  const validIssues = runLint(VALID_FRAMEWORK_TEXT);
  assert.strictEqual(validIssues.length, 0, "valid new framework template should not produce lint issues");

  const snakeCaseParameterText = VALID_FRAMEWORK_TEXT.replace(
    "- `P1` 查询长度：约束查询长度上限。",
    "- `query_length` 查询长度：约束查询长度上限。"
  );
  const snakeCaseParameterIssues = runLint(snakeCaseParameterText);
  assert.strictEqual(
    snakeCaseParameterIssues.length,
    0,
    "snake_case parameter ids should be accepted by framework lint"
  );

  const oldStyleHeadingText = VALID_FRAMEWORK_TEXT
    .replace(
      "## 1. 最小结构基（Minimal Structural Bases）",
      "## 1. 能力声明（Capability Statement）"
    )
    .replace(
      "## 4. 能力声明（Capability Statement）",
      "## 5. 验证（Verification）"
    );
  const oldStyleHeadingIssues = runLint(oldStyleHeadingText);
  assert(
    oldStyleHeadingIssues.some((issue) => issue.code === "FWL012"),
    "old heading sequence should be rejected by new lint rules"
  );

  const missingBoundarySubsectionText = VALID_FRAMEWORK_TEXT.replace(
    "### 3.2 参数边界（Parameter Constraints）\n\n- `P1` 查询长度：约束查询长度上限。\n\n",
    ""
  );
  const missingBoundarySubsectionIssues = runLint(missingBoundarySubsectionText);
  assert(
    missingBoundarySubsectionIssues.some((issue) => issue.code === "FWL006"),
    "missing boundary subsection 3.2 should be reported"
  );

  const starText = VALID_FRAMEWORK_TEXT.replace(
    "- `B1` 文本索引基：用于索引定位。",
    "* `B1` 文本索引基：用于索引定位。"
  );
  const starIssues = runLint(starText);
  assert(starIssues.some((issue) => issue.code === "FWL004"), "star list marker should be rejected");

  const oldRuleChildText = VALID_FRAMEWORK_TEXT.replace(
    "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`，导出 `C1`。",
    "- `R1` `文本定位组合`\n  - `R1.1` 参与基：`B1 + B2`。"
  );
  const oldRuleChildIssues = runLint(oldRuleChildText);
  assert(
    oldRuleChildIssues.some((issue) => issue.code === "FWL008"),
    "old rule child format should be rejected by new lint rules"
  );

  const missingCapabilityRefText = VALID_FRAMEWORK_TEXT.replace(
    "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`，导出 `C1`。",
    "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`，导出 `C2`。"
  );
  const missingCapabilityRefIssues = runLint(missingCapabilityRefText);
  assert(
    missingCapabilityRefIssues.some(
      (issue) => issue.code === "FWL011" && String(issue.message || "").includes("`C2`")
    ),
    "undefined capability reference should be reported"
  );

  const duplicateCapabilityText = `${VALID_FRAMEWORK_TEXT}\n- \`C1\` 重复能力：重复定义。`;
  const duplicateCapabilityIssues = runLint(duplicateCapabilityText);
  assert(
    duplicateCapabilityIssues.some((issue) => issue.code === "FWL013"),
    "duplicate C/N/B/R ids should be reported"
  );

  const missingRuleOutcomeText = VALID_FRAMEWORK_TEXT.replace(
    "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`，导出 `C1`。",
    "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`。"
  );
  const missingRuleOutcomeIssues = runLint(missingRuleOutcomeText);
  assert(
    missingRuleOutcomeIssues.some((issue) => issue.code === "FWL014"),
    "rule must declare C* output or N* invalid conclusion"
  );

  const missingBoundaryRefText = VALID_FRAMEWORK_TEXT.replace(
    "- `R1` `文本定位组合`：由 `{B1, B2}` 形成 `可读取单元`，导出 `C1`。",
    "- `R1` `文本定位组合`：由 `{B1, B2}` 在 `missing_param` 约束下形成 `可读取单元`，导出 `C1`。"
  );
  const missingBoundaryRefIssues = runLint(missingBoundaryRefText);
  assert(
    missingBoundaryRefIssues.some(
      (issue) => issue.code === "FWL011" && String(issue.message || "").includes("missing_param")
    ),
    "undefined boundary symbol referenced by rule should be reported"
  );

  const forbiddenLegacyText = VALID_FRAMEWORK_TEXT
    .replace("- `B1` 文本索引基：用于索引定位。", "- `B1` 文本索引基：用于索引定位。上游模块：L0.M0")
    .replace("- `N1` 非职责声明：不负责复杂语义检索。", "- `N1` 非职责声明：详见 projects/demo/project.toml。");
  const forbiddenLegacyIssues = runLint(forbiddenLegacyText);
  assert(
    forbiddenLegacyIssues.some((issue) => issue.code === "FWL015"),
    "legacy forbidden patterns should be reported"
  );

  const invalidParameterIdText = VALID_FRAMEWORK_TEXT.replace(
    "- `P1` 查询长度：约束查询长度上限。",
    "- `123` 查询长度：约束查询长度上限。"
  );
  const invalidParameterIdIssues = runLint(invalidParameterIdText);
  assert(
    invalidParameterIdIssues.some((issue) => issue.code === "FWL006"),
    "parameter id should start with alphabetic character"
  );
}

main();

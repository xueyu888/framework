const assert = require("assert");
const path = require("path");

const { lintFrameworkMarkdown } = require("./framework_lint");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

const VALID_FRAMEWORK_TEXT = [
  "# 知识库文本单元模块:KnowledgeBaseTextUnitModule",
  "",
  "@framework",
  "",
  "## 1. 能力声明（Capability Statement）",
  "",
  "- `C1` 单元定位能力：支持通过定位键唯一定位文本单元。",
  "- `N1` 非职责声明：不负责复杂语义检索。",
  "",
  "## 2. 边界定义（Boundary / Parameter 参数）",
  "",
  "- `P1` 文档标识参数：用于限定文本单元所属文档。来源：`C1`。",
  "",
  "## 3. 最小结构基（Minimal Structural Bases）",
  "",
  "- `B1` 文本索引基：L0.M0[R1]。来源：`C1 + P1`。",
  "",
  "## 4. 基组合原则（Base Combination Principles）",
  "",
  "- `R1` 文本定位组合",
  "  - `R1.1` 参与基：`B1`。",
  "  - `R1.2` 组合方式：按索引优先，再做局部过滤。",
  "  - `R1.3` 输出能力：`C1`。",
  "  - `R1.4` 参数绑定：`P1`。",
  "",
  "## 5. 验证（Verification）",
  "",
  "- `V1` 定位验证：给定定位键时必须返回唯一文本单元。",
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
  assert.strictEqual(validIssues.length, 0, "valid framework text should not produce lint issues");

  const validWithGoalText = VALID_FRAMEWORK_TEXT.replace(
    "## 1. 能力声明（Capability Statement）",
    "## 0. 目标\n\n目标说明。\n\n## 1. 能力声明（Capability Statement）"
  );
  const validWithGoalIssues = runLint(validWithGoalText);
  assert.strictEqual(validWithGoalIssues.length, 0, "optional ## 0 goal section should remain valid");

  const starText = VALID_FRAMEWORK_TEXT.replace(
    "- `C1` 单元定位能力：支持通过定位键唯一定位文本单元。",
    "* `C1` 单元定位能力：支持通过定位键唯一定位文本单元。"
  );
  const starIssues = runLint(starText);
  assert(starIssues.some((issue) => issue.code === "FWL004"), "star list marker should be rejected");

  const wrongSectionTitleText = VALID_FRAMEWORK_TEXT.replace(
    "## 2. 边界定义（Boundary / Parameter 参数）",
    "## 2. 参数说明"
  );
  const wrongSectionTitleIssues = runLint(wrongSectionTitleText);
  const wrongSectionTitleLine = wrongSectionTitleText.split("\n").indexOf("## 2. 参数说明") + 1;
  assert(
    wrongSectionTitleIssues.some(
      (issue) => issue.code === "FWL012" && issue.line === wrongSectionTitleLine
    ),
    "wrong second-level heading should be reported on the exact heading line"
  );

  const missingSectionText = VALID_FRAMEWORK_TEXT.replace(
    "## 5. 验证（Verification）\n\n- `V1` 定位验证：给定定位键时必须返回唯一文本单元。",
    ""
  );
  const missingIssues = runLint(missingSectionText);
  assert(
    missingIssues.some((issue) => issue.code === "FWL003"),
    "missing required trailing section should still be reported"
  );

  const misplacedThirdLevelText = VALID_FRAMEWORK_TEXT.replace(
    "## 2. 边界定义（Boundary / Parameter 参数）",
    "## 2. 边界定义（Boundary / Parameter 参数）\n\n### 乱写的小标题"
  );
  const misplacedThirdLevelIssues = runLint(misplacedThirdLevelText);
  assert(
    !misplacedThirdLevelIssues.some((issue) => issue.code === "FWL006"),
    "third-level headings should be tolerated as neutral separators"
  );

  const missingCapabilityRefText = VALID_FRAMEWORK_TEXT.replace(
    "  - `R1.3` 输出能力：`C1`。",
    "  - `R1.3` 输出能力：`C1 + C2`。"
  );
  const missingCapabilityRefIssues = runLint(missingCapabilityRefText);
  assert(
    missingCapabilityRefIssues.some(
      (issue) => issue.code === "FWL011" && String(issue.message || "").includes("`C2`")
    ),
    "undefined capability reference should be reported"
  );
}

main();

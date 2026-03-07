const assert = require("assert");
const fs = require("fs");
const path = require("path");

const {
  resolveDefinitionTarget,
} = require("./framework_navigation");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function loadFrameworkFile(relativePath) {
  const filePath = path.join(repoRoot, relativePath);
  return {
    filePath,
    text: fs.readFileSync(filePath, "utf8"),
  };
}

function locate(text, needle) {
  const index = text.indexOf(needle);
  assert.notStrictEqual(index, -1, `missing needle: ${needle}`);
  const before = text.slice(0, index);
  const line = before.split(/\r?\n/).length - 1;
  const lineStart = before.lastIndexOf("\n") + 1;
  return {
    line,
    character: index - lineStart,
  };
}

function targetLineText(result) {
  const text = fs.readFileSync(result.filePath, "utf8");
  return text.split(/\r?\n/)[result.line] || "";
}

function main() {
  const curtainL2 = loadFrameworkFile("framework/curtain/L2-M0-窗帘框架标准模块.md");
  const capRef = locate(curtainL2.text, "C1 + SPAN");
  const capResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: capRef.line,
    character: capRef.character,
  });
  assert(capResult, "capability ref should resolve");
  assert(capResult.filePath.endsWith("framework/curtain/L2-M0-窗帘框架标准模块.md"));
  assert(targetLineText(capResult).includes("`C1`"));

  const boundaryRef = locate(curtainL2.text, "SPAN + LOAD");
  const boundaryResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: boundaryRef.line,
    character: boundaryRef.character,
  });
  assert(boundaryResult, "boundary ref should resolve");
  assert(targetLineText(boundaryResult).includes("`SPAN`"));

  const baseRef = locate(curtainL2.text, "`B1 + B2`");
  const baseResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: baseRef.line,
    character: baseRef.character + 1,
  });
  assert(baseResult, "base ref should resolve");
  assert(targetLineText(baseResult).includes("`B1`"));

  const verifyRef = locate(curtainL2.text, "`R1` 必须满足");
  const verifyResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: verifyRef.line,
    character: verifyRef.character + 1,
  });
  assert(verifyResult, "verification rule ref should resolve");
  assert(targetLineText(verifyResult).includes("`R1`"));

  const moduleRef = locate(curtainL2.text, "L1.M0[R1]");
  const moduleResult = resolveDefinitionTarget({
    repoRoot,
    filePath: curtainL2.filePath,
    text: curtainL2.text,
    line: moduleRef.line,
    character: moduleRef.character + 1,
  });
  assert(moduleResult, "module ref should resolve");
  assert(moduleResult.filePath.endsWith("framework/curtain/L1-M0-安装与控制编排模块.md"));
  assert(targetLineText(moduleResult).startsWith("# "));

  const knowledgeBaseL0 = loadFrameworkFile("framework/knowledge_base/L0-M0-文件库与摄取原子模块.md");
  const externalRuleRef = locate(knowledgeBaseL0.text, "frontend.L1.M4[R1,R3]");
  const externalRuleResult = resolveDefinitionTarget({
    repoRoot,
    filePath: knowledgeBaseL0.filePath,
    text: knowledgeBaseL0.text,
    line: externalRuleRef.line,
    character: externalRuleRef.character + "frontend.L1.M4[".length + 3,
  });
  assert(externalRuleResult, "external rule ref should resolve");
  assert(externalRuleResult.filePath.endsWith("framework/frontend/L1-M4-文本块原子模块.md"));
  assert(targetLineText(externalRuleResult).includes("`R3`"));
}

main();

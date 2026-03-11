const assert = require("assert");
const path = require("path");

const { classifyWorkspaceChanges, readGovernanceTree, summarizeChangeContext } = require("./governance_tree");

const repoRoot = path.resolve(__dirname, "..", "..", "..");

function main() {
  const payload = readGovernanceTree(repoRoot, path.join("docs", "hierarchy", "shelf_governance_tree.json"));

  const frameworkPlan = classifyWorkspaceChanges(
    repoRoot,
    ["framework/knowledge_base/L2-M0-知识库工作台场景模块.md"],
    payload
  );
  assert(frameworkPlan.shouldMaterialize, "framework governance node changes should trigger materialization");
  assert(
    frameworkPlan.materializeProjects.some((item) => item.endsWith("projects/knowledge_base_basic/product_spec.toml")),
    "framework governance nodes should map to the knowledge base project"
  );
  assert(
    frameworkPlan.changeContext.affectedNodes.some((item) => item.includes("kb.answer.behavior")),
    "framework change should propagate to affected code symbols"
  );

  const codePlan = classifyWorkspaceChanges(
    repoRoot,
    ["src/knowledge_base_runtime/backend.py"],
    payload
  );
  assert.strictEqual(codePlan.shouldMaterialize, false, "code-only governed changes should not auto-materialize");
  assert(
    codePlan.changeContext.touchedNodes.some((item) => item.includes("kb.answer.behavior")),
    "code change should resolve touched governed code symbols"
  );

  const summary = summarizeChangeContext(payload, frameworkPlan.changeContext, 2);
  assert(summary.touchedCount >= 1, "change summary should expose touched-node count");
  assert(summary.affectedCount >= summary.touchedCount, "change summary should expose affected-node count");
}

main();

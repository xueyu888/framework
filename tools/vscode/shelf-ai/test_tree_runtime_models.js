const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const {
  buildRuntimeEvidenceTreeModel,
  buildRuntimeFrameworkTreeModel,
  buildRuntimeTreeModel,
} = require("./tree_runtime_models");

function writeFile(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
}

function createFrameworkAuthorGraphFixture() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-tree-runtime-author-"));
  const frameworkL0 = path.join(fixtureRoot, "framework", "demo", "L0-M0-source.md");
  const frameworkL1 = path.join(fixtureRoot, "framework", "demo", "L1-M0-aggregate.md");
  const projectFile = path.join(fixtureRoot, "projects", "demo", "project.toml");
  const canonicalPath = path.join(fixtureRoot, "projects", "demo", "generated", "canonical.json");
  const codeLayerPath = path.join(fixtureRoot, "src", "project_runtime", "code_layer.py");
  const evidenceLayerPath = path.join(fixtureRoot, "src", "project_runtime", "evidence_layer.py");

  writeFile(
    frameworkL0,
    [
      "# L0-M0 Source Module",
      "",
      "## 3. 最小结构基（Minimal Structural Bases）",
      "- `B1` 输入载荷基：消息内容。",
      "",
      "## 4. 基组合原则（Base Combination Principles）",
      "- `R1` 最小组合",
      "  - `R1.1` 参与基：`B1`。",
      "",
    ].join("\n")
  );
  writeFile(
    frameworkL1,
    [
      "# L1-M0 Aggregate Module",
      "",
      "## 3. 最小结构基（Minimal Structural Bases）",
      "- `B1` 上游聚合基：L0.M0[R1]。",
      "- `B2` 输出结构基：聚合后的输出。",
      "",
      "## 4. 基组合原则（Base Combination Principles）",
      "- `R2` 聚合组合",
      "  - `R2.1` 参与基：`B1 + B2`。",
      "",
    ].join("\n")
  );
  writeFile(
    projectFile,
    [
      "[project]",
      "project_id = \"demo\"",
      "",
      "[framework]",
      "",
      "[[framework.modules]]",
      "role = \"demo\"",
      "framework_file = \"framework/demo/L1-M0-aggregate.md\"",
      "",
    ].join("\n")
  );
  writeFile(codeLayerPath, "def demo():\n    return 'ok'\n");
  writeFile(evidenceLayerPath, "def evidence():\n    return 'ok'\n");
  writeFile(
    canonicalPath,
    JSON.stringify(
      {
        project: {
          project_id: "demo",
          display_name: "demo",
          version: "0.0.1",
          description: "demo fixture",
        },
        framework: {
          modules: [
            {
              module_id: "demo.L0.M0",
              framework_file: "framework/demo/L0-M0-source.md",
            },
            {
              module_id: "demo.L1.M0",
              framework_file: "framework/demo/L1-M0-aggregate.md",
            },
          ],
        },
        config: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: { file_path: "projects/demo/project.toml", line: 1 },
            },
            {
              module_id: "demo.L1.M0",
              source_ref: { file_path: "projects/demo/project.toml", line: 1 },
            },
          ],
        },
        code: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: { file_path: "src/project_runtime/code_layer.py", line: 1 },
            },
            {
              module_id: "demo.L1.M0",
              source_ref: { file_path: "src/project_runtime/code_layer.py", line: 1 },
            },
          ],
        },
        evidence: {
          modules: [
            {
              module_id: "demo.L0.M0",
              source_ref: { file_path: "src/project_runtime/evidence_layer.py", line: 1 },
            },
            {
              module_id: "demo.L1.M0",
              source_ref: { file_path: "src/project_runtime/evidence_layer.py", line: 1 },
            },
          ],
        },
      },
      null,
      2
    )
  );

  return fixtureRoot;
}

function createFrameworkOnlyFixtureWithoutProjects() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "shelf-tree-runtime-fw-only-"));
  const frameworkL0 = path.join(fixtureRoot, "framework", "demo", "L0-M0-source.md");
  writeFile(
    frameworkL0,
    [
      "# L0-M0 Source Module",
      "",
      "## 3. 最小结构基（Minimal Structural Bases）",
      "- `B1` 输入基。",
      "",
      "## 4. 基组合原则（Base Combination Principles）",
      "- `R1` 最小组合",
      "  - `R1.1` 参与基：`B1`。",
      "",
    ].join("\n")
  );
  return fixtureRoot;
}

function main() {
  const authorFixtureRoot = createFrameworkAuthorGraphFixture();
  try {
    const frameworkModel = buildRuntimeFrameworkTreeModel(authorFixtureRoot);
    assert.strictEqual(frameworkModel.kind, "framework");
    assert(
      frameworkModel.layoutMode === "framework_columns",
      "framework model should use framework_columns layout"
    );
    assert(
      Array.isArray(frameworkModel.frameworkGroups) && frameworkModel.frameworkGroups.length > 0,
      "framework model should include framework groups"
    );
    const moduleNodes = frameworkModel.nodes.filter((node) => node.kind === "framework_module");
    const baseNodes = frameworkModel.nodes.filter((node) => node.kind === "framework_base");
    assert(moduleNodes.length >= 2, "framework model should include module nodes from framework files");
    assert(baseNodes.length >= 3, "framework model should include base nodes from module B* declarations");
    assert(
      frameworkModel.edges.some((edge) => edge.relation === "module_contains_base"),
      "framework model should include module->base containment edges"
    );
    assert(
      frameworkModel.edges.some((edge) => edge.relation === "base_composition"),
      "framework model should include base composition edges from R*.1 participant bases"
    );
    assert(
      frameworkModel.edges.some((edge) =>
        edge.relation === "framework_module_growth"
        && edge.from === "demo.L0.M0"
        && edge.to === "demo.L1.M0"
      ),
      "framework model should include upstream module growth edges from base references like L0.M0[...]"
    );
    assert(
      frameworkModel.description.includes("no project config selection is required"),
      "framework model description should explicitly state no project config dependency"
    );
    assert(
      frameworkModel.levelLabels && Object.values(frameworkModel.levelLabels).some((label) => label.includes("基层")),
      "framework model should expose author labels for base rows"
    );

    const evidenceModel = buildRuntimeEvidenceTreeModel(authorFixtureRoot);
    assert.strictEqual(evidenceModel.kind, "evidence");
    assert(evidenceModel.nodes.length > 0, "evidence model should have nodes");
    assert(evidenceModel.layoutMode === "global_levels", "evidence model should keep global layout");
    assert(
      evidenceModel.edges.every((edge) => edge.relation === "tree_child"),
      "evidence edges should stay in tree_child relation"
    );

    const frameworkViaDispatcher = buildRuntimeTreeModel(authorFixtureRoot, "framework");
    const evidenceViaDispatcher = buildRuntimeTreeModel(authorFixtureRoot, "evidence");
    assert.strictEqual(frameworkViaDispatcher.kind, "framework");
    assert.strictEqual(evidenceViaDispatcher.kind, "evidence");
  } finally {
    fs.rmSync(authorFixtureRoot, { recursive: true, force: true });
  }

  const frameworkOnlyFixture = createFrameworkOnlyFixtureWithoutProjects();
  try {
    const frameworkModel = buildRuntimeFrameworkTreeModel(frameworkOnlyFixture);
    assert.strictEqual(frameworkModel.kind, "framework");
    assert(
      frameworkModel.nodes.some((node) => node.kind === "framework_module"),
      "framework-only fixture should still render module nodes without project config/canonical"
    );
    assert(
      frameworkModel.nodes.some((node) => node.kind === "framework_base"),
      "framework-only fixture should still render base nodes without project config/canonical"
    );
  } finally {
    fs.rmSync(frameworkOnlyFixture, { recursive: true, force: true });
  }
}

main();

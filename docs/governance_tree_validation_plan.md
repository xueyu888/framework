# 治理树校验方案（草案）

## 1. 结论

当前仓库已经具备一条可工作的“知识库高风险行为治理链”，但它还不是理想形态。

现状更准确的表述是：

- 仓库已经有一棵 **L0-L3 标准树**，用于表达 `specs -> framework -> mapping`。
- 知识库项目又额外有一套 **manifest 驱动的符号治理链**，用于表达 `Product Spec -> Implementation Config -> Code -> Evidence` 的局部闭环。

所以当前状态不是“一棵树管到底”，而是：

- `标准树`
- `项目治理 manifest`

这两套系统目前能够配合工作，但结构上仍然是双系统。

本草案主张把治理中心改成：

**Framework -> Product Spec -> Implementation Config -> Code -> Evidence 全部挂在一棵治理树上。**

树是主模型；校验器内部可以保留少量 `depends_on / derived_from` 依赖边做闭包计算，但对人和 AI 暴露的第一视角应该始终是一棵树。

## 2. 本次详细验证

### 2.1 标准树现状

仓库当前已经存在正式树模型，但它只覆盖标准层：

- [规范总纲与树形结构.md](/home/xue/code/shelf/specs/规范总纲与树形结构.md#L124) 明确规定 `mapping/mapping_registry.json` 的 `tree` 只表达 L0-L3 标准树。
- [mapping_registry.json](/home/xue/code/shelf/mapping/mapping_registry.json#L87) 的 `tree` 节点当前只覆盖 `specs/`、`framework/`、`mapping/`。
- [generate_framework_tree_hierarchy.py](/home/xue/code/shelf/scripts/generate_framework_tree_hierarchy.py#L66) 当前也是按这棵标准树和 `framework/` 文档生成树图。

因此现有“树”并没有覆盖：

- `projects/<project_id>/product_spec.toml`
- `projects/<project_id>/implementation_config.toml`
- `src/**` 里的受治理代码符号
- `projects/<project_id>/generated/*`

### 2.2 项目治理现状

知识库项目当前的治理闭环已经接通，但实现方式是“树外 manifest”：

- [governance.py](/home/xue/code/shelf/src/project_runtime/governance.py#L1034) 负责扫描 `@governed_symbol`、生成 `governance_manifest.json`、计算上游闭包 digest、提取实际 evidence、比对期望 evidence。
- [knowledge_base.py](/home/xue/code/shelf/src/project_runtime/knowledge_base.py#L1551) 在物化时生成 `governance_manifest.json`。
- [validate_strict_mapping.py](/home/xue/code/shelf/scripts/validate_strict_mapping.py#L606) 已经把 governance stage 接进严格校验主链。

知识库当前已受治理的高风险行为面包括：

- 运行时页面路由：[app.py](/home/xue/code/shelf/src/knowledge_base_runtime/app.py#L26)
- 前端 surface contract：[contracts.py](/home/xue/code/shelf/src/frontend_kernel/contracts.py#L9)
- 工作台 surface contract：[workbench.py](/home/xue/code/shelf/src/knowledge_base_framework/workbench.py#L9)
- 后端 API contract 与回答行为：[backend.py](/home/xue/code/shelf/src/knowledge_base_runtime/backend.py#L255)
- UI / backend 编译产物构建点：[knowledge_base.py](/home/xue/code/shelf/src/project_runtime/knowledge_base.py#L1163)

### 2.3 当前方案已经能校验什么

在知识库范围内，当前实现已经能做到这些：

- 上游变了但没有重物化，会报 `STALE_EVIDENCE`。
- 当前代码抽取出来的实际 evidence 与上游派生期望 evidence 不一致，会报 `EXPECTATION_MISMATCH`。
- 新增高风险 route 但没有 `@governed_symbol`，会报 `MISSING_BINDING`。
- 伪造/乱写 governed 注释，会报 `UNKNOWN_BINDING`、`UNEXPECTED_BINDING` 或 `INVALID_BINDING_METADATA`。
- manifest 缺失 symbol、重复 symbol、出现未知 symbol，会报 `GOVERNANCE_MANIFEST_INVALID`。

也就是说，**知识库高风险行为面已经能做到“从代码回查上游，或从上游要求代码收敛”。**

### 2.4 当前方案的结构性问题

虽然它能工作，但它还不是最终形态，主要问题有 4 个：

1. 树和治理模型分裂  
   当前 `mapping_registry.tree` 是一棵树，知识库治理又是一套 manifest，结构上不是一个统一模型。

2. Shelf AI 看到的是框架树，不是治理树  
   插件现在打开的是 framework tree，而不是 `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` 的实例治理树。

3. 变更定位还是“symbol compare 中心”，不是“节点传导中心”  
   当前是先扫 symbol，再比 evidence；而理想形态应该是“先找到变更节点，再做树闭包和局部校验”。

4. `projects/*` 仍然在树外  
   这和总纲里的“单向收敛链”在表达层上并不一致，因为 `Product Spec / Implementation Config / Evidence` 还没有正式挂进树。

## 3. 目标方案

### 3.1 总原则

治理主模型改成一棵统一治理树：

```text
Governance Root
└── Project
    ├── Framework
    ├── Product Spec
    ├── Implementation Config
    ├── Code
    └── Evidence
```

这棵树需要满足：

- 每个节点都有稳定 `node_id`
- 每个节点都知道自己属于哪一层
- 每个节点都知道自己的直接父节点
- 每个节点都知道自己对应的文件和定位点
- 高风险节点能声明自己的 extractor / comparator / validator
- 变更检查按“节点闭包”进行，而不是按目录硬编码进行

### 3.2 节点模型

第一版建议节点至少包含这些字段：

```json
{
  "node_id": "kb.code.api.create_chat_turn",
  "kind": "code_symbol",
  "layer": "Code",
  "owner": "framework",
  "risk": "high",
  "file": "src/knowledge_base_runtime/backend.py",
  "locator": "function:create_chat_turn",
  "parent": "kb.code.api",
  "depends_on": [
    "kb.framework.backend.R2",
    "kb.product.route.chat",
    "kb.product.chat",
    "kb.impl.backend"
  ],
  "derived_from": [
    "kb.framework.backend.R2",
    "kb.product.route.chat",
    "kb.product.chat",
    "kb.impl.backend"
  ],
  "validator": "governed_contract",
  "extractor": "python.api_contract.v1",
  "comparator": "exact_contract.v1"
}
```

说明：

- `parent` 负责树结构
- `depends_on / derived_from` 负责底层闭包计算
- `validator / extractor / comparator` 负责节点级校验

对外展示可以仍然只显示树；`depends_on` 是内部执行字段。

### 3.3 节点类型

第一版只需要这几类：

- `framework_rule`
- `product_section`
- `implementation_section`
- `code_symbol`
- `evidence_artifact`
- `project_root`

其中：

- `framework_rule` 对应具体 `R*`
- `product_section` 对应 `product_spec.toml` 某个 section path
- `implementation_section` 对应 `implementation_config.toml` 某个 section path
- `code_symbol` 对应受治理函数 / 类 / contract / route
- `evidence_artifact` 对应 `generated/*`

### 3.4 树结构示例

知识库项目的治理树可以先长成这样：

```text
project.knowledge_base_basic
├── framework
│   ├── frontend.L2.M0
│   │   └── frontend.R1 / R2 / R3 / R4
│   ├── knowledge_base.L2.M0
│   │   └── knowledge_base.R1 / R2 / R3 / R4
│   └── backend.L2.M0
│       └── backend.R1 / R2 / R3 / R4
├── product_spec
│   ├── surface
│   ├── route
│   ├── library
│   ├── preview
│   ├── chat
│   ├── context
│   └── return
├── implementation_config
│   ├── frontend
│   ├── backend
│   ├── evidence
│   └── artifacts
├── code
│   ├── runtime.page_routes
│   ├── frontend.surface_contract
│   ├── workbench.surface_contract
│   ├── ui.surface_spec
│   ├── backend.surface_spec
│   ├── api.library_contracts
│   ├── api.chat_contract
│   └── answer.behavior
└── evidence
    ├── framework_ir.json
    ├── product_spec.json
    ├── implementation_bundle.py
    ├── generation_manifest.json
    └── governance_manifest.json
```

## 4. 节点变更时的检查方式

### 4.1 框架节点变更

当 `framework/*.md` 中某个 `R*` 变更时：

1. 定位对应 `framework_rule` 节点
2. 找到它影响的 `product_section / implementation_section / code_symbol / evidence_artifact`
3. 标记这些下游节点为 `stale`
4. 要求先重新 materialize
5. 再对受影响的 `code_symbol` 和 `evidence_artifact` 做 compare

### 4.2 配置节点变更

当 `product_spec.toml` 或 `implementation_config.toml` 某个 section 变更时：

1. 定位 `product_section` / `implementation_section`
2. 只检查它影响的 `code_symbol` 和 `evidence_artifact`
3. 不需要对整个项目无差别全量 compare

### 4.3 代码节点变更

当 `src/**` 里的受治理函数或 contract 变更时：

1. 先定位 `code_symbol`
2. 找到其 `derived_from` 上游节点
3. 用当前上游节点重新派生期望 evidence
4. 抽取当前代码节点的 actual evidence
5. compare

只有在 compare 通过时，才认为这次代码变更仍然合法。

### 4.4 证据节点变更

当 `generated/*` 被直接改动时：

- 直接判为 `ILLEGAL_EDIT_TARGET`
- 不允许把 evidence 节点当源节点

## 5. 校验入口

最终应该只保留一个权威校验入口，但内部按节点模块化：

```text
validate_strict_mapping.py
└── governance_tree
    ├── tree_loading
    ├── closure_resolution
    ├── framework_checks
    ├── project_checks
    ├── code_symbol_checks
    └── evidence_checks
```

这意味着：

- CLI 仍然只跑一个入口
- Shelf AI 仍然只调用一个入口
- pre-push / CI 也仍然只调用一个入口
- 但内部不再是“按目录类型拼脚本”，而是“按节点类型和闭包做校验”

## 6. Shelf AI 应该怎么用这棵树

插件视角也应升级成治理树，而不是只展示 framework tree。

插件需要支持：

- 打开治理树
- 点击节点跳源文件
- 改动发生后高亮“受影响节点闭包”
- 对被影响节点局部校验
- 在 Problems 面板展示失败节点，而不是只展示失败文件

用户感知应该是：

- 我改了树上的一个节点
- Shelf 立即找出相关节点
- 再按节点关系告诉我：哪里 stale、哪里 mismatch、哪里非法

而不是：

- 我改了一个文件
- Shelf 跑一堆看起来分散的脚本

## 7. 迁移路径

建议分 4 步做，不要一次性推翻现有实现。

### 第 1 步：保留现有知识库 governance，实现树化描述

- 保留 `governance.py`
- 但新增统一 `governance_tree.json`
- 先把知识库项目的 `framework / product / implementation / code / evidence` 都挂到树上

### 第 2 步：把 `governance_manifest.json` 降级为派生证据

- manifest 不再作为主模型
- 它只是 `evidence` 节点之一
- 真正的主模型变成 `governance_tree.json`

### 第 3 步：Shelf AI 从 framework tree 升级到 governance tree

- 继续保留 framework tree 作为结构阅读视图
- 但新增 project governance tree 作为治理工作视图

### 第 4 步：`validate_strict_mapping.py` 切换到节点闭包执行

- 当前 manifest compare 继续保留一段时间
- 等 tree 版本稳定后，再把 manifest compare 降级成内部实现细节

## 8. 本次验证结果

2026-03-10 本地已验证：

- `uv run pytest -q`
- `uv run mypy`
- `uv run python scripts/materialize_project.py`
- `uv run python scripts/validate_strict_mapping.py`
- `uv run python scripts/validate_strict_mapping.py --check-changes`

全部通过。

但这些通过结果证明的是：

- 当前“标准树 + 知识库治理 manifest”方案可工作

它们**并不证明**：

- 仓库已经是“一棵治理树管到底”

这也是本草案要解决的核心问题。

## 9. 拍板建议

当前最合理的工程决策是：

1. 认可现有知识库治理实现作为过渡版
2. 不再继续扩 manifest-first 的思路
3. 正式把目标切到 governance-tree-first
4. 下一步从知识库项目开始，把 `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` 树化

一句话总结：

**当前方案已经能管住知识库高风险行为面，但它还不是“树中心”。下一阶段应把治理主模型从 manifest 升级成统一治理树。**

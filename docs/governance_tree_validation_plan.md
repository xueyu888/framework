# 双向治理当前实现说明

## 1. 当前结论

仓库现在已经不是“只对知识库几个文件打补丁”的状态，而是进入了一个可扩展的双向治理骨架：

- 先自动发现 `projects/<project_id>/` 下的框架驱动项目
- 再按模板注册加载项目
- 再为每个项目构建 object-first 的项目治理闭包
- 再从治理闭包自动推导 strict zone
- 再扫描 strict zone 中的高置信结构候选
- 再把候选全部消解为 `governed / attached / internal`
- 最后把 expected / actual compare、strict zone、workspace tree 一起并入 `materialize` / `validate` / Shelf guard 主链

当前仓库自动发现到的框架驱动项目集合只有一个：

- `knowledge_base_basic`

这是发现结果，不是硬编码前提。

## 2. 主入口与实现位置

### 2.1 项目注册与发现

- 模板注册：`src/project_runtime/template_registry.py`
- 项目自动发现：`src/project_runtime/project_governance.py` 里的 `discover_framework_driven_projects`
- 注册到知识库模板：`src/project_runtime/knowledge_base.py`

### 2.2 object-first 治理

- 通用对象模型、candidate scanner、strict zone 推导：`src/project_runtime/project_governance.py`
- 知识库模板如何把上游语义编译成结构对象：`src/project_runtime/governance.py`

### 2.3 主链接入

- 项目物化主入口：`scripts/materialize_project.py`
- 严格校验主入口：`scripts/validate_strict_mapping.py`
- 工作区治理树：`src/workspace_governance.py`
- VSCode / Shelf AI 后台守卫读取的治理树：`docs/hierarchy/shelf_governance_tree.json`

## 3. 框架驱动项目的发现规则

项目发现不是按模板名白名单做的，而是按以下规则自动识别：

1. 位于 `projects/<project_id>/`
2. 存在 `product_spec.toml`
3. 存在同目录 `implementation_config.toml`
4. `project_spec.toml` 中存在 `project.template`
5. `project.template` 能解析到已注册模板
6. 该模板能通过 `load_project(...)` 成功加载
7. 加载后的项目对象能给出 framework 引用和 generated artifact 契约

发现结果会形成 `FrameworkDrivenProjectRecord`，包含：

- `project_id`
- `template_id`
- `product_spec_file`
- `implementation_config_file`
- `generated_dir`
- `discovery_reasons`
- `framework_refs`
- `artifact_contract`

这批信息会进入项目级治理闭包和工作区治理树。

## 4. object-first 模型

治理中心已经从 `file-first` / `symbol-first` 升成 `object-first`。

当前主对象类型定义在 `src/project_runtime/project_governance.py`：

- `StructuralObject`
- `RequiredRole`
- `StructuralCandidate`
- `ResolvedRoleBinding`
- `StrictZoneEntry`
- `ProjectGovernanceClosure`

每个 `StructuralObject` 至少包含：

- `object_id`
- `project_id`
- `kind`
- `sources_framework`
- `sources_product`
- `sources_implementation`
- `semantic`
- `required_roles`
- `risk_level`
- `cardinality`
- `status`
- `expected_evidence`
- `expected_fingerprint`
- `actual_evidence`
- `actual_fingerprint`
- `comparator`
- `extractor`

### 4.1 当前知识库对象全集

知识库模板当前已经进入治理闭包的对象包括：

- `kb.runtime.page_routes`
- `kb.frontend.surface_contract`
- `kb.workbench.surface_contract`
- `kb.ui.surface_spec`
- `kb.backend.surface_spec`
- `kb.api.library_contracts`
- `kb.api.chat_contract`
- `kb.answer.behavior`
- `knowledge_base_basic.config_effect.*`

最后一类 `config_effect` 不是手工点名文件，而是从 `build_implementation_effect_manifest(...)` 自动提升出来的实现配置对象。

## 5. strict zone 的推导规则

strict zone 不再是固定文件白名单。

当前实现规则是：

1. 先根据项目结构对象的 `required_roles` 生成角色要求
2. 再做全仓 Python 结构候选扫描
3. 再用 `required_roles` 去匹配候选对象
4. 先做一轮 seed role binding
5. 从 seed role binding + evidence artifact contract 推导 strict zone
6. 再只保留 strict zone 内的高置信候选
7. 再做正式 role binding、candidate classification 和 strict zone 收敛

形式上可以理解成：

`strict_zone(project) = 承载该项目结构对象 required_roles 的最小实现闭包 + 必需 evidence carrier`

### 5.1 strict zone 为什么可审计

每个 strict zone 文件都会落成 `StrictZoneEntry`，里面明确记录：

- `file`
- `object_ids`
- `role_ids`
- `candidate_ids`
- `reasons`

所以每个进入 strict zone 的文件都有“因为哪些对象、哪些角色、哪些 evidence reason 进入”的解释。

## 6. Python 第一版 candidate scanner

当前只把 Python 做到第一版闭环，扫描规则在 `src/project_runtime/project_governance.py`。

扫描范围：

- `src/**/*.py`
- `scripts/**/*.py`

当前会扫描的高置信结构候选包括：

### 6.1 route 候选

- FastAPI / APIRouter decorator 的 handler
- router builder / app builder
- `include_router` / `add_api_route` / router construction

### 6.2 schema 候选

- `BaseModel`
- `TypedDict`
- `Enum`
- `dataclass`

### 6.3 builder / compiler / resolver / materializer 候选

- `build_*`
- `_build_*`
- `compile_*`
- `resolve_*`
- `create_*`
- `materialize_*`
- `_expected_*`
- `_actual_*`

并叠加职责信号：

- router construction
- route registration
- artifact write
- governance / manifest / tree / generated 文本信号
- implementation / ui_spec / backend_spec / generated_artifacts effect sink 信号

### 6.4 行为候选

- 函数名命中 `answer / retrieval / citation / merge / context / return`

## 7. governed / attached / internal 消解

scanner 输出的高置信候选不会停留在“扫到了但没人管”的状态。

当前实现里：

- 直接满足某个 `required_role` 的候选：`governed`
- 没直接绑定 role，但和某个 governed object 共享 strict zone carrier file：`attached`
- 仍然留在 strict zone 内、但不承担治理角色的高置信候选：`internal`

这一步由 `classify_candidates(...)` 完成。

当前策略是保守的：

- 先保证没有未解释的高置信候选
- 再逐步细化哪些 attached 应该进一步提升为 governed object

这意味着第一版对“高风险结构不许隐身”已经成立，但“所有 attached 都已经抽象成独立 object”还没有完全做完。

## 8. role closure 规则

`RequiredRole` 不是摆设，现在已经参与真实校验。

每个对象都会声明自己的 `required_roles`，当前知识库对象会自动带上这些角色类型：

- 主要实现承载 role
  - route handler
  - route registration
  - spec builder
  - behavior orchestrator
  - effect sink
- 治理与 evidence role
  - expected builder
  - actual extractor
  - effect evidence

校验时会做：

1. role -> candidate 解析
2. candidate -> role binding
3. role status 是否为 `satisfied`
4. 缺 role 直接报 `ROLE_CLOSURE_MISSING`

## 9. expected / actual compare

主规则已经不是“这轮是否一起改了上游文件”。

现在的主规则是：

- 从上游结构对象闭包推导 `expected_evidence`
- 从实现闭包提取 `actual_evidence`
- 用 `fingerprint + evidence` 做 compare

当前已经进入 compare 的面包括：

- page route contract
- frontend surface contract
- workbench surface contract
- ui surface spec
- backend surface spec
- library API contract
- chat API contract
- answer behavior
- implementation_config effect objects

其中：

- `fingerprint` 负责快速比较
- `evidence` 负责解释 mismatch

## 10. 工作区治理树

工作区不再只是 standards tree。

现在 `src/workspace_governance.py` 会把下面两部分合成一棵工作区树：

- Standards tree
- 每个自动发现的 framework-driven project tree

项目树当前包含这些层：

- `Framework`
- `Product Spec`
- `Implementation Config`
- `Project Structure`
- `Code`
- `Evidence`

其中：

- `Project Structure` 放 structural objects 和 required roles
- `Code` 放 strict zone files 和 structural candidates
- `Evidence` 放 generated artifact nodes

因此 Shelf AI 现在看到的不是“几个路径前缀”，而是“节点闭包 + derived_from”。

## 11. materialize / validate / guard / pre-push / CI 的接入情况

### 11.1 materialize

`scripts/materialize_project.py`

- 先自动发现框架驱动项目
- 再通过模板注册物化每个项目
- 再刷新工作区治理树

### 11.2 validate

`scripts/validate_strict_mapping.py`

继续是唯一权威校验入口，但内部已经接了：

- 项目自动发现
- 模板注册解析
- project governance tree compare
- object-first role closure / strict zone / candidate consistency

### 11.3 guard / pre-push / CI

VSCode guard、git hook、CI 仍然走：

- `scripts/materialize_project.py`
- `scripts/validate_strict_mapping.py`

没有新建另一个竞争性的“真正权威 CLI”。

## 12. 当前已知问题，不隐藏

这套系统已经能跑、能验、能扩，但还没有到终局。当前明确还存在这些边界：

### 12.1 当前只有一个已注册模板真正跑通

虽然主链已经泛化到“通过模板注册处理项目”，但仓库里目前只有 `knowledge_base_workbench` 一个成熟模板实现了完整治理闭包。

### 12.2 Python 优先，其他语言还没有第一版 scanner

object model 和 role model 是语言无关的，但当前 candidate scanner 只实现了 Python。

还没实现：

- JS / TS
- Go
- Rust

### 12.3 attached 仍然偏保守

现在的 attached 判定会优先保证“没有未解释的高置信候选”，所以有一部分共享 strict-zone carrier file 的候选会先归为 attached，而不是立刻升级成独立 object。

这不是错误，但说明对象全集还可以继续扩。

### 12.4 config effect sink 仍是模板内映射

`implementation_effect` 对象已经自动化了，但 effect target -> sink locator 的映射，当前仍由知识库模板内部规则提供。

这不影响主链泛化，但说明“effect sink role discovery”还没完全做到模板无知识。

### 12.5 governance manifest 还保留了兼容 `symbols`

主模型已经是 `structural_objects`，但 manifest 仍保留了 `symbols` 兼容字段，方便旧检查和旧调试脚本过渡。

当前它是兼容层，不再是主真相。

## 13. 如何扩展到 Python 以外语言

当前扩展路线已经清楚：

1. 复用 `StructuralObject / RequiredRole / StructuralCandidate / StrictZoneEntry`
2. 新增语言级 scanner
3. 让 scanner 输出同样的 candidate shape
4. 继续复用 role binding / strict zone / compare 主链

例如未来新增：

- `scan_typescript_structural_candidates(...)`
- `scan_go_structural_candidates(...)`
- `scan_rust_structural_candidates(...)`

它们不需要重写治理系统，只需要产出同一类 candidate 对象。

## 14. 当前验收状态

已经满足的点：

- 自动发现当前仓库里的 framework-driven projects
- 自动生成项目治理闭包
- strict zone 由 object/role/candidate 推导，而不是固定文件白名单
- 至少一个自动发现项目端到端打通
- 已进入主链命令

仍在持续扩展但不阻塞当前闭环的点：

- 多模板覆盖
- 非 Python scanner
- attached -> governed 的更细粒度提升策略

一句话总结：

**当前仓库已经具备“从 Framework 到 Code，再从 Code 反查回 Framework”的 object-first 双向治理骨架，并已在自动发现出的知识库项目上打通端到端闭环；但它仍是 Python-first、单成熟模板先行的第一版，而不是多语言多模板全部完善的终局。**

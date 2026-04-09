# 框架文档Lint标准

## 0. 定位

本文件定义 framework Markdown 的表达协议，以及它与 Config、Code、Evidence 的对齐约束。

## 1. 适用范围

- `specs/*.md`
- `framework/<domain>/Lx-Mn-*.md`
- `framework_drafts/<domain>/Lx-Mn-*.md`
- `projects/*/generated/*` 的派生一致性校验

## 2. Framework Markdown 规则

- 每个正式 framework 文件必须使用 `framework/<domain>/Lx-Mn-*.md` 命名。
- 每个文件必须保留 plain `@framework` 起手入口。
- 每个文件必须包含以下主 section：
  - `## 0. 目标 (Goal)`
  - `## 1. 最小结构基（Minimal Structural Bases）`
  - `## 2. 基排列组合（Base Arrangement / Combination）`
  - `## 3. 边界定义（Boundary）`
  - `## 4. 能力声明（Capability Statement）`
- `## 3. 边界定义（Boundary）` 必须包含以下子 section：
  - `### 3.1 接口定义（IO / Ports）`
  - `### 3.2 参数边界（Parameter Constraints）`
- 当前作者语法统一使用 `边界定义 / 参数边界`。
- 参数项 `boundary_id` 允许使用 `snake_case`、兼容既有全大写/混合大小写 token；下游 section / field 名统一按小写归一化，大小写本身不表达额外语义。
- `C* / N* / B* / R*` 编号必须稳定、唯一、可解析。
- `B*` 的上游模块引用必须写在主句中，不得使用 `上游模块：...`。
- framework 模块正文不得直接写入 `project.toml` 路径、已删除的双轨配置文件名、已删除的旧映射清单名或旧配置 section 语法。

## 3. 项目配置边界

- framework 文档只能描述结构语义，不得直接写入项目实例值。
- 项目配置唯一入口是 `projects/<project_id>/project.toml`。
- 参数跳转或实例落点必须回到 `project.toml` 的显式 section，例如：
  - `[communication.frontend.surface]`
  - `[communication.knowledge_base.chat]`
  - `[exact.frontend.surface]`
  - `[exact.backend.result]`
- `project.toml` 必须可解析，并能被编译器按 contract 切片分发。

## 4. 模块编译与 Contract 对齐

- 每个 framework 文件都必须被编译成唯一 `FrameworkModule` class。
- 每个 `B*` 都必须被编译成独立 `Base` class。
- 每个 `R*` 都必须被编译成独立 `Rule` class。
- `ConfigModule` 必须只消费对应 `FrameworkModule` export。
- `CodeModule` 必须只消费对应 `ConfigModule.exact_export`。
- `EvidenceModule` 必须只消费对应 `CodeModule` export。

## 5. Canonical 与派生视图

- `projects/*/generated/canonical.json` 是唯一机器真相源。
- 层级树、证据树、运行时快照和验证输出都必须明确是 canonical 派生视图。
- 直接编辑 `projects/*/generated/*` 必须被视为违规。

## 6. 自动检查必须覆盖的内容

- framework Markdown 结构完整性
- Framework / Base / Rule class 物化完整性
- 每个 `B*` 至少参与一条 `R*` 组合规则
- 每条 `R*` 至少声明一种结果：输出能力或失效结论
- `## 3` 子章节必须完整包含 `3.1` 与 `3.2`
- `3.1` 仅允许接口条目格式，`3.2` 仅允许参数条目格式
- 禁止伪拆分：同模块内两个 `B*` 若边界集合、规则参与集合、下游影响集合完全一致则判定违规
- `project.toml` 可解析性
- contract 切片与四层 compile 结果一致性
- canonical 可重新物化
- derived views 明确回指 canonical
- `--check-changes` 下的变更传导闭包

## 7. 与执行器关系

`scripts/validate_canonical.py` 是当前主要自动执行器，但脚本不是第一性事实来源；若 lint 合同要变，必须先改本文，再同步执行器。

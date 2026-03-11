# 当前治理树实现方案

## 1. 结论

当前仓库已经落到这条主链：

`Standards -> Project(Framework -> Product Spec -> Implementation Config -> Code -> Evidence) -> Workspace Evidence`

这不是早期那种“标准树 + 项目 manifest”并行的双中心实现了。现在真正的主模型是：

- 工作区统一治理树：`docs/hierarchy/shelf_governance_tree.json`
- 项目治理树：`projects/<project_id>/generated/governance_tree.json`
- 严格校验主入口：`scripts/validate_strict_mapping.py`
- 插件工作视图与自动守卫：`tools/vscode/shelf-ai`

当前已经做到：

- 全局一棵树
- 节点变化驱动相关检查
- 插件直接围绕治理树工作

但也有仍然保留的兼容/工程债，下面会明说，不隐藏。

## 2. 当前结构

### 2.1 工作区治理树

工作区树由 [src/workspace_governance.py](/home/xue/code/shelf/src/workspace_governance.py) 负责生成，产物是：

- [shelf_governance_tree.json](/home/xue/code/shelf/docs/hierarchy/shelf_governance_tree.json)
- [shelf_governance_tree.html](/home/xue/code/shelf/docs/hierarchy/shelf_governance_tree.html)

树顶层现在包含三个正式根分支：

- `Standards`
- `Projects`
- `Workspace Evidence`

其中：

- `Standards` 来自 [mapping_registry.json](/home/xue/code/shelf/mapping/mapping_registry.json)
- `Projects` 下面挂每个项目的 `Framework / Product Spec / Implementation Config / Code / Evidence`
- `Workspace Evidence` 下面挂工作区治理树自己的 JSON / HTML 产物

所以 `docs/hierarchy/shelf_governance_tree.json/html` 不再是树外脚本副产物，而是树上的 evidence 节点。

### 2.2 项目治理树

知识库项目的治理树仍由 [governance.py](/home/xue/code/shelf/src/project_runtime/governance.py) 生成，但现在它是工作区树的子树，不再是树外补丁。

项目树已经覆盖：

- `Framework`
- `Product Spec`
- `Implementation Config`
- `Code`
- `Evidence`

并且 code symbol 节点直接挂在树上，而不是只存在于 manifest 中。

### 2.3 manifest 的当前角色

[governance_manifest.json](/home/xue/code/shelf/projects/knowledge_base_basic/generated/governance_manifest.json) 还保留，但它现在只是辅助证据。

当前真实优先级是：

1. `governance_tree.json`
2. `governance_manifest.json`

也就是说：

- tree 是主结构
- manifest 是辅助展开视图

## 3. 当前校验是怎么做的

### 3.1 从上到下

当 `framework/*.md`、`product_spec.toml`、`implementation_config.toml` 变更时：

1. 工作区治理树根据变更文件定位触发节点
2. 通过 `parent / children / derived_from / reverse_derived` 计算受影响闭包
3. 若命中项目上游节点，插件会自动物化对应项目
4. 严格校验读取项目治理树与工作区治理树
5. 若上游闭包 digest 与当前树证据不一致，报 `STALE_EVIDENCE`

所以现在不再是“这一轮是否顺手改了上游文件”的流程检查，而是：

**当前代码和 evidence 是否仍然符合当前树上游闭包。**

### 3.2 从下到上

当知识库代码变更时：

1. 工作区治理树先定位被触碰的 `code_symbol`
2. 找到其 `derived_from` 上游节点
3. 从当前项目抽取 actual evidence
4. 与树里记录的 expected evidence / fingerprint 比较
5. 不一致时报 `EXPECTATION_MISMATCH`

所以“代码回查上游”现在走的是树闭包，而不是独立 symbol-manifest 比较。

### 3.3 直接非法目标

以下内容现在都被当成派生 evidence，不允许直接手改：

- `projects/*/generated/*`
- `docs/hierarchy/shelf_governance_tree.json`
- `docs/hierarchy/shelf_governance_tree.html`

严格模式下：

- 项目 evidence 会自动重新 materialize
- 工作区治理树 evidence 会自动重新 generate

## 4. 插件现在怎么围绕治理树工作

[extension.js](/home/xue/code/shelf/tools/vscode/shelf-ai/extension.js) 现在的主流程已经切到治理树：

1. 读取 `docs/hierarchy/shelf_governance_tree.json`
2. 用 [governance_tree.js](/home/xue/code/shelf/tools/vscode/shelf-ai/governance_tree.js) 解析 `file_index / parent_index / children_index / derived_index / reverse_derived_index`
3. 把本次保存/创建/删除/重命名命中的文件映射到治理树节点
4. 生成 `touched_nodes / affected_nodes / materialize_project_spec_files`
5. 按节点闭包决定：
   - 是否自动物化
   - 是否跑 `mypy`
   - 是否保护 evidence
6. 再调用唯一权威入口 [validate_strict_mapping.py](/home/xue/code/shelf/scripts/validate_strict_mapping.py)

插件侧边栏也已经不是单纯“打开树图”：

- 打开治理树
- 刷新治理树
- 展示最近一次 `touched / affected` 节点闭包
- 展示严格校验问题
- 展示 hooks / guard mode / tree readiness

也就是说，插件现在的工作视角已经是治理树，不再只是 framework tree。

## 5. 现在真正能保证什么

在知识库项目范围内，当前已经能保证：

- 改 framework / product / implementation，会自动命中相关项目和相关节点闭包
- 改 code，会回查其上游节点并比对 evidence
- 改 generated evidence，会被识别成非法目标
- 工作区治理树自身 evidence 被手改，也会被识别和恢复
- `pre-push` / CLI / 插件 都通过同一个严格校验入口收口

所以现在不是“AI 靠自觉遵守框架”，而是：

**仓库通过治理树知道这次改动碰到了哪个节点、它影响谁、以及当前代码是否仍然与上游派生定义一致。**

## 6. 仍然存在的问题

这些问题当前还存在，但它们已经不是主链路缺口，而是工程债或兼容层。

### 6.1 旧命名兼容仍在

插件内部还保留了旧命令 id 和旧配置 fallback，例如：

- `shelf.openFrameworkTree`
- `shelf.refreshFrameworkTree`
- `frameworkTreeHtmlPath`
- `frameworkTreeGenerateCommand`

这不是因为架构还没切过来，而是为了兼容已有用户配置和命令绑定。

### 6.2 工作区树目前按 `projects/*/product_spec.toml` 自动发现项目

也就是说：

- 工作区树已经是全局树
- 但“全局”的项目发现机制目前仍基于仓库当前目录结构约定

这在当前仓库是合理的，但如果未来项目注册方式变化，需要一起升级发现逻辑。

### 6.3 文件系统触发仍是路径级，闭包执行是节点级

插件监听 VSCode 文件事件时，第一层仍然需要靠 watched paths 触发；
但从“触发后怎么判断影响面”开始，已经是治理树节点闭包。

这意味着：

- 触发入口还是路径
- 决策与校验已经是树

这不是逻辑缺陷，但要明确它的分层。

## 7. 这套实现现在靠什么验证

当前本地已经验证通过：

- `uv run python scripts/materialize_project.py`
- `uv run mypy`
- `uv run pytest -q`
- `uv run python scripts/validate_strict_mapping.py`
- `uv run python scripts/validate_strict_mapping.py --check-changes`
- `node tools/vscode/shelf-ai/test_governance_tree.js`
- `node tools/vscode/shelf-ai/test_guarding.js`
- `node tools/vscode/shelf-ai/test_snippets.js`
- `bash tools/vscode/shelf-ai/install_local.sh`

其中：

- `test_workspace_governance.py` 验证工作区树生成和变更闭包
- `test_governance_manifest.py` 验证项目治理树/治理 evidence 的正确性
- 插件测试验证治理树分类、README/命令/配置契约和守卫行为

## 8. 一句话总结

当前实现已经不是“框架树 + 一些补丁校验”。

它现在的真实形态是：

**一个工作区统一治理树，下面挂标准、项目和 evidence；节点变化驱动局部闭包检查；插件直接围绕这棵树做自动物化、问题反馈和 evidence 保护。**

# 架构说明

## 当前主线

`shelf` 当前的默认主线不是 legacy 置物架求解，而是一个由结构化框架文档驱动的项目编译链：

> `Framework -> Product Spec -> Implementation Config -> Code -> Evidence`

它的目标是把“框架文档作为共同结构语言”这件事真正落到可运行、可追溯、可验证的工程闭环里。

## 主要分层

- `specs/` 与 `framework/*/*.md`
  - 定义共同结构、公理、边界、最小可行基、组合原则和验证规则。
- `projects/<project_id>/product_spec.toml`
  - 定义某个具体产品最终是什么。
- `projects/<project_id>/implementation_config.toml`
  - 定义该产品采用哪条实现路径落地。
- `src/framework_ir/`
  - 负责把框架 Markdown 解析为机器可读中间表示。
- `src/project_runtime/knowledge_base.py`
  - 负责把框架、产品规格和实现配置编译为项目运行时 bundle。
- `src/knowledge_base_runtime/`
  - 承载当前默认样例产品的运行时代码。
- `projects/<project_id>/generated/`
  - 承载物化出的证据层产物，例如 `framework_ir.json`、`product_spec.json`、`implementation_bundle.py`、治理清单与治理树。

## 默认运行链

1. 解析 `framework/*.md` 到 `framework_ir`
2. 校验结构、映射、层级、边界与弱充分性
3. 读取 `product_spec.toml` 与 `implementation_config.toml`
4. 编译生成运行时 bundle 与治理产物
5. 启动 runtime app

默认入口是：

- `uv run python src/main.py`
- `uv run python src/main.py serve`

## 当前默认样例

当前默认样例是 `projects/knowledge_base_basic/`，它展示的是：

- 通用前端框架
- 知识库领域框架
- 后端知识接口框架
- 产品真相与实现配置如何共同编译出一个知识库工作台

## Legacy 样本

历史上的置物架参考样本仍然保留，但已经不再是仓库默认主线。它现在位于：

- `src/examples/legacy_shelf/`
- `docs/legacy_shelf/`

运行命令：

- `uv run python src/main.py legacy-reference-shelf`

这个 legacy 样本的作用是保留方法论来源和早期严格对象域示范，而不是继续承担仓库默认入口职责。

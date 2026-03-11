# Python 实现质量标准

## 0. 定位
本文件定义 Python 代码的最低实现质量门槛，属于 `specs/code/` 代码规范目录的一部分。

`specs/code/` 用于承载各类代码规范，当前先落地 Python，后续可继续扩展其它语言或运行时规范。

## 1. 目标
定义 Python 实现应满足的最低质量要求，确保代码可检查、可维护、可进入推送流程。

本标准同时约束项目编译器、运行时与治理脚本如何解释 `Product Spec` 与 `Implementation Config`，避免项目级行为重新散落回 Python 硬编码。

## 2. 规范要求

- Python 代码必须通过静态类型检查。
- 静态类型检查命令统一为：`uv run mypy`。
- 未通过静态类型检查时，不得进入推送流程。
- Python 实现必须保持 `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` 的单向收敛，不得在代码中偷偷维护第二套项目真相。
- 项目级产品差异必须先进入 `projects/<project_id>/product_spec.toml`；项目级实现差异必须先进入 `projects/<project_id>/implementation_config.toml`，再由 Python 代码解释或编译。
- 解释 `implementation_config.toml` 的 Python 代码必须满足“配置即功能”：
  - 每个实现层字段都必须对应至少一个可观察的下游效果。
  - 下游效果可以是编译后的 `ui_spec` / `backend_spec` / 路由 / 生成产物命名 / 运行时选择路径。
  - 仅把配置原样抄进 bundle、但不进入任何下游选择或产物约束，不算“配置生效”。
- 禁止保留死配置字段。
  - 若某个 `implementation_config.toml` 字段已经不再驱动任何代码路径、编译结果或证据产物，应删除该字段，而不是继续保留占位选择器。
  - 若新增实现层字段，必须同步补齐解释代码、生成产物与自动校验。
- 对项目行为有影响的实现细节，优先暴露为可治理的配置项；Python 代码应尽量退回到解释器、编译器和执行器角色，而不是承载项目私有常量。

## 3. 外部关联

- 工程执行规范：`AGENTS.md`
- 仓库验证命令：`uv run mypy`
- 严格映射验证：`uv run python scripts/validate_strict_mapping.py`
- 框架设计核心标准：`specs/框架设计核心标准.md`
- 框架文档 Lint 标准：`specs/框架文档Lint标准.md`

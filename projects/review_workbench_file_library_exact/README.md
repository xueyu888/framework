# Review Workbench File Library Exact

这个项目用于对齐统一审核平台中文件仓库页的 1:1 产品结构实例。

说明：

- 不修改 `framework/review_workbench/*`，只通过新的 `project.toml` 做 Config 层精确实例化。
- 仍保留 `submission_review` 场景，以满足当前 runtime / validator 对 `review_workbench` 双场景示例的约束。
- `exact.code.frontend` 明确声明前端技术栈目标为 `React + Vite + TailwindCSS + TypeScript(strict)`。
- 当前仓库的 materialize 链路仍生成 canonical / runtime snapshot 等产物，并不会自动脚手架出真实 React 工程。

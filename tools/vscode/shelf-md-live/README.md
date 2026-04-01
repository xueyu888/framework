# Shelf Markdown Live

`Shelf Markdown Live` 是一个独立的 VS Code Markdown 自定义编辑器原型。

目标：

- 在同一个编辑 tab 中显示实时渲染的 Markdown
- 配色尽量跟随 VS Code 原生主题
- 优先服务 framework 风格文档，而不是通用 Markdown 全覆盖

当前原型支持：

- 标题
- 段落
- 列表
- 代码块
- 表格
- LaTeX 渲染（`$...$` / `$$...$$`）
- 原始 Markdown 回写

使用方式：

1. 在本目录执行 `npm install`
2. 在 VS Code 扩展开发模式中打开本插件目录
3. 打开一个 `.md` 文件
4. 通过 `Reopen With...` 选择 `Shelf Markdown Live`

说明：

- 这是原型，不是稳定编辑器
- 当前采用块级编辑：点击块进入编辑，失焦或 `Cmd/Ctrl + Enter` 提交
- `Show Raw` 可打开原始 Markdown 面板

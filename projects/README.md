# 项目实例层

`projects/` 用于承载“框架实例化后”的项目配置。

定位：
- `framework/` 定义抽象结构标准
- `projects/` 固定项目边界值、约束和组合侧重点
- `src/` 承载由框架与项目实例共同驱动的实现代码

约束：
- `projects/` 不属于 L0-L3 框架标准树
- `projects/` 里的文件不能替代标准源文档
- 项目实例只允许具体化框架允许变化的那部分
- 若项目实例反向要求修改框架根约束，必须先改标准，再改项目配置与实现

约定：
- 每个项目放在 `projects/<project_id>/`
- 主配置文件命名为 `project.toml`
- `project.toml` 至少包含：
  - `project`：项目元信息与模板类型
  - `framework_refs`：引用的框架标准
  - `composition_profile`：项目实例选择的组合方式
  - `boundary_values.*`：项目固定下来的边界值
  - `constraint_profile.*`：项目固定下来的约束
  - `scenes` / `seed_articles`：项目级场景与样例数据

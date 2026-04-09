# Shelf

Shelf 是一个面向 AI 编程的结构优先仓库。

仓库现在只保留一条主链：

```text
Framework -> Config -> Code -> Evidence
```

- `framework/*.md` 是唯一 Framework 作者源
- `projects/<project_id>/project.toml` 是唯一 Config 入口
- `Code` 层第一次落地到真实实现
- `Evidence` 层负责验证、快照、追溯和 GUI 材料
- `projects/*/generated/canonical.json` 是唯一机器真相源

## 项目状态

当前仓库未附带默认项目实例。

这意味着仓库目前处于 bootstrap / authoring 状态：

- `framework/*.md` 仍可继续演化作者源
- `uv run python scripts/validate_canonical.py` 与 `uv run python scripts/materialize_project.py` 会以 no-op success 提示当前处于零项目 bootstrap 状态
- `uv run python scripts/validate_canonical.py --check-changes` 仍可用于 bootstrap 门禁
- 在创建新的 `projects/<project_id>/project.toml` 之前，`src/main.py serve` 不会自动获得默认项目

## 快速开始

```bash
uv sync
bash scripts/install_git_hooks.sh
uv run mypy
uv run python scripts/validate_canonical.py --check-changes
```

创建新的 `projects/<project_id>/project.toml` 之后，再执行：

```bash
uv run python scripts/materialize_project.py --project-file projects/<project_id>/project.toml
uv run python scripts/validate_canonical.py --project-file projects/<project_id>/project.toml
uv run python src/main.py serve --project-file projects/<project_id>/project.toml
```

运行后默认入口：

- App: `http://127.0.0.1:8000/`
- Project Config API: `http://127.0.0.1:8000/project/config`
- Correspondence API: `http://127.0.0.1:8000/correspondence`

## 关键文件

- Framework 解析：
  - [src/framework_ir/parser.py](./src/framework_ir/parser.py)
- 四层编译器：
  - [src/project_runtime/compiler.py](./src/project_runtime/compiler.py)
  - [src/project_runtime/framework_layer.py](./src/project_runtime/framework_layer.py)
  - [src/project_runtime/config_layer.py](./src/project_runtime/config_layer.py)
  - [src/project_runtime/code_layer.py](./src/project_runtime/code_layer.py)
  - [src/project_runtime/evidence_layer.py](./src/project_runtime/evidence_layer.py)
- 运行时：
  - [src/project_runtime/runtime_app.py](./src/project_runtime/runtime_app.py)
- 物化与校验：
  - [scripts/materialize_project.py](./scripts/materialize_project.py)
  - [scripts/validate_canonical.py](./scripts/validate_canonical.py)

## 进一步阅读

- [docs/four-layer-architecture.md](./docs/four-layer-architecture.md)

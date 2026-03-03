# 置物架程序运行说明

本说明对应当前 `standards/L2/置物架框架标准.md` 的实现与验证流程。

## 1. 环境准备

在仓库根目录执行：

```bash
uv sync
bash scripts/install_git_hooks.sh
```

说明：
- 必须使用 `uv` 管理依赖与运行命令。
- `pre-push` hook 会在推送前自动做严格映射校验。

## 2. 运行主程序

```bash
uv run python src/main.py
```

作用：
- 运行当前“置物架结构 + 规则映射 + 验证”主流程。
- 在终端输出结构化结果（goal / boundary / structure / verification 等）。

## 3. 严格映射验证

```bash
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

作用：
- 校验 L0/L1/L2 到工程实现的映射一致性。
- `--check-changes` 用于检查变更传导是否完整。

## 4. 生成置物架组合与 3D 交互页面

```bash
uv run python scripts/generate_n2_shelf_dedup_viewer.py --layers 2 --x 30 --y 30 --h 30
```

常用参数：
- `--layers`: 层数 `N`
- `--x`: 单层宽度
- `--y`: 单层深度
- `--h`: 单层高度（同时作为侧板高度上限）
- `--output-dir`: 输出目录（可选）

默认输出目录命名：

```text
docs/diagrams/N{N}_x{X}_y{Y}_h{H}_panelmax{H}
```

关键产物：
- `interactive_3d.html`：交互式 3D 页面
- `summary.json`：组合统计与规则摘要
- `CASE-*.obj`：每种组合的 3D 模型
- `CASE-*.png`、`ALL_COMBOS_3D.png`：预览图

## 5. 打开与使用交互页面

在浏览器中打开：

```text
docs/diagrams/N{N}_x{X}_y{Y}_h{H}_panelmax{H}/interactive_3d.html
```

页面可做的事：
- 浏览去旋转重复后的所有合法组合。
- 调整方块数量、位置、层数、尺寸、重量。
- 调整外部承载属性（rod/panel/connector/board/boardDeflect）。
- 受力颜色从白到红表示利用率从低到高。
- 超限时在右侧故障框显示原因和当前承重，并用细线/编号指向具体超限基。

## 6. 建议执行顺序

```bash
uv sync
uv run python src/main.py
uv run python scripts/generate_n2_shelf_dedup_viewer.py --layers 2 --x 30 --y 30 --h 30
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

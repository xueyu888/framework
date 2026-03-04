# Frontend Spec Project

前端规范框架初始化项目（仅保留前端领域知识）。

## 目录
- `standards/L0`：规范总纲与树形结构
- `standards/L1`：方法标准（核心/可追溯/可删减）
- `standards/L2`：前端领域标准
- `standards/L3`：映射注册
- `src/`：最小可运行实现
- `scripts/`：严格映射校验脚本
- `docs/logic_record.json`：验证证据产物

## 快速开始
```bash
uv sync
uv run python src/main.py
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

## 说明
- 本项目采用 `Goal -> Boundary -> Module -> Combination Principles -> Verification` 五段式框架。
- L2 仅包含前端领域标准：总览层、页面层、业务组件层、基础组件层。

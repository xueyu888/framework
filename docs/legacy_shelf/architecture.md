# Legacy Shelf 参考架构

> 该目录承载历史置物架参考样本，不代表当前仓库默认主线。

## 项目结构
- `src/domain/`: 核心实体与数据模型
- `src/rules/`: 组合规则与结构规则判定
- `src/geometry/`: 网格与几何诱导构造
- `src/enumeration/`: 有界离散分型穷举与 canonical 去重
- `src/metrics/`: 空间利用度与简化载荷
- `src/verification/`: 统一验证报告
- `src/visualization/`: 3D 渲染（Plotly + OBJ fallback）
- `src/examples/legacy_shelf/reference_pipeline.py`: legacy 置物架流水线入口，输出样本证据与说明文档

## 数据流
自然语言规则 -> 形式化对象 -> 枚举候选 -> 规则判定 -> 计算空间利用度 -> baseline 比较 -> 输出证据

## 规则流
- R1/R2：模块种类组合过滤（FRAME/SHELF 通用）
- R3：对所有结构适用
- R4/R5/R6：仅对 SHELF 适用；FRAME 视为 not applicable/pass
- FRAME 特有规则：connected、ground_contact、minimal_under_deletability、可选 forbid_dangling_rods
- Verification：边界有效 + 组合有效 + 空间利用度提升

## 可追溯性
核心类名与规则函数保持与 L2 -> L3 映射一致，输出 `docs/legacy_shelf/logic_record.json` 保存步骤级证据链，输出 `docs/legacy_shelf/run_summary.json` 保存运行摘要。

# 窗帘框架模块标准（L0）xx
<!--@layer module=curtain; level=L0-->

## 1. 目标（Goal）

- 小标题：一句话描述该层要解决的问题。

请补充本层目标正文。

## 2. 边界定义（Boundary）

- 小标题：定义该层负责什么、不负责什么。
- `TODO_SCOPE`：待补充边界定义。

## 3. 最小可行基（Bases）

- 小标题：列出最小能力基并补全 `@base` 元数据。
- `B1` 待定义能力基1  <!--@base id=B1; name=BASE_1; capability=todo_capability_1-->
- `B2` 待定义能力基2  <!--@base id=B2; name=BASE_2; capability=todo_capability_2-->
- `B3` 待定义能力基3  <!--@base id=B3; name=BASE_3; capability=todo_capability_3-->
- `B4` 待定义能力基4  <!--@base id=B4; name=BASE_4; capability=todo_capability_4-->

## 4. 组合原则（Combination Principles）

- 小标题：描述组合方向、约束和映射示例。
仅允许下游向上游组合：`L0 -> L1`。禁止同层组合与反向组合。

组合约束集合：
- `C1` 相邻层约束
- `C2` 下游上行约束
- `C3` 能力契约约束

组合映射（示例）：
- `U1 = {L0.B1, L0.B2} --[C1,C2,C3]--> L1.B1`

- 待补充组合关系。  <!--@compose from=L0.Mcurtain.B1; to=L1.Mcurtain.B1; rule=adjacent_only; principle=P_DOWNSTREAM_UPSTREAM; constraint=C1_C2_C3-->
- 待补充组合关系。  <!--@compose from=L0.Mcurtain.B2; to=L1.Mcurtain.B2; rule=adjacent_only; principle=P_DOWNSTREAM_UPSTREAM; constraint=C1_C2_C3-->
- 待补充组合关系。  <!--@compose from=L0.Mcurtain.B3; to=L1.Mcurtain.B3; rule=adjacent_only; principle=P_DOWNSTREAM_UPSTREAM; constraint=C1_C2_C3-->
- 待补充组合关系。  <!--@compose from=L0.Mcurtain.B4; to=L1.Mcurtain.B1; rule=adjacent_only; principle=P_DOWNSTREAM_UPSTREAM; constraint=C1_C2_C3-->

## 5. 验证（Verification）

- 小标题：定义可执行验证条件。
- 每个 `L0` 基必须至少指向一个 `L1` 父节点。
- 每个 `L1` 基必须至少由一个 `L0` 子节点支撑。
- 不允许同层或跨层跳级组合。

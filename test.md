## 2. 边界定义（Boundary）
- `N`：层数（trace=BoundaryDefinition.layers_n; type=int）
- `P`：每层承重（trace=BoundaryDefinition.payload_p_per_layer; type=number）
- `S`：每层空间（trace=BoundaryDefinition.space_s_per_layer; type=Space3D）
- `O`：开口尺寸（trace=BoundaryDefinition.opening_o; type=Opening2D）
- `A`：占地面积（trace=BoundaryDefinition.footprint_a; type=Footprint2D）

## 3. 模块（最小可行基，Base）
- `M1` 杆（name=ROD; capability=结构骨架与承力通道）
- `M2` 连接接口（name=CONNECTOR; capability=对接关系_传力规则_装配语义）
- `M3` 隔板（name=PANEL; capability=承载面_载荷分配到连接点）

## 4. 组合原则（Combination Principles）
- `R1`：组合不得孤立，至少包含 2 个模块（kind=subset_precheck; expr=len(combo)>=2; reason=combo_too_small）
- `R2`：每个可用组合必须包含连接接口模块（kind=subset_precheck; expr=CONNECTOR in combo; reason=connector_missing）
- `R3`：正交原则（kind=structural; trace=StructuralPrinciples.rods_orthogonal_layout; reason=rod_not_orthogonal）
- `R4`：板方向原则（kind=structural; trace=StructuralPrinciples.boards_parallel_with_rod_constraints; reason=board_orientation_invalid）
- `R5`：四角贴合原则（kind=structural; trace=StructuralPrinciples.exact_fit; params=epsilon:number; reason=exact_fit_failed）
- `R6`：上视投影增益原则（kind=goal_related; trace=check_r6_projected_panel_gain; reason=projected_gain_not_positive）

## 5. 验证（Verification）
通过条件：
- boundary_valid
- combo_in_valid_set
- expr: target_efficiency > baseline_efficiency
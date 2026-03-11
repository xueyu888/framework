# 给其它 AI 的 Shelf 仓库全景说明

## 1. 这份文档是给谁看的

这份文档不是给第一次打开仓库的人做快速上手，也不是给最终用户看的产品说明。

它是写给另一个 AI 的。目标是让另一个 AI 在尽量少翻文件的前提下，快速建立对 `shelf` 的整体模型，然后基于这个模型提出真正有用的建议，而不是把仓库误解成一个普通的前端项目、一个单纯的知识库 demo，或者一个“用 Markdown 写模板”的系统。

如果你是另一个 AI，可以把这份文档理解成：

- 当前仓库思想的压缩说明
- 当前工程方法的压缩说明
- 当前已落地能力与边界的压缩说明
- 当前仍未解决问题的明确清单

---

## 2. 一句话定义这个仓库

`shelf` 当前最准确的定义不是“置物架项目”，也不是“知识库项目”。

它更准确的定义是：

> 一个以“结构”为第一性对象、以框架文档为源语言、以项目物化和治理验证为目标的编译型仓库。

它要打通的是下面这条单向链路：

> `Framework -> Product Spec -> Implementation Config -> Code -> Evidence`

其中：

- `Framework` 负责定义共同结构语言
- `Product Spec` 负责定义某个具体产品最终是什么
- `Implementation Config` 负责定义该产品采用哪条实现路径落地
- `Code` 负责实现
- `Evidence` 负责保存可验证、可追溯、可反查的证据

这个仓库真正想证明的是：

> 框架文档能否成为人和 AI 的共同结构语言，并进一步约束产品真相、实现细化、运行时代码和验证证据。

---

## 3. 这个仓库为什么存在

这个仓库背后的判断是：

人和 AI 在协作写软件时，最容易失控的不是“代码能不能写出来”，而是：

- 双方讨论的层次混在一起
- 产品真相和实现细节互相污染
- 框架文档只是说明书，代码才是真相
- 改完代码以后，很难反查它还是否符合原先的结构约束

因此，`shelf` 的目标不是做一个更花哨的代码生成器，而是建立一套更稳定的协作结构。

它的核心假设是：

1. 结构比功能更基础  
   功能是结构的外显结果，结构才是第一性对象。

2. 框架不是项目模板  
   框架不是为了某一个项目写死的骨架，而是跨实例稳定复用的共同结构语言。

3. 分层必须单向收敛  
   `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` 只能单向流动，不能反向污染。

4. 配置不应只是备注  
   尤其是 `implementation_config.toml`，它不是给人留印象用的，它应该真的进入下游行为。当前仓库把这件事概括为：  
   `配置即功能`

5. 验证不能只靠人眼  
   至少关键结构必须能被自动反查、自动比对、自动拒绝漂移。

---

## 4. 这个仓库的第一性哲学

### 4.1 结构是第一性对象

仓库最核心的哲学不在某个工程技巧里，而在 [框架设计核心标准.md](../specs/框架设计核心标准.md) 的基本立场里：

- 结构不是功能
- 结构不是实现
- 结构不是实例
- 结构是对象之所以能够稳定成立的组织关系

因此，这个仓库写框架时，不从“我要什么功能列表”起步，而从以下五件事起步：

1. 能力声明
2. 边界定义
3. 最小可行基
4. 组合原则
5. 验证

这五件事一起定义“什么结构成立”。

### 4.2 目标只是入口，不是第一性事实

仓库允许在框架文档开头写目标，但目标只是探索入口，不是结构正确性的第一性依据。

如果更深入的结构推导表明：

- 有更稳定的组织方式
- 有更一般的可复用结构
- 有更少自由度但更强生成性的表达

那么应该修正原目标，而不是强迫结构服从最初执念。

### 4.3 逐结构覆盖，而不是逐行覆盖

这个仓库不追求“每一行代码都有框架对应项”。那样会把框架变成代码索引，最后不可维护。

它追求的是：

> 每个高风险、稳定、可命名、会影响系统边界或行为的结构对象，都应该能回挂到上游结构链路。

换句话说，目标不是逐语法对象治理，而是逐结构对象治理。

---

## 5. 仓库的方法论骨架

### 5.1 Framework 层

`Framework` 层负责定义共同结构语言。

它由两部分组成：

- `specs/`
  - 规定总纲、核心标准、Lint 合同、代码规范
- `framework/<domain>/Lx-Mn-*.md`
  - 规定某个领域的分层模块标准

框架文档不是自由文本，而是有协议的 Markdown。

每个 `framework/*.md` 都要求存在：

- `## 1. 能力声明`
- `## 2. 边界定义`
- `## 3. 最小可行基`
- `## 4. 基组合原则`
- `## 5. 验证`

并要求文档里的结构项使用稳定编号：

- `C*`：能力项
- `B*`：最小可行基
- `R*`：组合规则
- `V*`：验证项

### 5.2 Product Spec 层

`projects/<project_id>/product_spec.toml` 负责定义：

> 某个具体产品最终是什么。

它是产品真相层。

它应该包含：

- 页面与承载结构
- 路由真相
- 视觉语义
- 交互语义
- 业务对象
- 返回回路
- 内容种子

它不应该包含：

- 技术栈选择
- 类名函数名
- CSS 细节
- DOM 细节
- 后端 transport 选择
- 仅属于某种实现路径的技巧

### 5.3 Implementation Config 层

`projects/<project_id>/implementation_config.toml` 负责定义：

> 同一个产品真相，本次采用哪条实现路径落地。

它是实现细化层。

它应该回答：

- 前端 renderer / style / script 走哪条实现 profile
- 后端 renderer / transport / retrieval 走哪条实现 profile
- 证据对外暴露在哪里
- 生成产物如何命名

它不应该反向改写产品真相。

当前仓库正在强化一个原则：

> `implementation_config.toml` 里的字段，不能只是存在于文件里或抄进 bundle 里，而必须真的进入下游编译结果或运行时行为。

这就是“配置即功能”。

### 5.4 Code 层

`src/` 里承载的是编译器、运行时模板、治理器和验证器。

它不是项目层人工业务真相的第一入口。

对知识库主链来说，代码主要承担三种职责：

- 解析框架 Markdown 到 IR
- 把 `Framework + Product Spec + Implementation Config` 编译成项目结构
- 消费编译结果生成 runtime 和 evidence

### 5.5 Evidence 层

`projects/<project_id>/generated/` 承载的是证据，不是人工编辑源。

当前知识库主链的 canonical 生成物包括：

- `framework_ir.json`
- `product_spec.json`
- `implementation_bundle.py`
- `generation_manifest.json`
- `governance_manifest.json`
- `governance_tree.json`

这些产物的地位不是“缓存”，而是：

- 编译结果证据
- 治理关系证据
- 反查校验证据

---

## 6. 这个仓库当前怎么跑

### 6.1 默认主线

默认主线已经不是 legacy 置物架，而是知识库工作台样例：

- 项目：`projects/knowledge_base_basic/`
- 运行命令：`uv run python src/main.py`

当前默认主链是：

1. 解析 `framework/*.md` 到 `framework_ir`
2. 校验结构、层级、映射、弱充分性
3. 加载 `product_spec.toml` 与 `implementation_config.toml`
4. 编译为项目级 `KnowledgeBaseProject`
5. 物化 generated artifacts
6. 用 runtime 代码消费编译结果并启动 FastAPI app

### 6.2 关键代码位置

如果另一个 AI 要快速抓主链，优先看这些文件：

- `src/framework_ir/parser.py`
  - 负责把框架 Markdown 解析为机器可读 IR
- `src/project_runtime/knowledge_base.py`
  - 负责知识库主模板的编译与物化
- `src/project_runtime/governance.py`
  - 负责定义高风险 governed symbols、expected evidence 与 actual extractors
- `src/knowledge_base_runtime/app.py`
  - 负责把编译结果装配成 FastAPI 路由
- `src/knowledge_base_runtime/backend.py`
  - 负责后端接口与回答行为
- `src/knowledge_base_runtime/frontend.py`
  - 负责前端页面拼装
- `scripts/materialize_project.py`
  - 物化项目产物
- `scripts/validate_strict_mapping.py`
  - 执行主要结构校验、治理校验、配置生效校验

### 6.3 关键校验命令

当前标准工作流里的核心命令是：

```bash
uv run python src/main.py
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

---

## 7. 用一个具体例子理解“从框架到代码”

用 `/api/knowledge/product-spec` 这条路由可以把主链看清楚。

### 7.1 上游结构来源

这条路由不是直接写死在运行时代码里的。

它同时受到三层约束：

1. `Framework`
   - 规定页面/API/证据暴露这类结构必须存在
2. `Product Spec`
   - 在 `route.api_prefix` 中固定产品 API 前缀
3. `Implementation Config`
   - 在 `evidence.product_spec_endpoint` 中细化产品真相接口对外暴露路径

### 7.2 编译阶段

`src/project_runtime/knowledge_base.py` 会：

- 校验 `evidence.product_spec_endpoint` 必须落在 `route.api_prefix` 之下
- 再把它编译进 `backend_spec.transport.product_spec_endpoint`

### 7.3 运行时代码

`src/knowledge_base_runtime/app.py` 最终不是写：

```python
@app.get("/api/knowledge/product-spec")
```

而是消费编译结果：

```python
transport = _require_backend_transport(resolved)

@app.get(transport["product_spec_endpoint"])
def product_spec() -> dict[str, object]:
    return resolved.to_product_spec_dict()
```

因此，这条链是：

`framework rule -> product route -> implementation evidence -> compiled backend_spec.transport -> runtime route`

这也是当前仓库希望推广的模式：

> runtime 不重新发明产品真相，而是消费编译后的结构。

更完整的展开见 [框架到代码映射与反查覆盖说明.md](./框架到代码映射与反查覆盖说明.md)。

---

## 8. 这个仓库如何反过来检查“代码有没有脱框架”

这个仓库目前不是只做正向生成，它也在做反向治理。

当前反查主要有四层。

### 8.1 generated artifacts 重物化对比

`validate_project_generation_discipline()` 会重新物化一套 generated artifacts，然后与项目当前 `generated/` 下的产物逐个做字节级比较。

因此：

- 不能手改 `generated/*`
- 不能让 evidence 脱离上游 truth 单独漂移

### 8.2 governed symbol 的 expected/actual 对比

`src/project_runtime/governance.py` 定义了一组高风险 governed symbols，例如：

- `kb.runtime.page_routes`
- `kb.frontend.surface_contract`
- `kb.workbench.surface_contract`
- `kb.ui.surface_spec`
- `kb.backend.surface_spec`
- `kb.api.library_contracts`
- `kb.api.chat_contract`
- `kb.answer.behavior`

每个 symbol 都有：

- 上游依赖闭包
- expected evidence builder
- actual extractor
- 允许绑定的代码位置

校验时会比较 expected 和 actual。  
如果代码改了，但上游结构和治理证据没跟上，就会失败。

### 8.3 配置即功能校验

当前仓库已经把“配置即功能”落实成自动检查。

`validate_implementation_config_effects()` 会读取 `implementation_config.toml` 的叶子字段，检查：

- 它是否声明了下游效果
- 这些效果路径是否真的存在
- 这些效果值是否真的反映当前配置值

例如：

- `frontend.style_profile` 必须进入 `ui_spec.implementation.style_profile`
- `backend.retrieval_strategy` 必须进入 `backend_spec.retrieval.strategy`
- `evidence.product_spec_endpoint` 必须进入 `backend_spec.transport.product_spec_endpoint`

### 8.4 高风险未治理结构扫描

当前治理器会特别扫描知识库主链中高风险的页面/API builder。

如果在这些位置新增了新的路由或高风险入口，但没有纳入治理绑定，治理快照构建会失败。

---

## 9. 当前仓库已经做到什么，还没做到什么

### 9.1 已经做到的

1. 主线已清晰  
   仓库当前默认主线明确是“框架文档编译成知识库工作台示例”。

2. 分层已清晰  
   `Framework -> Product Spec -> Implementation Config -> Code -> Evidence` 已是仓库明确的主模型。

3. 关键生成链已跑通  
   框架、产品和实现配置可以物化出 runtime 和 evidence。

4. 关键反查链已跑通  
   对高风险结构对象，已经能做 expected/actual 的自动比对。

5. 配置即功能已部分落地  
   `implementation_config.toml` 的关键叶子字段已进入自动校验。

### 9.2 还没做到的

1. 还没有“仓库全部代码完全被框架覆盖”

当前做到的是：

- 关键结构强覆盖
- canonical generated artifacts 强一致性覆盖
- 关键实现配置字段的生效性覆盖

还没做到的是：

- 所有低风险 helper 都有上游结构映射
- 所有内部算法细节都有完整框架反查
- 所有样本代码都进入同等强度治理

2. 还没有“结构对象全集治理”

当前治理更像“已识别高风险对象治理”，还不是“结构对象全集扫描 + 全覆盖闭合校验”。

3. `implementation_config.toml` 还不够强

虽然现在已经有“配置即功能”校验，但它仍然偏薄。  
很多真正的实现细节，仍然主要藏在 Python 里，而不是清晰暴露在实现配置层。

4. 生成物设计还有简化空间

例如 `implementation_bundle.py` 目前仍然偏大，承担了过多“给人看”和“给机器看”的混合职责。

5. 当前只有单模板主链成熟

`knowledge_base_workbench` 是当前成熟主链。其它模板体系还没有进入同等成熟度。

---

## 10. 仓库里还有一条 legacy 线，不能误解

仓库名叫 `shelf`，最早来源于置物架对象域。

现在仍保留一条 legacy 样本线：

- `src/examples/legacy_shelf/`
- `docs/legacy_shelf/`

它的价值不是当前默认入口，而是：

- 作为方法论来源
- 作为早期严格对象域样本
- 作为“结构 -> 枚举 -> 验证 -> 证据”的参考实现

因此，另一个 AI 不应该把 legacy 线误判为当前默认主产品，但也不应该忽略它，因为很多核心思想就是从这条线长出来的。

---

## 11. 另一个 AI 最容易误解的点

### 11.1 误解一：这是一个普通的知识库项目

不是。  
知识库只是当前默认样例和主编译链承载体。

### 11.2 误解二：这是一个用 Markdown 写模板的系统

也不是。  
框架 Markdown 在这里不是模板，而是结构源语言。

### 11.3 误解三：`product_spec.toml` 和 `implementation_config.toml` 都是配置文件，所以差不多

不对。  
这两层语义不同：

- `product_spec.toml` 是产品真相
- `implementation_config.toml` 是实现细化

### 11.4 误解四：generated 产物只是缓存

不对。  
generated 产物是证据层，不只是缓存。

### 11.5 误解五：治理就是 lint

不对。  
lint 只是表达和闭合检查的一部分。  
治理更强调：

- 结构对象绑定
- expected/actual 证据比对
- 高风险结构反查

### 11.6 误解六：目标是让所有代码逐行都能映射到框架

也不对。  
当前目标是逐结构覆盖，不是逐语法元素覆盖。

---

## 12. 当前最值得其它 AI 帮忙思考的问题

如果你是另一个 AI，最有价值的建议不是“换个 UI 框架”或者“代码再重构一下”，而是以下问题：

### 12.1 如何定义“结构对象全集”

当前仓库已经有 governed symbols，但还没有真正完整的“结构对象全集”机制。

最重要的问题是：

> 如何系统性地定义、扫描、分类并校验一个项目中的全部结构对象，而不是只治理一小组高风险对象？

### 12.2 如何把“逐结构覆盖”真正做成机器可判定

理想状态是同时满足：

- 每个上游结构都有下游落点
- 每个下游结构对象都有上游来源
- 允许豁免的对象被明确标记为 `non_structural`
- 从属对象被明确标记为 `derived_structure`

也就是把“覆盖”从口头判断，推进成双向闭合校验。

### 12.3 如何让 `implementation_config.toml` 更强，但不退化成伪代码

这是当前最实际的问题之一。

方向是对的：

- 更多实现差异应该进入实现配置层

但风险也明显：

- 如果无节制扩张，它会变成另一个代码文件

因此需要找到：

> 哪些实现维度是真正稳定、值得配置化的，哪些则应继续留在代码解释器里。

### 12.4 如何减少 generated 中间产物的重复和 token 成本

当前生成物已经比早期收敛了，但仍存在：

- 一些信息在多个产物中重复展开
- 部分产物兼具“给人看”和“给机器看”两种职责

其它 AI 可以重点审视：

- 哪些产物是真必要证据
- 哪些产物可以合并或降级为派生视图
- 哪些产物命名和分层还不够准

### 12.5 如何提升从代码反查框架的强度

当前已经能对关键结构做反查，但还做不到全量结构覆盖。

值得思考的问题是：

- 如何用 AST 或运行时提取更完整的结构候选对象
- 如何定义 expected/actual contract 的扩展面
- 如何把更多高风险 helper 提升成治理对象

### 12.6 如何判断当前方案是否已经是“最简实现”

这个仓库并不排斥重构。  
如果存在更少层、更少重复源、更少中间产物、但仍能保留同样能力的方案，应该大胆提出。

但判断标准不应只是“文件更少”，而应是：

- 是否仍保持单向真相流
- 是否仍保持结构先于实现
- 是否仍支持产品真相与实现细化分层
- 是否仍支持反向治理和证据校验

---

## 13. 如果另一个 AI 要给建议，最好按什么维度输出

建议按以下维度组织反馈：

1. 这个仓库当前定义是否准确  
   也就是：它到底是不是“结构语言编译器 + 项目物化器 + 治理验证器”。

2. 当前分层是否合理  
   尤其是 `Framework / Product Spec / Implementation Config / Code / Evidence` 的边界是否清楚。

3. 当前主链最脆弱的点在哪里  
   例如：
   - 结构对象全集缺失
   - implementation config 偏薄
   - generated 产物重复
   - 治理覆盖面不足

4. 是否存在更简洁但等价的实现方案  
   如果有，应该明确指出哪些层可以折叠、哪些产物可以降级、哪些真相源可以合并。

5. 如果继续推进，优先级应该是什么  
   建议不要只提“理想终局”，而要给出有顺序的推进路径。

---

## 14. 最后一句话

如果要把这个仓库压缩成一句最硬的定义，那就是：

> `shelf` 试图把“结构先于功能、框架先于实现、真相单向收敛、关键结构可反查”这四件事，落实成一个真的能跑、能编译、能验证、能治理的工程系统。

如果另一个 AI 要给建议，最有价值的不是把它当成一个普通项目来优化，而是判断：

> 这套“结构语言 -> 产品真相 -> 实现细化 -> 代码 -> 证据”的方法，是否还能更稳、更简、更可验证。

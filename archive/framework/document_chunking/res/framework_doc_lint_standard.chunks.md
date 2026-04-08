# framework_doc_lint_standard Chunk View

- source: `/home/wuyz/Ability_Enhance/frame/shelf/specs/框架文档Lint标准.md`
- paragraph blocks: `18`
- text chunks: `10`

<!-- chunk:tc-0001 start -->
## tc-0001

- title_block_id: `pb-0001`
- body_block_count: `0`
- order_range: `1..1`

# 框架文档Lint标准
<!-- chunk:tc-0001 end -->

---

<!-- chunk:tc-0002 start -->
## tc-0002

- title_block_id: `pb-0002`
- body_block_count: `1`
- order_range: `2..3`

## 0. 定位
本文件定义框架标准文档的表达协议与 lint 合同，不定义框架设计的语义核心。

关系边界：
- `specs/框架设计核心标准.md` 负责定义“什么结构成立、什么组合合法、哪些边界允许变化”。
- 本文件负责定义这些结构在 Markdown、树注册与治理校验中必须如何表达、如何编号、如何被 lint。
- `scripts/validate_strict_mapping.py` 是本文件的主要自动执行器，但脚本不是第一性事实来源；规则本体以本文件为准。
<!-- chunk:tc-0002 end -->

---

<!-- chunk:tc-0003 start -->
## tc-0003

- title_block_id: `pb-0004`
- body_block_count: `1`
- order_range: `4..5`

## 1. 适用范围

- `specs/` 下承载 L0/L1 标准的 Markdown 文件。
- `framework/<module>/Lx-Mn-*.md` 下承载领域模块标准的 Markdown 文件。
- `mapping/mapping_registry.json` 承载的标准树、映射注册与变更传导元数据。
- `projects/<project_id>/generated/` 的生成产物一致性校验。
<!-- chunk:tc-0003 end -->

---

<!-- chunk:tc-0004 start -->
## tc-0004

- title_block_id: `pb-0006`
- body_block_count: `0`
- order_range: `6..6`

## 2. 文档表达规则
<!-- chunk:tc-0004 end -->

---

<!-- chunk:tc-0005 start -->
## tc-0005

- title_block_id: `pb-0007`
- body_block_count: `1`
- order_range: `7..8`

### 2.1 路径、层级与文件命名

- `L0/L1` 标准文件必须位于 `specs/`。
- `L2` 标准文件必须位于 `framework/<module>/Lx-Mn-*.md`。
- `L3` 注册文件必须位于 `mapping/`。
- 模块是文件级单元：一个 `framework/<domain>/Lx-Mn-*.md` 文件对应一个模块。
- 当同层存在多个模块文件时，文件名必须使用 `Lx-Mn-*.md` 表示模块编号（例如 `L1-M0-...md`）。
- 模块别名（若需要）是文件级信息，不得绑定到单个 `B*`。
<!-- chunk:tc-0005 end -->

---

<!-- chunk:tc-0006 start -->
## tc-0006

- title_block_id: `pb-0009`
- body_block_count: `1`
- order_range: `9..10`

### 2.2 框架 Markdown 必备结构

- 面向 `framework/*.md` 的标准模块文档必须保留 plain `@framework` 指令对应的标准模板起手入口。
- `@framework` 入口属于框架作者起手约束，不得删除；若未来替换实现方式，必须提供同等直接、默认可用且可回归测试的替代入口。
- 框架模块文档应按顺序提供以下主 section：
  - `## 1. 能力声明`
  - `## 2. 边界定义`
  - `## 3. 最小可行基`
  - `## 4. 基组合原则`
  - `## 5. 验证`
<!-- chunk:tc-0006 end -->

---

<!-- chunk:tc-0007 start -->
## tc-0007

- title_block_id: `pb-0011`
- body_block_count: `1`
- order_range: `11..12`

### 2.3 编号与表达格式

- `C*`、`B*`、`R*`、`V*` 必须使用稳定、连续且可解析的编号。
- 每个基必须具备 `B{n}` 标识，并可规范化映射为 `L{X}.M{m}.B{n}`。
- `B*` 行格式应为 `B* 名称：<结构定义或 Lx.My[...] 或 framework.Lx.My[...]>。来源：\`...\``。
- 若引用本框架更低层模块或外部更基础通用框架，模块引用必须直接内联写在 `B*` 主句中。
- 禁止使用 `上游模块：...` 这类追加字段表达模块依赖。
- 外部框架引用可写为 `frontend.L1.M0[R1,R2]` 这类显式形式；本地框架引用可写为 `L1.M0[R1,R2]`。
<!-- chunk:tc-0007 end -->

---

<!-- chunk:tc-0008 start -->
## tc-0008

- title_block_id: `pb-0013`
- body_block_count: `1`
- order_range: `13..14`

## 3. 自动 Lint 与治理校验

- 路径与层级 lint：校验 `L0/L1/L2/L3` 文件路径是否落在合法目录。
- 文档结构 lint：校验 `@framework` 文档是否具备必备主 section、标题与可解析条目。
- 编号与语法 lint：校验 `C/B/R/V` 编号、`B*` 表达格式、inline ref 语法以及禁用的遗留写法。
- 引用图 lint：校验模块依赖方向、无环性、显式引用可解释性与根层自足性。
- 树注册 lint：校验 `mapping/mapping_registry.json` 的标准树节点、唯一挂载关系与 L0-L3 落点。
- 变更传导 lint：校验 `L0 -> L1 -> L2 -> L3` 的变更传播是否闭合。
- 生成产物 lint：校验项目生成产物是否可由框架、`product_spec.toml` 与 `implementation_config.toml` 重新物化并保持一致。
<!-- chunk:tc-0008 end -->

---

<!-- chunk:tc-0009 start -->
## tc-0009

- title_block_id: `pb-0015`
- body_block_count: `1`
- order_range: `15..16`

## 4. 非自动审查边界

- lint 不替代 `specs/框架设计核心标准.md` 的语义判断。
- “这个基是否真的是结构”“这个边界是否真正服务能力成立”“这个组合是否导出声明能力”仍以核心标准为准。
- 当表达格式合法但语义不成立时，应先按核心标准修正文档结构定义，而不是放宽 lint。
<!-- chunk:tc-0009 end -->

---

<!-- chunk:tc-0010 start -->
## tc-0010

- title_block_id: `pb-0017`
- body_block_count: `1`
- order_range: `17..18`

## 5. 外部关联

- `specs/规范总纲与树形结构.md`
- `specs/框架设计核心标准.md`
- `mapping/mapping_registry.json`
- `scripts/validate_strict_mapping.py`
<!-- chunk:tc-0010 end -->

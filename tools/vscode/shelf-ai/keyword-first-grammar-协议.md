# `.sf` 实验语言规范（Shelf Framework Preview）

## 0. 文档定位

本文档用于把 Shelf AI 当前 `.sf` 语言预览的作者规则写清楚，供人阅读、评审和对照实现。

它只覆盖当前插件里的实验性 `.sf` / `shelf-framework` 语言预览，不覆盖正式 `framework/*.md` 作者源。

职责边界如下：

- 本文档负责把当前 `.sf` 的写法、限制、编辑器行为与 lint 规则说明清楚。
- 编辑器里的直接机器规则仍以共享 grammar 实现为准：
  - `tools/vscode/shelf-ai/sf_grammar.js`
  - `tools/vscode/shelf-ai/sf_completion.js`
  - `tools/vscode/shelf-ai/sf_lint.js`
  - `tools/vscode/shelf-ai/extension.js`
- `.sf` 仅用于编辑器预览，不进入 canonical / materialize / publish 主链，不替代正式 `framework/*.md` 作者源。

如果本文档与上述实现不一致，应优先修正文档或实现，不能长期容忍“双份规则各写一套”。

## 1. 适用范围

当前 `.sf` 语言的正式适用范围是：

- 独立的 `.sf` 文件
- VS Code language id：`shelf-framework`
- 插件提供的语义高亮、实时 lint、上下文补全

当前 `.sf` 语言的明确非目标是：

- 作为 `framework/*.md` 的替代输入
- 参与 canonical 生成
- 参与 materialize / validate / publish 正式链路
- 在编辑器外声明仓库机器真相

## 2. 总体文件形状

一个 `.sf` 文件当前按“单文件单模块”处理，标准形状如下：

```sf
MODULE 中文模块名:EnglishName:
    Goal := "模块目标"

    Base:
        set 名称 := "..."
        elem 名称 := "..."
        struct 名称 := "..."
        seq 名称 := "..."
        op[2:1] 名称 := "..."

    Principles:
         名称 := "..."
        eq 名称 := "..."

    Spaces:
        set 名称 := "..."
        comb 名称 := "..."
        seq 名称 := "..."

    Boundary:
        in<subtype> 名称 := "..."
        out<subtype> 名称 := "..."
        param<enum> 名称 := "..."
        param<range> 名称 := "..."
```

当前强制的顶层顺序固定为：

1. `MODULE`
2. `Goal`
3. `Base`
4. `Principles`
5. `Spaces`
6. `Boundary`

其中 `Goal / Base / Principles / Spaces / Boundary` 都是必需块，不允许缺省或调序。

## 3. 强制结构规则

### 3.1 模块头

模块头必须写成：

```sf
MODULE 中文模块名:EnglishName:
```

当前实现要求：

- 关键字必须是全大写 `MODULE`
- 中文模块名部分不能包含 `:`
- 英文名必须匹配标识符形式：首字符为字母或 `_`，后续允许字母、数字、`_`
- 行尾必须保留最后一个 `:`

不允许写成：

- `module 中文模块名:EnglishName:`
- `MODULE 中文模块名:English-Name:`
- `MODULE 中文模块名:123Name:`

### 3.2 顶层块

模块体内固定存在以下顶层块：

- `Goal := "..."`
- `Base:`
- `Principles:`
- `Spaces:`
- `Boundary:`

当前 lint 会同时检查：

- 是否缺少顶层块
- 顶层块是否按固定顺序出现

### 3.3 缩进

当前 `.sf` 使用固定的 4 空格层级：

```text
0 空格   MODULE ...
4 空格   Goal / Base / Principles / Spaces / Boundary
8 空格   block 内声明
```

当前强制规则：

- 禁止使用 tab
- 声明层必须是 8 空格缩进
- 顶层块应使用 4 空格缩进

## 4. 各块允许的语句

### 4.1 Goal

`Goal` 必须是单行声明：

```sf
Goal := "模块目标"
```

当前实现把 `Goal` 视为模块级单例，不支持多行 clause 语法，也不支持 `goal xxx := ...` 这类额外 kind。

### 4.2 Base

`Base:` 下当前只允许以下五类语句：

```sf
set 名称 := 内容
elem 名称 := 内容
struct 名称 := 内容
seq 名称 := 内容
op[shape] 名称 := 内容
```

说明：

- `set` 用于集合基
- `elem` 用于结构基
- `struct` 用于具名复合结构基
- `seq` 用于有序集合基或顺序结构基
- `op[shape]` 用于操作子基
- `op` 当前实现允许省略 `[shape]`，但标准示例建议显式写出，如 `op[2:1]`
- `Base` 至少需要一个声明

当前不再接受旧原型里的：

- `rel`
- `attr`

### 4.3 Principles

`Principles:` 下当前只允许：

```sf
sat 名称 := 内容
eq 名称 := 内容
```

说明：

- `sat` 表示成立/满足类原则
- `eq` 表示判同/归并类原则
- `Principles` 至少需要一个声明

当前不再接受旧原型里的：

- `form`
- `id`
- `norm`

### 4.4 Spaces

`Spaces:` 下当前只允许：

```sf
set 名称 := 内容
comb 名称 := 内容
seq 名称 := 内容
```

说明：

- `set` 表示结果集合或候选集合
- `comb` 表示组合分类或组合结果
- `seq` 表示序列、候选行或枚举条目
- `Spaces` 至少需要一个声明

### 4.5 Boundary

`Boundary:` 下当前只允许：

```sf
in<subtype> 名称 := 内容
out<subtype> 名称 := 内容
param<enum> 名称 := 内容
param<range> 名称 := 内容
```

说明：

- `in` 与 `out` 当前必须显式带 subtype
- `Boundary` 只负责输入/输出/参数，不再把操作签名单独写成 `op[...]`
- `subtype` 当前按开放语义标签处理；`string`、`record`、`enum`、`view` 等命名都可以，只要作者语义自洽
- `param` 当前只有 `enum` 与 `range` 两种正式写法
- `Boundary` 至少需要一个边界声明

标准示例如下：

```sf
in<subtype> 输入边界 := "..."
out<subtype> 输出边界 := "..."
in<enum> 输入状态 := Base.状态集合
out<enum> 输出状态 := Base.状态集合
param<enum> 状态集合 := "{pending, success, failed}"
param<range> 最大层数 := "[0:2]"
```

补充约定：

- `Boundary` 右值可以直接写字面内容
- 也可以直接绑定到已定义的 `Base.xxx` 符号

例如：

```sf
in<enum> 是否完成过 := Base.是否完成过
out<enum> 是否第一次完成 := Base.是否第一次完成
```

## 5. 右侧内容与引用规则

### 5.1 右侧内容

当前 `.sf` 的 `:=` 右侧内容仍按“作者文本”处理，插件只要求它是非空内容。

也就是说，当前 lint 不继续解析右侧为更细 AST。

声明头本身仍然必须出现在首行，但右侧内容现在允许两种写法：

- 单行写完
- 在首行给出声明头与右值起始片段，后续以更深缩进继续续写

下面这些写法在当前实现里都属于可接受的右侧内容：

```sf
set 变量集合 := "记作 V"
sat 条件同一 := "若在全部赋值下结果一致，则归入同一结果类"
seq 深度零行 := "{深度零, {0, 1, x, y, z}, 通过}"
in<enum> 输入状态 := Base.状态集合
param<range> 最大层数 := "[0:2]"
```

例如，下面这种多行续写现在也是允许的：

```sf
seq 情况总表 := <  <recorded, finished, yes>,
                <recorded, unfinished, no>,
                <unrecorded, finished, no>>
```

因此，当前 `.sf` 采用的是“单行声明头 + 自由右值文本（可续行）”的预览模型，而不是旧版 clause 结构模型。

### 5.2 引用语法

当前实现识别的引用路径是：

- `Base.名称`
- `Principles.名称`
- `Spaces.名称`
- `Boundary.名称`

例如：

```sf
sat 允许提交 := "只有当 Base.父任务记录 与 Boundary.状态输入 同时存在时才成立"
comb 合法组合 := "按 Principles.允许提交 把 Spaces.候选行 归入同一类"
```

重要说明：

- 当前引用路径不带 statement kind
- 当前引用路径也不带 subtype

因此：

- `Principles.条件同一` 是当前合法引用形式
- `Principles.eq.条件同一` 不是当前引用形式
- `Boundary.变量边界` 是当前合法引用形式
- `Boundary.param<enum>.变量边界` 不是当前引用形式

### 5.3 括号与集合约定

当前 `.sf` 对右值文本采用以下约定：

- `{...}` 表示集合内容，或枚举值域内容
- `<...>` 表示有序集合，或有顺序约束的条目序列
- `t(i)` 表示时间位点；常见约定里，`t(0)` 表示进入当前判断前的历史位点，`t(1)` 表示本次输入或触发所在位点

例如：

```sf
set 状态集合 := {finished, unfinished}
param<enum> 状态边界 := {finished, unfinished}
seq 情况总表 := < <recorded, finished, yes>, <recorded, unfinished, no> >
sat 首次完成触发 := "仅当 t(0)=unfinished 且 t(1)=finish 时，判定为 yes"
```

这两个符号约定当前主要用于作者表达与团队约定；lint 不会进一步校验花括号或尖括号内部的细粒度结构，但规范层面应按此语义理解。

### 5.4 引用校验范围

当前 lint 只校验：

- 引用是否指向当前文件内已定义的符号

当前 lint 不做：

- 跨文件引用解析
- canonical 级别对象追踪
- statement body 的深层语义验证

### 5.5 名称建议

虽然当前声明名在解析上可以写较宽松的自然语言，但引用解析按连续 token 工作。为保证引用、补全与高亮稳定，建议声明名遵守以下约束：

- 尽量不包含空格
- 尽量不包含括号、引号、尖括号、花括号等标点
- 优先使用中文连续词或稳定英文标识符
- 若要表达时间位点，建议把 `t(0)`、`t(1)` 等时间符号写在 `:=` 右侧内容中，而不是直接写进可引用的声明名；当前引用 token 不建议包含括号

## 6. 强制规则与推荐排版的边界

为了让作者知道“哪些会直接报错，哪些只是推荐写法”，当前约定分为两层：

### 6.1 当前 lint 强制的规则

当前插件会直接报错的规则只有这些：

- 首行必须是 `MODULE 中文模块名:EnglishName:`
- 禁止 tab
- 顶层 `Goal / Base / Principles / Spaces / Boundary` 必须全部存在且顺序固定
- `Goal` 必须是 `Goal := "..."` 单行
- `Base` 里只能写 `set / elem / struct / seq / op[...]`
- `Principles` 里只能写 `sat / eq`
- `Spaces` 里只能写 `set / comb / seq`
- `Boundary` 里只能写 `in<...> / out<...> / param<enum|range>`
- 声明缩进必须使用固定 4 空格层级
- 引用必须命中当前文件内已定义符号

### 6.2 当前推荐但尚未 lint 强制的排版

以下属于当前推荐写法，但不是 lint 的额外独立强制项：

- 相邻顶层块之间保留一个空行
- `op` 显式写出 `[shape]`
- `in` / `out` 使用稳定的 subtype 名称，如 `string`、`record`、`enum`、`view`
- `:=` 右侧优先使用清晰的引号文本或结构化字面量
- 若右值续行，续行应缩进到声明头之下，不要回退到 8 空格声明层
- `{}` 优先用于集合/枚举值域，`<>` 优先用于有序条目序列

## 7. 编辑器行为

当前 `.sf` 的语义高亮、补全与 lint 共用同一套 grammar 入口。

### 7.1 语义高亮

当前会做语义高亮的内容包括：

- `MODULE`
- `Goal`
- `Base:` / `Principles:` / `Spaces:` / `Boundary:`
- `set / elem / struct / seq / op / sat / eq / comb / in / out / param`
- `elem 点`、`set 点集`、`param<enum> 状态边界` 这类声明名
- `[2:1]` 这类 shape 片段
- `<enum>`、`<range>`、`<view>` 这类 subtype 片段
- `Base.xxx` / `Principles.xxx` / `Spaces.xxx` / `Boundary.xxx` 形式的引用

### 7.2 上下文补全

当前补全按位置工作：

- 空文件或模块头位置：
  - 给完整 `.sf` 模板
  - 给 `MODULE`
  - 给 `Goal` 与各个 block
- 进入某个 block 且位于声明层：
  - `Base` 下给 `set / elem / struct / seq / op[...]`
  - `Principles` 下给 `sat / eq`
  - `Spaces` 下给 `set / comb / seq`
  - `Boundary` 下给 `in<...> / out<...> / param<enum> / param<range>`

### 7.3 触发字符

当前 `.sf` 自动触发补全的字符集合为：

```text
M G B P S e r s q c i o p < [ : . 空格
```

## 8. 当前 lint 诊断码

当前 `.sf` 使用以下诊断码：

- `SFL001`：文件必须以 `MODULE 中文模块名:EnglishName:` 起始
- `SFL002`：禁止使用 tab
- `SFL003`：顶层块缺失或顺序不合法
- `SFL004`：`Goal` 不是合法单行格式
- `SFL005`：`Base` block 语句格式不合法
- `SFL006`：`Principles` block 语句格式不合法
- `SFL007`：`Spaces` block 语句格式不合法
- `SFL008`：`Boundary` block 语句格式不合法
- `SFL009`：缩进层级不是固定 4 空格步长
- `SFL010`：引用了当前文件内未定义符号

## 9. 禁止继续沿用的旧原型写法

为避免旧文档和新实现混杂，下面这些写法不应再作为当前 `.sf` 规范传播：

- 小写 `module`
- `rel / attr`
- `form / id / norm`
- `Boundary.in.名称` 之外再带 kind 或 subtype 的旧引用路径
- `on(...) / body(...) / from(...) / by(...) / payload(...) / card(...) / affects(...)` 这类 clause-first 多行值语法，作为当前 `.sf` 的正式结构要求

这些写法可能出现在历史讨论或旧草稿里，但不代表当前插件实现。

## 10. 标准示例

下面给出一份与当前实现一致的标准示例：

```sf
MODULE 布尔逻辑模块:BooleanLogicModule:
    Goal := "定义由 0、1、And、Or、Not 生成的布尔表达式系统；在给定边界下，把全部合法组合按层数与可导出的定律进行分类。"

    Base:
        set 变量集合 := "记作 V；元素写作 x、y、z 等。"
        set 常元集合 := "元素写作 0、1。"
        struct 表达式树 := "记作 Tree；表示由常元、变量与连接子递归生成的复合结构。"
        seq 变量顺序 := "记作 <x, y, z>；表示变量的一个有序排列。"
        op[2:1] And := "记作 And(e, f)；二元连接子。"

    Principles:
        sat And成立 := "对任意 e、f 与赋值 α，And(e, f) 成立当且仅当两者同时成立。"
        eq 条件同一 := "若对全部赋值结果一致，则归入同一结果类。"

    Spaces:
        set 候选结果集合 := "{深度零组合, 深度一组合}"
        comb 组合分类总表 := "列名固定为 {组合类型, 组合方式, 对应原则, 是否通过, 归类结果}。"
        seq 深度零行 := "{深度零, {0, 1, x, y, z}, 通过}"

    Boundary:
        in<enum> 输入变量 := Base.变量集合
        out<enum> 输出取值 := Boundary.变量取值边界
        param<enum> 变量边界 := "{x, y, z}"
        param<enum> 变量取值边界 := "{0, 1}"
        param<range> 最大嵌套层数 := "[0:2]"
```

完整可运行示例见：

- `tools/vscode/shelf-ai/examples/合取模块.sf`
- `tools/vscode/shelf-ai/examples/父子任务状态记录模块.sf`

## 11. 实现对应

为了让作者知道“规则写在哪”，当前 `.sf` 语言相关实现分布如下：

- 语法定义、语义高亮 token、补全触发字符：
  - `tools/vscode/shelf-ai/sf_grammar.js`
- 补全条目与上下文判定：
  - `tools/vscode/shelf-ai/sf_completion.js`
- 实时 lint 规则：
  - `tools/vscode/shelf-ai/sf_lint.js`
- VS Code provider 注册、diagnostics 文案、language 接线：
  - `tools/vscode/shelf-ai/extension.js`
- `.sf` 语言注册与括号/自动闭合配置：
  - `tools/vscode/shelf-ai/package.json`
  - `tools/vscode/shelf-ai/languages/shelf-framework.json`
- 回归测试：
  - `tools/vscode/shelf-ai/test_sf_language.js`

后续若 `.sf` 语法继续演进，应优先同时更新：

1. `sf_grammar.js`
2. `sf_completion.js`
3. `sf_lint.js`
4. 本文档

不能只改其中一处，导致别人读到的规范与编辑器实际行为再次分叉。

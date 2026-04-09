# Keyword-First Framework Language Reference

## 1. Overview

本文件只定义这门 framework 作者语言的表面语法。

目标是把下面三层区分清楚：

- `Goal`、`Base`、`Principles`、`Spaces`、`Boundary` 是模块级 block，首字母大写。
- `elem`、`rel`、`attr`、`form`、`sat`、`id`、`norm`、`comb`、`seq`、`in`、`out`、`param` 是 block 内声明 kind，保持小写。
- `schema`、`range`、`enum` 是声明的子类型，只挂在声明 kind 后面，例如 `in<schema>`、`param<range>`，不挂在 block 名上。

因此：

- `Principles<Form>` 不是目标语法。
- `Boundary<Type>` 不是目标语法。
- `form ...`、`sat ...` 应直接写在 `Principles:` 下面。
- `in<schema> ...`、`out<schema> ...`、`param<range> ...` 应直接写在 `Boundary:` 下面。

## 2. Canonical Shape

```
module 中文模块名:EnglishModuleName:
    Goal := "..."

    Base:
        elem 名称 := ...
        rel 名称 := ...
        attr 名称 := ...

    Principles:
        form 名称 := ...
        sat 名称 := ...
        id 名称 := ...
        norm 名称 := ...

    Spaces:
        comb 名称 := ...
        seq 名称 := ...

    Boundary:
        in<schema> 名称 := ...
        out<schema> 名称 := ...
        param<range> 名称 := ...
        param<enum> 名称 := ...
```

这门语言的核心约束是：

- block 名负责命名空间；
- kind 负责声明类别；
- subtype 负责值形状；
- 引用路径只看 `block.kind.name`，不把 subtype 算进命名空间。

例如：

- `Principles.form.失败传播`
- `Spaces.comb.父任务失败闭包`
- `Boundary.in.子任务记录输入`
- `Boundary.param.传播窗口`

这里的 `schema`、`range`、`enum` 只说明声明的值类型，不进入引用路径。

## 3. Blocks

### 3.1 Module

模块头声明整个文件的唯一模块名。

```
module 中文模块名:EnglishModuleName:
```

其中：

- 前半段是中文作者名；
- 后半段是英文稳定符号名；
- 末尾的 `:` 打开一个缩进块。

### 3.2 Goal

`Goal` 是模块级单例声明，不再使用额外的 `goal` kind。

```
Goal := "记录父任务及其子任务的状态，并在子任务状态变化后同步更新父任务状态"
```

一个模块当前只允许一个 `Goal`。

### 3.3 Base

`Base` 用来声明最小结构基。

```
Base:
    elem 名称 := ...
    rel 名称 := ...
    attr 名称 := ...
```

当前最小必要 kind：

- `elem`：结构中的独立单元
- `rel`：结构单元之间的关系
- `attr`：挂在某个结构单元上的结构位置或结构属性

`Base` 里不放 `enum`、`range`、`schema`。这些不是结构基，而是边界值类型。

### 3.4 Principles

`Principles` 用来声明组合原则。这里不再引入统一的 `rule` 壳层，而是直接用原则类型本身作为 kind。

```
Principles:
    form 名称 := ...
    sat 名称 := ...
    id 名称 := ...
    norm 名称 := ...
```

各 kind 的职责：

- `form`：说明一个组合如何成立
- `sat`：说明一个已形成组合需要满足什么约束
- `id`：说明“什么算同一个”
- `norm`：说明组合结果如何归一化或稳定化

### 3.5 Spaces

`Spaces` 用来声明结果组合空间。

```
Spaces:
    comb 名称 := ...
    seq 名称 := ...
```

各 kind 的职责：

- `comb`：无序组合结果
- `seq`：有序组合结果

### 3.6 Boundary

`Boundary` 用来声明输入、输出、参数边界。

```
Boundary:
    in<schema> 名称 := ...
    out<schema> 名称 := ...
    param<range> 名称 := ...
    param<enum> 名称 := ...
```

这里的主 kind 只有三种：

- `in`
- `out`
- `param`

子类型挂在 kind 后面：

- `schema`：结构化载荷
- `range`：区间值域
- `enum`：枚举值域

因此：

- `enum` 不是 `Base`
- `enum` 也不是新的 block
- `enum` 是 `Boundary` 声明的 subtype

## 4. Statement Forms

### 4.1 Base Statements

```
elem 名称 := 值
rel 名称 := 值
attr 名称 := 值
```

右侧的 `值` 可以是：

- 一个文档链接
- 一个已有符号引用
- 一段简短自然语言说明

### 4.2 Principle Statements

```
form 名称 := on(<引用列表>), body("说明")
sat 名称 := on(<引用列表>), body("说明")
id 名称 := on(<引用列表>), body("说明")
norm 名称 := on(<引用列表>), body("说明")
```

说明：

- `on(...)` 说明该原则作用在哪些结构或空间上；
- `body("...")` 说明该原则的自然语言内容；
- `form/sat/id/norm` 本身就是声明类型，所以不再额外写 `rule`。

### 4.3 Space Statements

```
comb 名称 := from(<引用列表>), by(<原则引用列表>)
seq 名称 := from(<引用列表>), by(<原则引用列表>)
```

说明：

- `from(...)` 说明该空间由哪些结构基出发；
- `by(...)` 说明该空间受哪些原则约束；
- `comb` 与 `seq` 直接表示结果空间的形态。

### 4.4 Boundary Statements

输入边界：

```
in<schema> 名称 := payload(值), card(基数), to(目标引用)
```

输出边界：

```
out<schema> 名称 := payload(值), card(基数), from(来源引用)
```

参数边界：

```
param<range> 名称 := domain(值域), affects(<引用列表>)
param<enum> 名称 := domain(值域), affects(<引用列表>)
param<schema> 名称 := domain(值域), affects(<引用列表>)
```

说明：

- `in` 必须写 `payload`、`card`、`to`
- `out` 必须写 `payload`、`card`、`from`
- `param` 必须写 `domain`、`affects`

也就是说，`Boundary` 的统一性来自“声明头形式统一”，而不是“所有字段完全相同”。

## 5. References

引用路径统一使用点路径：

```
Base.名称
Principles.form.名称
Principles.sat.名称
Principles.id.名称
Principles.norm.名称
Spaces.comb.名称
Spaces.seq.名称
Boundary.in.名称
Boundary.out.名称
Boundary.param.名称
```

注意：

- `Boundary.in.状态输入` 是合法引用；
- `Boundary.in<schema>.状态输入` 不是引用路径；
- subtype 只在声明处出现，不在引用处出现。

## 6. Full Grammar

本节定义逻辑语法，不直接规定物理换行。

也就是说：

- `form/sat/id/norm`
- `comb/seq`
- `in/out/param`

这些声明在语义上仍是单个 statement；
是否换成多行，由第 7 节的 canonical formatting 决定。

```
module_file        := module_decl NL INDENT module_body DEDENT
module_decl        := "module" WS module_name ":"
module_name        := natural_name ":" english_identifier

module_body        := goal_stmt NL NL
                      base_block NL NL
                      principles_block NL NL
                      spaces_block NL NL
                      boundary_block

goal_stmt          := "Goal" WS ":=" WS string_literal

base_block         := "Base:" NL INDENT base_stmt+ DEDENT
base_stmt          := base_kind WS natural_name WS ":=" WS base_value NL
base_kind          := "elem" | "rel" | "attr"

principles_block   := "Principles:" NL INDENT principle_stmt+ DEDENT
principle_stmt     := principle_kind WS natural_name WS ":=" WS principle_value NL
principle_kind     := "form" | "sat" | "id" | "norm"
principle_value    := "on(" ref_list ")" "," WS "body(" string_literal ")"

spaces_block       := "Spaces:" NL INDENT space_stmt+ DEDENT
space_stmt         := space_kind WS natural_name WS ":=" WS space_value NL
space_kind         := "comb" | "seq"
space_value        := "from(" ref_list ")" "," WS "by(" ref_list ")"

boundary_block     := "Boundary:" NL INDENT boundary_stmt+ DEDENT
boundary_stmt      := in_stmt | out_stmt | param_stmt

in_stmt            := "in" subtype_opt WS natural_name WS ":=" WS in_value NL
out_stmt           := "out" subtype_opt WS natural_name WS ":=" WS out_value NL
param_stmt         := "param" subtype_opt WS natural_name WS ":=" WS param_value NL

subtype_opt        := "" | "<" boundary_subtype ">"
boundary_subtype   := "schema" | "range" | "enum"

in_value           := "payload(" expr ")" "," WS "card(" cardinality ")" "," WS "to(" ref ")"
out_value          := "payload(" expr ")" "," WS "card(" cardinality ")" "," WS "from(" ref ")"
param_value        := "domain(" expr ")" "," WS "affects(" ref_list ")"

ref_list           := "<" ref ("," WS ref)* ">"
ref                := base_ref | principle_ref | space_ref | boundary_ref
base_ref           := "Base." natural_name
principle_ref      := "Principles." principle_kind "." natural_name
space_ref          := "Spaces." space_kind "." natural_name
boundary_ref       := "Boundary." boundary_kind "." natural_name
boundary_kind      := "in" | "out" | "param"

base_value         := link_literal | ref | natural_text
expr               := ref | literal | natural_text
literal            := string_literal | collection_literal | scalar_literal
cardinality        := integer | integer ".." integer_or_star
integer_or_star    := integer | "*"
```

## 7. Canonical Formatting

### 7.1 Indentation

缩进规则固定如下：

- 缩进单位固定为 `4` 个空格。
- 禁止使用 tab。
- `module` 体内缩进一级。
- `Base`、`Principles`、`Spaces`、`Boundary` 内的声明再缩进一级。
- 多行声明的续行，相对于声明头再多缩进一级。

因此标准层级是：

```
0 空格   module ...
4 空格   Goal / Base / Principles / Spaces / Boundary
8 空格   elem / form / comb / in<schema> / ...
12 空格  on(...) / body(...) / payload(...) / ...
```

### 7.2 Line Breaking

换行规则固定如下：

- `Goal` 必须单行书写。
- `Base` 中的 `elem / rel / attr` 必须单行书写。
- `Principles` 中的 `form / sat / id / norm` 必须在 `:=` 后换行。
- `Spaces` 中的 `comb / seq` 必须在 `:=` 后换行。
- `Boundary` 中的 `in / out / param` 必须在 `:=` 后换行。

标准形式如下：

```
form 名称 :=
    on(<...>),
    body("...")

comb 名称 :=
    from(<...>),
    by(<...>)

in<schema> 名称 :=
    payload(...),
    card(...),
    to(...)
```

### 7.3 Clause Layout

多行声明内部的 clause 布局固定如下：

- 每一行只允许一个 clause。
- 非最后一个 clause 末尾必须带 `,`。
- 最后一个 clause 末尾不得带 `,`。
- clause 名与左括号之间不留空格，例如 `on(...)`、`payload(...)`。
- `:=` 后面不得继续写同一行内容，必须直接换行。

### 7.4 Blank Lines

空行规则固定如下：

- `Goal` 与 `Base` 之间保留一个空行。
- 相邻 block 之间保留一个空行。
- `Base`、`Principles`、`Spaces` 内部声明之间不插入空行。
- `Boundary` 内部相邻声明之间保留一个空行。

这里把 `Boundary` 单独拉开，是因为它直接构成模块对外表面，视觉上需要更强分隔。

### 7.5 Formatter Contract

formatter 和 lint 必须共同遵守下面这组规则：

- 语法是否成立，按第 6 节判定。
- 物理排版是否规范，按第 7 节判定。
- 对于 `principle_value / space_value / in_value / out_value / param_value`，换行只影响排版，不改变 AST。

## 8. Canonical Example

```
module 父子任务状态记录模块:TaskStateRecorder:
    Goal := "记录父任务及其子任务的状态，并在子任务状态变化后同步更新父任务状态"

    Base:
        elem 父任务提交处理逻辑 := [父任务提交处理逻辑](../../docs/back_zrx/父任务提交处理逻辑.md)
        elem 子任务提交处理逻辑 := [子任务提交处理逻辑](../../docs/back_zrx/子任务提交处理逻辑.md)
        attr 父任务状态记录表 := [父任务状态记录表](../../docs/back_zrx/父任务状态记录表.md)
        attr 子任务状态记录表 := [子任务状态记录表](../../docs/back_zrx/子任务状态记录表.md)

    Principles:
        form 子任务提交 :=
            on(<Base.子任务提交处理逻辑, Base.子任务状态记录表, Base.父任务状态记录表>),
            body("接收子任务记录并同步更新父任务状态")
        sat 子任务提交 :=
            on(<Spaces.comb.子任务提交>),
            body("父任务记录必须先存在，子任务提交后父任务状态必须同步更新")

    Spaces:
        comb 子任务提交 :=
            from(<Base.子任务提交处理逻辑, Base.子任务状态记录表, Base.父任务状态记录表>),
            by(<Principles.form.子任务提交, Principles.sat.子任务提交>)

    Boundary:
        in<schema> 子任务记录输入 :=
            payload({子任务id, 父任务id, 子任务状态, 是否初次完成, 子任务附加信息}),
            card(1),
            to(Spaces.comb.子任务提交)

        out<schema> 父任务记录输出 :=
            payload({父任务id, 子任务总数, 已完成子任务数, 父任务状态, 父任务附加信息}),
            card(0..1),
            from(Spaces.comb.子任务提交)

        param<enum> 子任务状态集合 :=
            domain({pending, running, success, failed}),
            affects(<Boundary.in.子任务记录输入, Spaces.comb.子任务提交>)
```

## 9. Design Notes

这版语法刻意固定了三件事：

- `Principles` 下直接写 `form/sat/id/norm`，不用 `rule` 再包一层；
- `Boundary` 下直接写 `in/out/param`，subtype 挂在 kind 后面；
- `enum/range/schema` 不再和 `Base` 混在一起，而是作为边界值类型出现。

这样后面的 parser、lint、completion、highlight 才能稳定围绕同一棵 AST 工作。

const sfGrammar = require("./sf_grammar");

function createIssue({ file, line, column, code, message, level = "error" }) {
  return {
    file,
    line: Number(line || 1),
    column: Number(column || 1),
    code,
    message,
    level,
  };
}

function markerColumn(rawLine) {
  const index = String(rawLine || "").search(/\S/u);
  return index >= 0 ? index + 1 : 1;
}

function collectRefs(text) {
  return [...String(text || "").matchAll(sfGrammar.SF_REFERENCE_PATTERN)].map((match) => String(match[0] || ""));
}

function collectTopLevelEntries(lines) {
  const entries = [];
  for (let index = 0; index < lines.length; index += 1) {
    const raw = String(lines[index] || "");
    const trimmed = sfGrammar.trimLine(raw);
    const indent = sfGrammar.getIndent(raw);
    if (!trimmed) {
      continue;
    }
    if (index === 0 && sfGrammar.SF_MODULE_DECL_PATTERN.test(trimmed)) {
      entries.push({ id: "module", line: index + 1, raw, trimmed });
      continue;
    }
    if (indent !== 4) {
      continue;
    }
    if (sfGrammar.SF_GOAL_PATTERN.test(trimmed)) {
      entries.push({ id: "goal", line: index + 1, raw, trimmed });
      continue;
    }
    const sectionId = sfGrammar.detectShelfFrameworkSectionId(trimmed);
    if (sectionId) {
      entries.push({ id: sectionId, line: index + 1, raw, trimmed });
    }
  }
  return entries;
}

function findEntry(entries, id) {
  return entries.find((item) => item.id === id) || null;
}

function sliceBlockLines(lines, entries, sectionId) {
  const start = findEntry(entries, sectionId);
  if (!start) {
    return [];
  }
  const startIndex = start.line;
  const order = ["goal", "base", "principles", "spaces", "boundary"];
  const currentOrderIndex = order.indexOf(sectionId);
  let endIndex = lines.length;
  for (let index = currentOrderIndex + 1; index < order.length; index += 1) {
    const next = findEntry(entries, order[index]);
    if (next) {
      endIndex = next.line - 1;
      break;
    }
  }
  return lines.slice(startIndex, endIndex).map((text, offset) => ({
    line: startIndex + offset + 1,
    text: String(text || ""),
  }));
}

function validateTopLevelStructure({ file, lines, issues }) {
  const entries = collectTopLevelEntries(lines);
  const firstNonEmptyIndex = lines.findIndex((line) => sfGrammar.trimLine(line));
  const firstNonEmpty = firstNonEmptyIndex >= 0 ? sfGrammar.trimLine(lines[firstNonEmptyIndex]) : "";
  if (!sfGrammar.SF_MODULE_DECL_PATTERN.test(firstNonEmpty)) {
    issues.push(
      createIssue({
        file,
        line: firstNonEmptyIndex >= 0 ? firstNonEmptyIndex + 1 : 1,
        column: 1,
        code: "SFL001",
        message: "`.sf` 文件必须以 `MODULE 中文模块名:EnglishName:` 起始。",
      })
    );
  }

  const expectedOrder = ["goal", "base", "principles", "spaces", "boundary"];
  let cursor = 0;
  for (const expected of expectedOrder) {
    const entry = findEntry(entries, expected);
    if (!entry) {
      issues.push(
        createIssue({
          file,
          line: firstNonEmptyIndex >= 0 ? firstNonEmptyIndex + 1 : 1,
          column: 1,
          code: "SFL003",
          message: `缺少顶层块：${expected === "goal" ? "Goal" : expected[0].toUpperCase() + expected.slice(1)}`,
        })
      );
      continue;
    }
    const actualIndex = entries.findIndex((item) => item.line === entry.line);
    if (actualIndex < cursor) {
      issues.push(
        createIssue({
          file,
          line: entry.line,
          column: markerColumn(entry.raw),
          code: "SFL003",
          message: "顶层块顺序必须固定为 Goal / Base / Principles / Spaces / Boundary。",
        })
      );
    } else {
      cursor = actualIndex;
    }
  }

  const goalEntry = findEntry(entries, "goal");
  if (goalEntry && !sfGrammar.SF_GOAL_PATTERN.test(goalEntry.trimmed)) {
    issues.push(
      createIssue({
        file,
        line: goalEntry.line,
        column: markerColumn(goalEntry.raw),
        code: "SFL004",
        message: "`Goal` 必须写成 `Goal := \"...\"` 单行格式。",
      })
    );
  }

  return entries;
}

function validateFlatBlock({
  file,
  entries,
  lines,
  issues,
  definitions,
  references,
  sectionId,
  code,
  definitionPathPrefix,
  emptyMessage,
  invalidMessage,
}) {
  const blockLines = sliceBlockLines(lines, entries, sectionId).filter((item) => sfGrammar.trimLine(item.text));
  if (!blockLines.length) {
    issues.push(
      createIssue({
        file,
        line: findEntry(entries, sectionId)?.line || 1,
        column: 1,
        code,
        message: emptyMessage,
      })
    );
    return;
  }

  for (const item of blockLines) {
    const trimmed = sfGrammar.trimLine(item.text);
    if (sfGrammar.getIndent(item.text) !== 8) {
      issues.push(
        createIssue({
          file,
          line: item.line,
          column: 1,
          code: "SFL009",
          message: "`.sf` 声明缩进必须使用 4 空格层级。",
        })
      );
      continue;
    }
    const matchedDefinition = sfGrammar.getStatementDefinitionsForSection(sectionId)
      .find((definition) => definition.pattern.test(trimmed));
    if (!matchedDefinition) {
      issues.push(
        createIssue({
          file,
          line: item.line,
          column: markerColumn(item.text),
          code,
          message: invalidMessage,
        })
      );
      continue;
    }
    const match = trimmed.match(matchedDefinition.pattern);
    const name = String(match?.groups?.name || "").trim();
    if (name) {
      definitions.add(`${definitionPathPrefix}.${name}`);
    }
    for (const ref of collectRefs(trimmed)) {
      references.push({ ref, line: item.line, column: markerColumn(item.text), file });
    }
  }
}

function lintShelfFrameworkFile({ filePath, text }) {
  const file = String(filePath || "");
  const lines = sfGrammar.splitLines(text);
  const issues = [];
  const definitions = new Set();
  const references = [];

  for (let index = 0; index < lines.length; index += 1) {
    if (String(lines[index] || "").includes("\t")) {
      issues.push(
        createIssue({
          file,
          line: index + 1,
          column: 1,
          code: "SFL002",
          message: "`.sf` 格式禁止使用 tab，缩进必须固定为 4 个空格。",
        })
      );
    }
  }

  const entries = validateTopLevelStructure({ file, lines, issues });
  validateFlatBlock({
    file,
    entries,
    lines,
    issues,
    definitions,
    references,
    sectionId: "base",
    code: "SFL005",
    definitionPathPrefix: "Base",
    emptyMessage: "`Base` block 至少需要一个 `set/elem/relation` 声明。",
    invalidMessage: "`Base` 内只允许 `set 名称 := 值`、`elem 名称 := 值` 或 `relation[shape] 名称 := 值`。",
  });
  validateFlatBlock({
    file,
    entries,
    lines,
    sectionId: "principles",
    issues,
    definitions,
    references,
    code: "SFL006",
    definitionPathPrefix: "Principles",
    emptyMessage: "`Principles` block 至少需要一个 `sat/eq` 声明。",
    invalidMessage: "`Principles` 内只允许 `sat 名称 := 值` 或 `eq 名称 := 值`。",
  });
  validateFlatBlock({
    file,
    entries,
    lines,
    sectionId: "spaces",
    issues,
    definitions,
    references,
    code: "SFL007",
    definitionPathPrefix: "Spaces",
    emptyMessage: "`Spaces` block 至少需要一个 `comb/seq` 声明。",
    invalidMessage: "`Spaces` 内只允许 `comb 名称 := 值` 或 `seq 名称 := 值`。",
  });
  validateFlatBlock({
    file,
    entries,
    lines,
    sectionId: "boundary",
    issues,
    definitions,
    references,
    code: "SFL008",
    definitionPathPrefix: "Boundary",
    emptyMessage: "`Boundary` block 至少需要一个 `param<...>` 声明。",
    invalidMessage: "`Boundary` 内只允许 `param<子类型> 名称 := 值`、`in<子类型> 名称 := 值` 或 `out<子类型> 名称 := 值`。",
  });

  for (const reference of references) {
    if (!definitions.has(reference.ref)) {
      issues.push(
        createIssue({
          file: reference.file,
          line: reference.line,
          column: reference.column,
          code: "SFL010",
          message: `引用了未定义符号：${reference.ref}`,
        })
      );
    }
  }

  return issues;
}

module.exports = {
  lintShelfFrameworkFile,
};

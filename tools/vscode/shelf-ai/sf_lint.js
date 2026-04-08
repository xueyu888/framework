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
        message: "`.sf` 文件必须以 `module 中文模块名:EnglishName:` 起始。",
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

function validateBaseBlock({ file, entries, lines, issues, definitions, references }) {
  const blockLines = sliceBlockLines(lines, entries, "base").filter((item) => sfGrammar.trimLine(item.text));
  if (!blockLines.length) {
    issues.push(
      createIssue({
        file,
        line: findEntry(entries, "base")?.line || 1,
        column: 1,
        code: "SFL005",
        message: "`Base` block 至少需要一个 `elem/rel/attr` 声明。",
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
    const matchedDefinition = sfGrammar.getStatementDefinitionsForSection("base")
      .find((definition) => definition.pattern.test(trimmed));
    if (!matchedDefinition) {
      issues.push(
        createIssue({
          file,
          line: item.line,
          column: markerColumn(item.text),
          code: "SFL005",
          message: "`Base` 内只允许 `elem/rel/attr 名称 := 值`。",
        })
      );
      continue;
    }
    const match = trimmed.match(matchedDefinition.pattern);
    const name = String(match?.groups?.name || "").trim();
    if (name) {
      definitions.add(`Base.${name}`);
    }
    for (const ref of collectRefs(trimmed)) {
      references.push({ ref, line: item.line, column: markerColumn(item.text), file });
    }
  }
}

function validateStructuredBlock({
  file,
  entries,
  lines,
  sectionId,
  issues,
  definitions,
  references,
  code,
  allowedKinds,
  clauseOrderByKind,
  definitionPathPrefix,
}) {
  const blockLines = sliceBlockLines(lines, entries, sectionId);
  const nonEmptyLines = blockLines.filter((item) => sfGrammar.trimLine(item.text));
  if (!nonEmptyLines.length) {
    issues.push(
      createIssue({
        file,
        line: findEntry(entries, sectionId)?.line || 1,
        column: 1,
        code,
        message: `\`${definitionPathPrefix}\` block 不能为空。`,
      })
    );
    return;
  }

  let index = 0;
  let parsedCount = 0;

  while (index < nonEmptyLines.length) {
    const head = nonEmptyLines[index];
    const headTrimmed = sfGrammar.trimLine(head.text);
    if (sfGrammar.getIndent(head.text) !== 8) {
      issues.push(
        createIssue({
          file,
          line: head.line,
          column: 1,
          code: "SFL009",
          message: "`.sf` 声明头必须位于 8 空格缩进层。",
        })
      );
      index += 1;
      continue;
    }

    const headMatch = headTrimmed.match(
      /^(?<kind>[a-z]+)(?<subtype><(?:schema|range|enum)>)?\s+(?<name>[^:=]+?)\s*:=\s*$/u
    );
    if (!headMatch) {
      issues.push(
        createIssue({
          file,
          line: head.line,
          column: markerColumn(head.text),
          code,
          message: `\`${definitionPathPrefix}\` 声明头格式不合法。`,
        })
      );
      index += 1;
      continue;
    }

    const kind = String(headMatch.groups?.kind || "");
    const subtype = String(headMatch.groups?.subtype || "");
    const name = String(headMatch.groups?.name || "").trim();
    if (!allowedKinds.has(kind)) {
      issues.push(
        createIssue({
          file,
          line: head.line,
          column: markerColumn(head.text),
          code,
          message: `\`${definitionPathPrefix}\` 不允许 kind \`${kind}\`。`,
        })
      );
      index += 1;
      continue;
    }
    if (sectionId === "boundary" && !subtype) {
      issues.push(
        createIssue({
          file,
          line: head.line,
          column: markerColumn(head.text),
          code,
          message: "`Boundary` 声明必须显式写子类型，如 `in<schema>`、`param<enum>`。",
        })
      );
    }

    definitions.add(`${definitionPathPrefix}.${kind}.${name}`);
    parsedCount += 1;

    const expectedClauses = clauseOrderByKind[kind] || [];
    for (let clauseIndex = 0; clauseIndex < expectedClauses.length; clauseIndex += 1) {
      index += 1;
      const clauseLine = nonEmptyLines[index];
      if (!clauseLine) {
        issues.push(
          createIssue({
            file,
            line: head.line,
            column: markerColumn(head.text),
            code,
            message: `\`${kind} ${name}\` 缺少 clause：${expectedClauses[clauseIndex]}(...)`,
          })
        );
        break;
      }
      const clauseTrimmed = sfGrammar.trimLine(clauseLine.text);
      const clauseIndent = sfGrammar.getIndent(clauseLine.text);
      const isLastClause = clauseIndex === expectedClauses.length - 1;
      const expectedPattern = new RegExp(
        `^${expectedClauses[clauseIndex]}\\(.+\\)${isLastClause ? "" : ","}$`,
        "u"
      );

      if (clauseIndent !== 12 || !expectedPattern.test(clauseTrimmed)) {
        issues.push(
          createIssue({
            file,
            line: clauseLine.line,
            column: markerColumn(clauseLine.text),
            code,
            message: `\`${kind} ${name}\` 的 clause 必须按固定顺序书写：${expectedClauses.join(" / ")}。`,
          })
        );
      }
      for (const ref of collectRefs(clauseTrimmed)) {
        references.push({ ref, line: clauseLine.line, column: markerColumn(clauseLine.text), file });
      }
    }

    index += 1;
  }

  if (!parsedCount) {
    issues.push(
      createIssue({
        file,
        line: findEntry(entries, sectionId)?.line || 1,
        column: 1,
        code,
        message: `\`${definitionPathPrefix}\` block 中没有可解析声明。`,
      })
    );
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
  validateBaseBlock({ file, entries, lines, issues, definitions, references });
  validateStructuredBlock({
    file,
    entries,
    lines,
    sectionId: "principles",
    issues,
    definitions,
    references,
    code: "SFL006",
    allowedKinds: new Set(["form", "sat", "id", "norm"]),
    clauseOrderByKind: {
      form: ["on", "body"],
      sat: ["on", "body"],
      id: ["on", "body"],
      norm: ["on", "body"],
    },
    definitionPathPrefix: "Principles",
  });
  validateStructuredBlock({
    file,
    entries,
    lines,
    sectionId: "spaces",
    issues,
    definitions,
    references,
    code: "SFL007",
    allowedKinds: new Set(["comb", "seq"]),
    clauseOrderByKind: {
      comb: ["from", "by"],
      seq: ["from", "by"],
    },
    definitionPathPrefix: "Spaces",
  });
  validateStructuredBlock({
    file,
    entries,
    lines,
    sectionId: "boundary",
    issues,
    definitions,
    references,
    code: "SFL008",
    allowedKinds: new Set(["in", "out", "param"]),
    clauseOrderByKind: {
      in: ["payload", "card", "to"],
      out: ["payload", "card", "from"],
      param: ["domain", "affects"],
    },
    definitionPathPrefix: "Boundary",
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

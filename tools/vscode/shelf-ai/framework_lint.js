const path = require("path");

const TITLE_PATTERN = /^#\s+(?<cn>[^:]+):(?<en>.+)$/;
const CAPABILITY_LINE_PATTERN = /^-\s+`(?<id>C\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const NON_RESPONSIBILITY_LINE_PATTERN = /^-\s+`(?<id>N\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const BOUNDARY_LINE_PATTERN = /^-\s+`(?<id>[A-Z0-9_]+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const BASE_LINE_PATTERN = /^-\s+`(?<id>B\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const VERIFY_LINE_PATTERN = /^-\s+`(?<id>V\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const RULE_TOP_PATTERN = /^-\s+`(?<id>R\d+)`\s+(?<name>.+)$/;
const RULE_CHILD_PATTERN = /^\s*-\s+`(?<id>R\d+\.\d+)`\s+(?<body>.+)$/;

const SECTION_GOAL_TITLE = "## 0. 目标 (Goal)";
const SECTION_CAPABILITY_TITLES = ["## 1. 能力声明（Capability Statement）"];
const SECTION_PARAMETER_TITLES = [
  "## 2. 边界定义（Boundary / Parameter 参数）",
];
const SECTION_BASE_TITLES = ["## 3. 最小结构基（Minimal Structural Bases）"];
const SECTION_RULE_TITLES = ["## 4. 基组合原则（Base Combination Principles）"];
const SECTION_VERIFICATION_TITLES = ["## 5. 验证（Verification）"];
const RULE_BOUNDARY_BINDING_PREFIXES = ["参数绑定", "边界绑定"];
const RULE_OUTPUT_PREFIXES = ["输出能力", "失效结论"];

function normalizeSlashes(value) {
  return String(value || "").replace(/\\/g, "/");
}

function toRelativeFilePath(filePath, repoRoot) {
  if (!filePath) {
    return null;
  }
  if (!repoRoot) {
    return normalizeSlashes(filePath);
  }
  const relative = normalizeSlashes(path.relative(repoRoot, filePath));
  if (relative.startsWith("../") || relative === "..") {
    return normalizeSlashes(filePath);
  }
  return relative;
}

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

function splitSectionBlocks(lines) {
  const blocks = [];
  let current = null;

  for (let index = 0; index < lines.length; index += 1) {
    const raw = lines[index];
    const trimmed = raw.trim();
    if (trimmed.startsWith("## ")) {
      current = {
        title: trimmed,
        line: index + 1,
        entries: [],
      };
      blocks.push(current);
      continue;
    }
    if (!current) {
      continue;
    }
    current.entries.push({
      line: index + 1,
      text: raw,
      trimmed,
    });
  }

  return blocks;
}

function findSectionBlock(blocks, titles) {
  return blocks.find((block) => titles.includes(block.title)) || null;
}

function firstNonEmptyLine(lines) {
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].trim()) {
      return {
        line: index + 1,
        text: lines[index].trim(),
      };
    }
  }
  return null;
}

function markerColumn(rawLine) {
  const starIndex = rawLine.indexOf("*");
  if (starIndex >= 0) {
    return starIndex + 1;
  }
  const dashIndex = rawLine.indexOf("-");
  if (dashIndex >= 0) {
    return dashIndex + 1;
  }
  const firstChar = rawLine.search(/\S/);
  return firstChar >= 0 ? firstChar + 1 : 1;
}

function headingColumn(rawLine) {
  const firstChar = String(rawLine || "").search(/\S/);
  return firstChar >= 0 ? firstChar + 1 : 1;
}

function frameworkRequiredSectionTitles() {
  return [
    SECTION_CAPABILITY_TITLES[0],
    SECTION_PARAMETER_TITLES[0],
    SECTION_BASE_TITLES[0],
    SECTION_RULE_TITLES[0],
    SECTION_VERIFICATION_TITLES[0],
  ];
}

function validateSectionHeadingSequence({ lines, file, issues, sectionBlocks }) {
  const actualHeadings = sectionBlocks.map((block) => ({
    title: block.title,
    line: block.line,
    text: String(lines[block.line - 1] || block.title),
  }));
  const requiredTitles = frameworkRequiredSectionTitles();
  const expectedTitles = actualHeadings.some((heading) => heading.title === SECTION_GOAL_TITLE)
    ? [SECTION_GOAL_TITLE, ...requiredTitles]
    : requiredTitles;

  let actualIndex = 0;
  let expectedIndex = 0;

  while (actualIndex < actualHeadings.length && expectedIndex < expectedTitles.length) {
    const actual = actualHeadings[actualIndex];
    const expected = expectedTitles[expectedIndex];
    if (actual.title === expected) {
      actualIndex += 1;
      expectedIndex += 1;
      continue;
    }
    const matchedElsewhereIndex = expectedTitles.indexOf(actual.title);
    if (matchedElsewhereIndex > expectedIndex) {
      for (let missingIndex = expectedIndex; missingIndex < matchedElsewhereIndex; missingIndex += 1) {
        issues.push(
          createIssue({
            file,
            line: actual.line,
            column: headingColumn(actual.text),
            code: "FWL003",
            message: `缺少必需章节：${expectedTitles[missingIndex]}`,
          })
        );
      }
      expectedIndex = matchedElsewhereIndex;
      continue;
    }

    issues.push(
      createIssue({
        file,
        line: actual.line,
        column: headingColumn(actual.text),
        code: "FWL012",
        message: matchedElsewhereIndex >= 0
          ? `标准二级标题顺序错误：这里应为“${expected}”，实际是“${actual.title}”。`
          : `标准二级标题错误：这里应为“${expected}”，实际是“${actual.title}”。`,
      })
    );
    actualIndex += 1;
    if (matchedElsewhereIndex < 0) {
      expectedIndex += 1;
    }
  }

  for (let index = actualIndex; index < actualHeadings.length; index += 1) {
    const actual = actualHeadings[index];
    issues.push(
      createIssue({
        file,
        line: actual.line,
        column: headingColumn(actual.text),
        code: "FWL012",
        message: `发现非标准二级标题“${actual.title}”。`,
      })
    );
  }

  const missingAnchorLine = actualHeadings.length
    ? actualHeadings[actualHeadings.length - 1].line
    : 1;
  for (let index = expectedIndex; index < expectedTitles.length; index += 1) {
    issues.push(
      createIssue({
        file,
        line: missingAnchorLine,
        column: 1,
        code: "FWL003",
        message: `缺少必需章节：${expectedTitles[index]}`,
      })
    );
  }
}

function lintFlatListSection({
  block,
  file,
  issues,
  validPattern,
  allowPatterns = [],
  invalidCode,
  invalidMessage,
}) {
  let matchCount = 0;

  for (const row of block.entries) {
    if (!row.trimmed || row.trimmed === "---") {
      continue;
    }
    if (row.trimmed.startsWith("### ")) {
      continue;
    }
    if (!/^[-*]\s+/.test(row.trimmed)) {
      continue;
    }
    if (/^\*\s+/.test(row.trimmed)) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL004",
          message: "列表项必须使用 `-`，不要使用 `*`。",
        })
      );
      continue;
    }

    const isAllowed = validPattern.test(row.trimmed)
      || allowPatterns.some((pattern) => pattern.test(row.trimmed));
    if (isAllowed) {
      matchCount += 1;
      continue;
    }

    issues.push(
      createIssue({
        file,
        line: row.line,
        column: markerColumn(row.text),
        code: invalidCode,
        message: invalidMessage,
      })
    );
  }

  if (matchCount === 0) {
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL010",
        level: "warning",
        message: `章节“${block.title}”没有可解析的条目。`,
      })
    );
  }
}

function lintRuleSection({ block, file, issues }) {
  let matchCount = 0;

  for (const row of block.entries) {
    if (!row.trimmed || row.trimmed === "---") {
      continue;
    }
    if (row.trimmed.startsWith("### ")) {
      continue;
    }
    if (!/^\s*[-*]\s+/.test(row.text)) {
      continue;
    }
    if (/^\s*\*\s+/.test(row.text)) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL004",
          message: "列表项必须使用 `-`，不要使用 `*`。",
        })
      );
      continue;
    }

    const matchesTop = RULE_TOP_PATTERN.test(row.trimmed);
    const matchesChild = RULE_CHILD_PATTERN.test(row.text);
    if (matchesTop || matchesChild) {
      matchCount += 1;
      continue;
    }

    issues.push(
      createIssue({
        file,
        line: row.line,
        column: markerColumn(row.text),
        code: "FWL008",
        message: "规则章节条目格式错误，必须匹配 `- `R*`` 或 `- `R*.*``。",
      })
    );
  }

  if (matchCount === 0) {
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL010",
        level: "warning",
        message: `章节“${block.title}”没有可解析的条目。`,
      })
    );
  }
}

function collectSectionTokenSet(block, pattern) {
  const tokens = new Set();
  if (!block) {
    return tokens;
  }
  for (const row of block.entries) {
    if (!row || !row.trimmed) {
      continue;
    }
    const match = pattern.exec(row.trimmed);
    if (!match || !match.groups || !match.groups.id) {
      continue;
    }
    tokens.add(String(match.groups.id).trim());
  }
  return tokens;
}

function parseRuleChildClause(rowText) {
  const childMatch = RULE_CHILD_PATTERN.exec(String(rowText || ""));
  if (!childMatch || !childMatch.groups || !childMatch.groups.body) {
    return null;
  }
  const body = String(childMatch.groups.body).trim().replace(/。$/, "");
  const separatorIndex = body.search(/[：:]/);
  if (separatorIndex < 0) {
    return null;
  }
  const label = body.slice(0, separatorIndex).trim();
  const expression = body.slice(separatorIndex + 1).trim();
  if (!label || !expression) {
    return null;
  }
  return {
    label,
    expression,
  };
}

function extractSimpleTokens(expression, regex) {
  const tokens = [];
  for (const match of String(expression || "").matchAll(regex)) {
    if (!match || !match[0]) {
      continue;
    }
    tokens.push(match[0]);
  }
  return [...new Set(tokens)];
}

function extractBoundaryTokens(expression) {
  const expr = String(expression || "");
  const segments = [...expr.matchAll(/`([^`]+)`/g)].map((match) => String(match[1] || ""));
  const sources = segments.length ? segments : [expr];
  const tokens = [];
  for (const source of sources) {
    for (const match of source.matchAll(/\b[A-Z][A-Z0-9_]*\b/g)) {
      if (!match || !match[0]) {
        continue;
      }
      tokens.push(match[0]);
    }
  }
  return [...new Set(tokens)];
}

function extractSourceExpression(text) {
  const raw = String(text || "");
  const match = /来源[：:]\s*(.+)$/.exec(raw);
  return (match ? match[1] : raw).trim();
}

function isBoundaryLikeToken(token) {
  const value = String(token || "").trim();
  if (!value) {
    return false;
  }
  if (/^P\d+$/.test(value)) {
    return true;
  }
  if (!/^[A-Z][A-Z0-9_]+$/.test(value)) {
    return false;
  }
  if (/^(?:L|M)\d+$/.test(value)) {
    return false;
  }
  if (/^R\d+(?:\.\d+)?$/.test(value)) {
    return false;
  }
  if (/^[CBV]\d+$/.test(value)) {
    return false;
  }
  return true;
}

function unresolvedSymbolIssue({ file, row, token, message }) {
  const text = String(row?.text || "");
  const index = text.indexOf(token);
  return createIssue({
    file,
    line: row.line,
    column: index >= 0 ? index + 1 : markerColumn(text),
    code: "FWL011",
    message,
  });
}

function lintRuleReferenceIntegrity({
  block,
  file,
  issues,
  capabilityIds,
  boundaryIds,
  baseIds,
}) {
  if (!block) {
    return;
  }
  const canCheckCapability = capabilityIds.size > 0;
  const canCheckBoundary = boundaryIds.size > 0;
  const canCheckBase = baseIds.size > 0;

  for (const row of block.entries) {
    const clause = parseRuleChildClause(row.text);
    if (!clause) {
      continue;
    }

    if (canCheckBase && clause.label === "参与基") {
      for (const token of extractSimpleTokens(clause.expression, /\bB\d+\b/g)) {
        if (baseIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `规则引用了未定义的结构基 \`${token}\`。请先在“## 3. 最小结构基（Minimal Structural Bases）”中定义。`,
          })
        );
      }
      continue;
    }

    if (canCheckCapability && RULE_OUTPUT_PREFIXES.includes(clause.label)) {
      for (const token of extractSimpleTokens(clause.expression, /\bC\d+\b/g)) {
        if (capabilityIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `规则引用了未定义的能力 \`${token}\`。请先在“## 1. 能力声明（Capability Statement）”中定义。`,
          })
        );
      }
      continue;
    }

    if (canCheckBoundary && RULE_BOUNDARY_BINDING_PREFIXES.includes(clause.label)) {
      for (const token of extractBoundaryTokens(clause.expression)) {
        if (boundaryIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `规则引用了未定义的参数 \`${token}\`。请先在“## 2. 边界定义（Boundary / Parameter 参数）”中定义。`,
          })
        );
      }
    }
  }
}

function lintBoundaryReferenceIntegrity({
  block,
  file,
  issues,
  capabilityIds,
}) {
  if (!block || capabilityIds.size === 0) {
    return;
  }
  for (const row of block.entries) {
    const match = BOUNDARY_LINE_PATTERN.exec(row.trimmed);
    if (!match || !match.groups || !match.groups.body) {
      continue;
    }
    const sourceExpr = extractSourceExpression(match.groups.body);
    for (const token of extractSimpleTokens(sourceExpr, /\bC\d+\b/g)) {
      if (capabilityIds.has(token)) {
        continue;
      }
      issues.push(
        unresolvedSymbolIssue({
          file,
          row,
          token,
          message: `参数来源引用了未定义的能力 \`${token}\`。请先在“## 1. 能力声明（Capability Statement）”中定义。`,
        })
      );
    }
  }
}

function lintBaseReferenceIntegrity({
  block,
  file,
  issues,
  capabilityIds,
  boundaryIds,
}) {
  if (!block) {
    return;
  }
  const canCheckCapability = capabilityIds.size > 0;
  const canCheckBoundary = boundaryIds.size > 0;

  for (const row of block.entries) {
    const match = BASE_LINE_PATTERN.exec(row.trimmed);
    if (!match || !match.groups || !match.groups.body) {
      continue;
    }
    const sourceExpr = extractSourceExpression(match.groups.body);
    if (canCheckCapability) {
      for (const token of extractSimpleTokens(sourceExpr, /\bC\d+\b/g)) {
        if (capabilityIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `结构基来源引用了未定义的能力 \`${token}\`。请先在“## 1. 能力声明（Capability Statement）”中定义。`,
          })
        );
      }
    }
    if (canCheckBoundary) {
      for (const token of extractBoundaryTokens(sourceExpr).filter(isBoundaryLikeToken)) {
        if (boundaryIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `结构基来源引用了未定义的参数 \`${token}\`。请先在“## 2. 边界定义（Boundary / Parameter 参数）”中定义。`,
          })
        );
      }
    }
  }
}

function lintFrameworkMarkdown({ repoRoot, filePath, text }) {
  const lines = String(text || "").split(/\r?\n/);
  const file = toRelativeFilePath(filePath, repoRoot);
  const issues = [];

  const firstLine = firstNonEmptyLine(lines);
  if (!firstLine) {
    issues.push(
      createIssue({
        file,
        line: 1,
        column: 1,
        code: "FWL001",
        message: "框架文件缺少标题行 `# 中文名:EnglishName`。",
      })
    );
    return issues;
  }

  if (!TITLE_PATTERN.test(firstLine.text)) {
    issues.push(
      createIssue({
        file,
        line: firstLine.line,
        column: 1,
        code: "FWL001",
        message: "标题格式错误，必须是 `# 中文名:EnglishName`。",
      })
    );
  }

  const directiveLines = [];
  for (let index = 0; index < lines.length; index += 1) {
    const trimmed = lines[index].trim();
    if (trimmed.startsWith("@framework")) {
      directiveLines.push({
        line: index + 1,
        text: trimmed,
      });
    }
  }

  if (directiveLines.length === 0) {
    issues.push(
      createIssue({
        file,
        line: Math.max(1, firstLine.line + 1),
        column: 1,
        code: "FWL002",
        message: "缺少 `@framework` 指令。",
      })
    );
  }
  for (const directive of directiveLines) {
    if (directive.text !== "@framework") {
      issues.push(
        createIssue({
          file,
          line: directive.line,
          column: 1,
          code: "FWL002",
          message: "`@framework` 必须为无参数单行指令。",
        })
      );
    }
  }

  const sectionBlocks = splitSectionBlocks(lines);
  validateSectionHeadingSequence({
    lines,
    file,
    issues,
    sectionBlocks,
  });

  const capabilitySection = findSectionBlock(sectionBlocks, SECTION_CAPABILITY_TITLES);
  if (capabilitySection) {
    lintFlatListSection({
      block: capabilitySection,
      file,
      issues,
      validPattern: CAPABILITY_LINE_PATTERN,
      allowPatterns: [NON_RESPONSIBILITY_LINE_PATTERN],
      invalidCode: "FWL005",
      invalidMessage: "能力章节条目格式错误，必须匹配 `- `C*` 名称：描述。` 或 `- `N*` 名称：描述。`。",
    });
  }

  const parameterSection = findSectionBlock(sectionBlocks, SECTION_PARAMETER_TITLES);
  if (parameterSection) {
    lintFlatListSection({
      block: parameterSection,
      file,
      issues,
      validPattern: BOUNDARY_LINE_PATTERN,
      invalidCode: "FWL006",
      invalidMessage: "参数章节条目格式错误，必须匹配 `- `PARAM` 名称：描述。来源：`C*``。",
    });
  }

  const baseSection = findSectionBlock(sectionBlocks, SECTION_BASE_TITLES);
  if (baseSection) {
    lintFlatListSection({
      block: baseSection,
      file,
      issues,
      validPattern: BASE_LINE_PATTERN,
      invalidCode: "FWL007",
      invalidMessage: "最小结构基章节条目格式错误，必须匹配 `- `B*` 名称：描述。来源：`...``。",
    });
  }

  const ruleSection = findSectionBlock(sectionBlocks, SECTION_RULE_TITLES);
  if (ruleSection) {
    lintRuleSection({
      block: ruleSection,
      file,
      issues,
    });
  }

  const verificationSection = findSectionBlock(sectionBlocks, SECTION_VERIFICATION_TITLES);
  if (verificationSection) {
    lintFlatListSection({
      block: verificationSection,
      file,
      issues,
      validPattern: VERIFY_LINE_PATTERN,
      invalidCode: "FWL009",
      invalidMessage: "验证章节条目格式错误，必须匹配 `- `V*` 名称：描述。`。",
    });
  }

  const capabilityIds = collectSectionTokenSet(capabilitySection, CAPABILITY_LINE_PATTERN);
  const boundaryIds = collectSectionTokenSet(parameterSection, BOUNDARY_LINE_PATTERN);
  const baseIds = collectSectionTokenSet(baseSection, BASE_LINE_PATTERN);

  lintBoundaryReferenceIntegrity({
    block: parameterSection,
    file,
    issues,
    capabilityIds,
  });

  lintBaseReferenceIntegrity({
    block: baseSection,
    file,
    issues,
    capabilityIds,
    boundaryIds,
  });

  lintRuleReferenceIntegrity({
    block: ruleSection,
    file,
    issues,
    capabilityIds,
    boundaryIds,
    baseIds,
  });

  return issues;
}

module.exports = {
  lintFrameworkMarkdown,
};

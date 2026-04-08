const path = require("path");

const TITLE_PATTERN = /^#\s+(?<cn>[^:]+):(?<en>.+)$/;
const CAPABILITY_LINE_PATTERN = /^-\s+`(?<id>C\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const NON_RESPONSIBILITY_LINE_PATTERN = /^-\s+`(?<id>N\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const BASE_LINE_PATTERN = /^-\s+`(?<id>B\d+)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const RULE_LINE_PATTERN = /^-\s+`(?<id>R\d+)`\s+`(?<name>[^`]+)`[：:]\s*(?<body>.+)$/;
const PORT_LINE_PATTERN = /^-\s+`(?<id>[A-Za-z][A-Za-z0-9_]*)`\s*[：:]\s*(?<body>.+)$/;
const PARAMETER_LINE_PATTERN = /^-\s+`(?<id>[A-Za-z][A-Za-z0-9_]*)`\s+(?<name>[^：:]+)[：:]\s*(?<body>.+)$/;
const SYMBOL_TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9_]*/g;
const FORBIDDEN_CONFIG_SECTION_PATTERN = /\[(?:exact|communication|framework)\.[^\]]+\]/i;

const SECTION_GOAL_TITLE = "## 0. 目标 (Goal)";
const SECTION_BASE_TITLE = "## 1. 最小结构基（Minimal Structural Bases）";
const SECTION_RULE_TITLE = "## 2. 基排列组合（Base Arrangement / Combination）";
const SECTION_BOUNDARY_TITLE = "## 3. 边界定义（Boundary）";
const SECTION_CAPABILITY_TITLE = "## 4. 能力声明（Capability Statement）";

const SECTION_BOUNDARY_PORTS_TITLE = "### 3.1 接口定义（IO / Ports）";
const SECTION_BOUNDARY_PARAMETERS_TITLE = "### 3.2 参数边界（Parameter Constraints）";

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

function findSectionBlock(blocks, title) {
  return blocks.find((block) => block.title === title) || null;
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
    SECTION_GOAL_TITLE,
    SECTION_BASE_TITLE,
    SECTION_RULE_TITLE,
    SECTION_BOUNDARY_TITLE,
    SECTION_CAPABILITY_TITLE,
  ];
}

function validateSectionHeadingSequence({ lines, file, issues, sectionBlocks }) {
  const actualHeadings = sectionBlocks.map((block) => ({
    title: block.title,
    line: block.line,
    text: String(lines[block.line - 1] || block.title),
  }));
  const expectedTitles = frameworkRequiredSectionTitles();

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

function extractBoundarySubsections({ block, file, issues }) {
  const portBlock = {
    title: SECTION_BOUNDARY_PORTS_TITLE,
    line: block.line,
    entries: [],
  };
  const parameterBlock = {
    title: SECTION_BOUNDARY_PARAMETERS_TITLE,
    line: block.line,
    entries: [],
  };

  let activeSubsection = "";
  let hasPortsHeading = false;
  let hasParametersHeading = false;

  for (const row of block.entries) {
    if (!row.trimmed || row.trimmed === "---") {
      continue;
    }
    if (row.trimmed.startsWith("### ")) {
      if (row.trimmed === SECTION_BOUNDARY_PORTS_TITLE) {
        hasPortsHeading = true;
        portBlock.line = row.line;
        activeSubsection = "ports";
        continue;
      }
      if (row.trimmed === SECTION_BOUNDARY_PARAMETERS_TITLE) {
        hasParametersHeading = true;
        parameterBlock.line = row.line;
        activeSubsection = "parameters";
        continue;
      }
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: headingColumn(row.text),
          code: "FWL006",
          message: `边界定义子章节标题错误：必须使用“${SECTION_BOUNDARY_PORTS_TITLE}”或“${SECTION_BOUNDARY_PARAMETERS_TITLE}”。`,
        })
      );
      activeSubsection = "";
      continue;
    }

    if (!activeSubsection) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL006",
          message: "边界定义中的内容必须位于 3.1 接口定义或 3.2 参数边界子章节内。",
        })
      );
      continue;
    }

    if (activeSubsection === "ports") {
      portBlock.entries.push(row);
      continue;
    }
    if (activeSubsection === "parameters") {
      parameterBlock.entries.push(row);
    }
  }

  if (!hasPortsHeading) {
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL006",
        message: `缺少必需子章节：${SECTION_BOUNDARY_PORTS_TITLE}`,
      })
    );
  }
  if (!hasParametersHeading) {
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL006",
        message: `缺少必需子章节：${SECTION_BOUNDARY_PARAMETERS_TITLE}`,
      })
    );
  }

  return {
    portBlock: hasPortsHeading ? portBlock : null,
    parameterBlock: hasParametersHeading ? parameterBlock : null,
  };
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

    if (RULE_LINE_PATTERN.test(row.trimmed)) {
      matchCount += 1;
      continue;
    }

    issues.push(
      createIssue({
        file,
        line: row.line,
        column: markerColumn(row.text),
        code: "FWL008",
        message: "基排列组合章节条目格式错误，必须匹配 `- `R*` `规则名`：由 ... 导出 ...`。",
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

function collectSectionTokenOccurrences(block, patterns) {
  const occurrences = new Map();
  if (!block) {
    return occurrences;
  }
  for (const row of block.entries) {
    if (!row || !row.trimmed) {
      continue;
    }
    for (const pattern of patterns) {
      const match = pattern.exec(row.trimmed);
      if (!match || !match.groups || !match.groups.id) {
        continue;
      }
      const token = String(match.groups.id).trim();
      if (!token) {
        continue;
      }
      if (!occurrences.has(token)) {
        occurrences.set(token, []);
      }
      occurrences.get(token).push(row);
      break;
    }
  }
  return occurrences;
}

function lintDuplicateTokenOccurrences({ file, issues, occurrences }) {
  for (const [token, rows] of occurrences.entries()) {
    if (!Array.isArray(rows) || rows.length <= 1) {
      continue;
    }
    const firstLine = rows[0].line;
    for (const row of rows.slice(1)) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL013",
          message: `编号重复：\`${token}\` 已在第 ${firstLine} 行定义。`,
        })
      );
    }
  }
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

function extractBoundaryLikeTokens(expression) {
  const tokens = [];
  for (const match of String(expression || "").matchAll(SYMBOL_TOKEN_PATTERN)) {
    const token = String(match[0] || "");
    if (!token) {
      continue;
    }
    if (/^(?:[BCNRV]\d+|L\d+|M\d+)$/i.test(token)) {
      continue;
    }
    if (/^P\d+$/i.test(token) || token.includes("_")) {
      tokens.push(token);
    }
  }
  return [...new Set(tokens)];
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
  baseIds,
  boundaryIds,
}) {
  if (!block) {
    return;
  }
  const canCheckCapability = capabilityIds.size > 0;
  const canCheckBase = baseIds.size > 0;
  const boundaryIdSet = new Set([...boundaryIds].map((item) => String(item || "").toLowerCase()));

  for (const row of block.entries) {
    const match = RULE_LINE_PATTERN.exec(row.trimmed);
    if (!match || !match.groups || !match.groups.body) {
      continue;
    }
    const expression = String(match.groups.body || "");
    const outputTokens = extractSimpleTokens(expression, /\bC\d+\b/g);
    const invalidTokens = extractSimpleTokens(expression, /\bN\d+\b/g);

    if (!outputTokens.length && !invalidTokens.length) {
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: markerColumn(row.text),
          code: "FWL014",
          message: "规则必须至少声明一种结果：输出能力（C*）或失效结论（N*）。",
        })
      );
    }

    if (canCheckBase) {
      for (const token of extractSimpleTokens(expression, /\bB\d+\b/g)) {
        if (baseIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `规则引用了未定义的结构基 \`${token}\`。请先在“${SECTION_BASE_TITLE}”中定义。`,
          })
        );
      }
    }

    if (canCheckCapability) {
      for (const token of outputTokens) {
        if (capabilityIds.has(token)) {
          continue;
        }
        issues.push(
          unresolvedSymbolIssue({
            file,
            row,
            token,
            message: `规则引用了未定义的能力 \`${token}\`。请先在“${SECTION_CAPABILITY_TITLE}”中定义。`,
          })
        );
      }
    }

    for (const token of extractBoundaryLikeTokens(expression)) {
      if (boundaryIdSet.has(token.toLowerCase())) {
        continue;
      }
      issues.push(
        unresolvedSymbolIssue({
          file,
          row,
          token,
          message: `规则引用了未定义的边界符号 \`${token}\`。请先在“${SECTION_BOUNDARY_TITLE}”中定义。`,
        })
      );
    }
  }
}

function lintForbiddenLegacyPatterns({ lines, file, issues }) {
  for (let index = 0; index < lines.length; index += 1) {
    const text = String(lines[index] || "");
    const trimmed = text.trim();
    if (!trimmed) {
      continue;
    }
    if (/上游模块[：:]/.test(trimmed)) {
      issues.push(
        createIssue({
          file,
          line: index + 1,
          column: markerColumn(text),
          code: "FWL015",
          message: "禁止使用“上游模块：...”，请在 B* 主句中内联写模块引用。",
        })
      );
    }
    if (/project\.toml/i.test(trimmed)) {
      issues.push(
        createIssue({
          file,
          line: index + 1,
          column: markerColumn(text),
          code: "FWL015",
          message: "framework 正文不得直接写入 project.toml 路径。",
        })
      );
    }
    if (FORBIDDEN_CONFIG_SECTION_PATTERN.test(trimmed)) {
      issues.push(
        createIssue({
          file,
          line: index + 1,
          column: markerColumn(text),
          code: "FWL015",
          message: "framework 正文不得直接写入配置 section 语法（exact/communication/framework）。",
        })
      );
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

  const baseSection = findSectionBlock(sectionBlocks, SECTION_BASE_TITLE);
  if (baseSection) {
    lintFlatListSection({
      block: baseSection,
      file,
      issues,
      validPattern: BASE_LINE_PATTERN,
      invalidCode: "FWL007",
      invalidMessage: "最小结构基章节条目格式错误，必须匹配 `- `B*` 名称：描述。`。",
    });
  }

  const ruleSection = findSectionBlock(sectionBlocks, SECTION_RULE_TITLE);
  if (ruleSection) {
    lintRuleSection({
      block: ruleSection,
      file,
      issues,
    });
  }

  const boundarySection = findSectionBlock(sectionBlocks, SECTION_BOUNDARY_TITLE);
  let portBlock = null;
  let parameterBlock = null;
  if (boundarySection) {
    const boundarySubsections = extractBoundarySubsections({
      block: boundarySection,
      file,
      issues,
    });
    if (boundarySubsections.portBlock) {
      portBlock = boundarySubsections.portBlock;
      lintFlatListSection({
        block: boundarySubsections.portBlock,
        file,
        issues,
        validPattern: PORT_LINE_PATTERN,
        invalidCode: "FWL006",
        invalidMessage: "接口定义条目格式错误，必须匹配 `- `PORT_ID`：描述。`。",
      });
    }
    if (boundarySubsections.parameterBlock) {
      parameterBlock = boundarySubsections.parameterBlock;
      lintFlatListSection({
        block: boundarySubsections.parameterBlock,
        file,
        issues,
        validPattern: PARAMETER_LINE_PATTERN,
        invalidCode: "FWL006",
        invalidMessage: "参数边界条目格式错误，必须匹配 `- `PARAM` 参数名：描述。`。",
      });
    }
  }

  const capabilitySection = findSectionBlock(sectionBlocks, SECTION_CAPABILITY_TITLE);
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

  lintForbiddenLegacyPatterns({
    lines,
    file,
    issues,
  });

  lintDuplicateTokenOccurrences({
    file,
    issues,
    occurrences: collectSectionTokenOccurrences(capabilitySection, [
      CAPABILITY_LINE_PATTERN,
      NON_RESPONSIBILITY_LINE_PATTERN,
    ]),
  });
  lintDuplicateTokenOccurrences({
    file,
    issues,
    occurrences: collectSectionTokenOccurrences(baseSection, [BASE_LINE_PATTERN]),
  });
  lintDuplicateTokenOccurrences({
    file,
    issues,
    occurrences: collectSectionTokenOccurrences(ruleSection, [RULE_LINE_PATTERN]),
  });

  const capabilityIds = collectSectionTokenSet(capabilitySection, CAPABILITY_LINE_PATTERN);
  const baseIds = collectSectionTokenSet(baseSection, BASE_LINE_PATTERN);
  const boundaryIds = new Set([
    ...collectSectionTokenSet(portBlock, PORT_LINE_PATTERN),
    ...collectSectionTokenSet(parameterBlock, PARAMETER_LINE_PATTERN),
  ]);
  lintRuleReferenceIntegrity({
    block: ruleSection,
    file,
    issues,
    capabilityIds,
    baseIds,
    boundaryIds,
  });

  return issues;
}

module.exports = {
  lintFrameworkMarkdown,
};

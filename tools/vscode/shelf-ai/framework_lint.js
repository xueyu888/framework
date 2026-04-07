const fs = require("fs");
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
const FRAMEWORK_MODULE_PATH_PATTERN = /^(framework|framework_drafts)\/([^/]+)\/L\d+-M\d+-[^/]+\.md$/;
const FRAMEWORK_CONTROLLED_PATH_PATTERN = /^(framework|framework_drafts)(?:\/|$)/;
const MARKDOWN_LINK_PATTERN = /\[[^\]]*]\(([^)]+)\)/g;

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

function toLowerPath(value) {
  return normalizeSlashes(value).toLowerCase();
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

function isMarkdownPath(value) {
  return toLowerPath(value).endsWith(".md");
}

function isControlledFrameworkPath(value) {
  return FRAMEWORK_CONTROLLED_PATH_PATTERN.test(normalizeSlashes(value));
}

function getFrameworkScopeInfo(relPath) {
  const normalized = normalizeSlashes(relPath);
  const parts = normalized.split("/").filter(Boolean);
  if (!parts.length || (parts[0] !== "framework" && parts[0] !== "framework_drafts")) {
    return null;
  }
  return {
    rootName: parts[0],
    domain: parts[1] || "",
    relativeWithinDomain: parts.slice(2).join("/"),
  };
}

function parseFrameworkDirectiveLines(text) {
  const lines = String(text || "").split(/\r?\n/);
  const directives = [];
  for (let index = 0; index < lines.length; index += 1) {
    const trimmed = lines[index].trim();
    if (!trimmed.startsWith("@framework")) {
      continue;
    }
    directives.push({
      line: index + 1,
      text: trimmed,
    });
  }
  return directives;
}

function hasFrameworkDirective(text) {
  return parseFrameworkDirectiveLines(text).length > 0;
}

function classifyFrameworkMarkdown({ repoRoot, filePath, text }) {
  const relativePath = toRelativeFilePath(filePath, repoRoot);
  const normalizedPath = normalizeSlashes(relativePath || "");
  const scopeInfo = getFrameworkScopeInfo(normalizedPath);
  const directiveLines = parseFrameworkDirectiveLines(text);
  const isMarkdown = isMarkdownPath(normalizedPath);
  const isModulePath = FRAMEWORK_MODULE_PATH_PATTERN.test(normalizedPath);
  const isControlledMarkdown = Boolean(scopeInfo) && isMarkdown;
  const isFrameworkModuleDocument = directiveLines.length > 0 || isModulePath;

  return {
    file: normalizedPath,
    isMarkdown,
    isControlledMarkdown,
    isFrameworkModuleDocument,
    isModulePath,
    hasFrameworkDirective: directiveLines.length > 0,
    directiveLines,
    scopeInfo,
    shouldLint: isMarkdown && (isControlledMarkdown || directiveLines.length > 0),
  };
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

function dedupeIssues(issues) {
  const seen = new Set();
  const deduped = [];
  for (const issue of issues || []) {
    const signature = [
      String(issue?.file || ""),
      Number(issue?.line || 1),
      Number(issue?.column || 1),
      String(issue?.code || ""),
      String(issue?.message || ""),
      String(issue?.level || ""),
    ].join("::");
    if (seen.has(signature)) {
      continue;
    }
    seen.add(signature);
    deduped.push(issue);
  }
  return deduped;
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

function lintFrameworkModuleMarkdown({ repoRoot, filePath, text }) {
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

  const directiveLines = parseFrameworkDirectiveLines(text);

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

function trimMarkdownLinkTarget(rawTarget) {
  let target = String(rawTarget || "").trim();
  if (target.startsWith("<") && target.endsWith(">")) {
    target = target.slice(1, -1).trim();
  }
  const titleMatch = /^(?<path>.+?)\s+["'][^"']*["']$/.exec(target);
  if (titleMatch?.groups?.path) {
    target = titleMatch.groups.path.trim();
  }
  const hashIndex = target.indexOf("#");
  if (hashIndex >= 0) {
    target = target.slice(0, hashIndex);
  }
  return target.trim();
}

function isExternalMarkdownLink(target) {
  const text = String(target || "").trim();
  return !text
    || text.startsWith("#")
    || /^[a-z][a-z0-9+.-]*:/i.test(text)
    || text.startsWith("//");
}

function offsetToLineColumn(text, offset) {
  const source = String(text || "");
  const safeOffset = Math.max(0, Math.min(Number(offset || 0), source.length));
  let line = 1;
  let column = 1;
  for (let index = 0; index < safeOffset; index += 1) {
    if (source[index] === "\n") {
      line += 1;
      column = 1;
      continue;
    }
    column += 1;
  }
  return { line, column };
}

function extractLocalMarkdownLinks(filePath, text) {
  const links = [];
  const source = String(text || "");
  for (const match of source.matchAll(MARKDOWN_LINK_PATTERN)) {
    const rawTarget = String(match[1] || "");
    const target = trimMarkdownLinkTarget(rawTarget);
    if (isExternalMarkdownLink(target)) {
      continue;
    }
    const offset = Number(match.index || 0) + match[0].indexOf(rawTarget);
    const location = offsetToLineColumn(source, offset);
    const resolvedPath = path.resolve(path.dirname(filePath), target);
    links.push({
      rawTarget,
      target,
      resolvedPath,
      line: location.line,
      column: location.column,
    });
  }
  return links;
}

function listControlledMarkdownFiles(repoRoot) {
  const files = [];
  const walk = (currentPath) => {
    if (!fs.existsSync(currentPath) || !fs.statSync(currentPath).isDirectory()) {
      return;
    }
    for (const entry of fs.readdirSync(currentPath, { withFileTypes: true })) {
      const childPath = path.join(currentPath, entry.name);
      if (entry.isDirectory()) {
        walk(childPath);
        continue;
      }
      const relPath = normalizeSlashes(path.relative(repoRoot, childPath));
      if (isMarkdownPath(relPath) && isControlledFrameworkPath(relPath)) {
        files.push(childPath);
      }
    }
  };

  walk(path.join(repoRoot, "framework"));
  walk(path.join(repoRoot, "framework_drafts"));
  return files.sort();
}

function readFileWithOverrides(filePath, overrides) {
  if (overrides && Object.prototype.hasOwnProperty.call(overrides, filePath)) {
    return String(overrides[filePath] || "");
  }
  return fs.readFileSync(filePath, "utf8");
}

function sameFrameworkScope(left, right) {
  return Boolean(left)
    && Boolean(right)
    && left.rootName === right.rootName
    && left.domain
    && left.domain === right.domain;
}

function lintFrameworkWorkspace({ repoRoot, documentOverrides = {} }) {
  const issues = [];
  const entries = listControlledMarkdownFiles(repoRoot).map((filePath) => {
    const text = readFileWithOverrides(filePath, documentOverrides);
    const classification = classifyFrameworkMarkdown({ repoRoot, filePath, text });
    return {
      filePath,
      text,
      classification,
    };
  });

  const controlledModules = entries.filter((entry) => entry.classification.isModulePath);
  const controlledAttachments = entries.filter((entry) => !entry.classification.isModulePath);
  const referencedAttachments = new Set();

  for (const entry of entries) {
    issues.push(...lintFrameworkMarkdown({
      repoRoot,
      filePath: entry.filePath,
      text: entry.text,
    }));
  }

  for (const entry of controlledModules) {
    const sourceScope = entry.classification.scopeInfo;
    for (const link of extractLocalMarkdownLinks(entry.filePath, entry.text)) {
      const resolvedRelPath = normalizeSlashes(path.relative(repoRoot, link.resolvedPath));
      const targetScope = getFrameworkScopeInfo(resolvedRelPath);
      const targetExists = fs.existsSync(link.resolvedPath) && fs.statSync(link.resolvedPath).isFile();
      const targetIsMarkdown = isMarkdownPath(link.target);

      if (!targetExists) {
        issues.push(
          createIssue({
            file: entry.classification.file,
            line: link.line,
            column: link.column,
            code: "FWL017",
            message: `framework 模块引用的 Markdown 不存在：\`${link.target}\`。`,
          })
        );
        continue;
      }
      if (!targetIsMarkdown) {
        issues.push(
          createIssue({
            file: entry.classification.file,
            line: link.line,
            column: link.column,
            code: "FWL017",
            message: `framework 模块只允许直接引用 Markdown 文件：\`${link.target}\`。`,
          })
        );
        continue;
      }
      if (!sameFrameworkScope(sourceScope, targetScope)) {
        issues.push(
          createIssue({
            file: entry.classification.file,
            line: link.line,
            column: link.column,
            code: "FWL017",
            message: `framework 模块引用的 Markdown 必须位于同一受控域内：\`${link.target}\`。`,
          })
        );
        continue;
      }
      if (!FRAMEWORK_MODULE_PATH_PATTERN.test(resolvedRelPath)) {
        referencedAttachments.add(resolvedRelPath);
      }
    }
  }

  for (const entry of controlledAttachments) {
    const relPath = entry.classification.file;
    const scopeInfo = entry.classification.scopeInfo;
    if (!scopeInfo?.domain) {
      issues.push(
        createIssue({
          file: relPath,
          line: 1,
          column: 1,
          code: "FWL018",
          message: "framework 受控目录中的附属 Markdown 必须位于 `<root>/<domain>/...` 下，并被同域模块直接引用。",
        })
      );
      continue;
    }
    if (!referencedAttachments.has(relPath)) {
      issues.push(
        createIssue({
          file: relPath,
          line: 1,
          column: 1,
          code: "FWL018",
          message: "只有被 framework 模块直接引用的 Markdown 附件才是有效作者源；当前文件未被引用。",
        })
      );
    }
  }

  return dedupeIssues(issues);
}

function lintFrameworkMarkdown({ repoRoot, filePath, text }) {
  const classification = classifyFrameworkMarkdown({ repoRoot, filePath, text });
  if (!classification.shouldLint) {
    return [];
  }

  const issues = [];
  if (classification.isFrameworkModuleDocument) {
    issues.push(...lintFrameworkModuleMarkdown({ repoRoot, filePath, text }));
    if (!classification.isModulePath) {
      issues.push(
        createIssue({
          file: classification.file,
          line: classification.directiveLines[0]?.line || 1,
          column: 1,
          code: "FWL016",
          message: "带 `@framework` 的模块文件必须位于 `framework/<domain>/L*-M*-*.md` 或 `framework_drafts/<domain>/L*-M*-*.md`。",
        })
      );
    }
  }

  return dedupeIssues(issues);
}

module.exports = {
  classifyFrameworkMarkdown,
  hasFrameworkDirective,
  isControlledFrameworkPath,
  lintFrameworkWorkspace,
  lintFrameworkMarkdown,
};

const fs = require("fs");
const path = require("path");
const frameworkGrammar = require("./framework_grammar");

const TITLE_PATTERN = frameworkGrammar.FRAMEWORK_TITLE_PATTERN;
const FRAMEWORK_DIRECTIVE = frameworkGrammar.FRAMEWORK_DIRECTIVE;
const FRAMEWORK_REQUIRED_TOP_LEVEL_SECTIONS = frameworkGrammar.FRAMEWORK_REQUIRED_TOP_LEVEL_SECTIONS;
const FRAMEWORK_REQUIRED_BOUNDARY_SECTIONS = frameworkGrammar.FRAMEWORK_REQUIRED_BOUNDARY_SECTIONS;
const FRAMEWORK_SECTION_HEADINGS = frameworkGrammar.FRAMEWORK_SECTION_HEADINGS;

const FORBIDDEN_CONFIG_SECTION_PATTERN = /\[(?:exact|communication|framework)\.[^\]]+\]/i;
const FRAMEWORK_MODULE_PATH_PATTERN = /^(framework|framework_drafts)\/([^/]+)\/L\d+-M\d+-[^/]+\.md$/;
const FRAMEWORK_CONTROLLED_PATH_PATTERN = /^(framework|framework_drafts)(?:\/|$)/;
const MARKDOWN_LINK_PATTERN = /\[[^\]]*]\(([^)]+)\)/g;

const SYMBOL_REFERENCE_PATTERN = /\b(?<kind>base|cs|cp\.(?:form|sat|id|norm)|bd\.(?:in|out|param))\.(?<name>[^,\s<>(){}[\]]+)/gu;

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
  const lines = frameworkGrammar.splitLines(text);
  const directives = [];
  for (let index = 0; index < lines.length; index += 1) {
    const trimmed = lines[index].trim();
    if (!trimmed.startsWith(FRAMEWORK_DIRECTIVE)) {
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
  const firstChar = String(rawLine || "").search(/\S/u);
  return firstChar >= 0 ? firstChar + 1 : 1;
}

function headingColumn(rawLine) {
  const firstChar = String(rawLine || "").search(/\S/u);
  return firstChar >= 0 ? firstChar + 1 : 1;
}

function validateTopSectionHeadingSequence({ lines, file, issues, sectionBlocks }) {
  const actualHeadings = sectionBlocks.map((block) => ({
    title: block.title,
    line: block.line,
    text: String(lines[block.line - 1] || block.title),
  }));
  const expectedTitles = FRAMEWORK_REQUIRED_TOP_LEVEL_SECTIONS;

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

function collectLogicalStatements(entries) {
  const statements = [];
  let current = null;

  const flush = () => {
    if (current && current.rows.length) {
      statements.push(current);
    }
    current = null;
  };

  for (const row of entries || []) {
    const trimmed = String(row?.trimmed || "");
    if (!trimmed) {
      flush();
      continue;
    }
    if (trimmed.startsWith("### ")) {
      flush();
      continue;
    }

    const statementKind = frameworkGrammar.detectStatementKind(trimmed);
    const isIndented = /^\s+/u.test(String(row?.text || ""));

    if (statementKind) {
      flush();
      current = { rows: [row] };
      continue;
    }
    if (current && isIndented) {
      current.rows.push(row);
      continue;
    }

    flush();
    current = { rows: [row] };
  }

  flush();
  return statements;
}

function lintSectionStatements({
  file,
  issues,
  block,
  sectionId,
  invalidCode,
  invalidMessage,
}) {
  const allowedStatementIds = new Set(frameworkGrammar.getAllowedStatementIdsForSection(sectionId));
  const statements = collectLogicalStatements(block.entries);
  let validCount = 0;
  const parsedStatements = [];

  for (const statement of statements) {
    const firstRow = statement.rows[0];
    const firstTrimmed = String(firstRow?.trimmed || "");
    const firstLineText = String(firstRow?.text || "");
    const statementKind = frameworkGrammar.detectStatementKind(firstTrimmed);
    const normalizedStatement = frameworkGrammar.normalizeStatementLines(
      statement.rows.map((row) => row.text)
    );

    if (firstTrimmed.startsWith("-") || firstTrimmed.startsWith("*")) {
      issues.push(
        createIssue({
          file,
          line: firstRow.line,
          column: markerColumn(firstLineText),
          code: "FWL004",
          message: "keyword-first grammar 不使用列表符，请直接写语句（如 `base ... := ...`）。",
        })
      );
      continue;
    }

    if (!statementKind || !allowedStatementIds.has(statementKind)) {
      issues.push(
        createIssue({
          file,
          line: firstRow.line,
          column: markerColumn(firstLineText),
          code: invalidCode,
          message: invalidMessage,
        })
      );
      continue;
    }
    if (!frameworkGrammar.validateStatement(statementKind, normalizedStatement)) {
      issues.push(
        createIssue({
          file,
          line: firstRow.line,
          column: markerColumn(firstLineText),
          code: invalidCode,
          message: invalidMessage,
        })
      );
      continue;
    }

    validCount += 1;
    parsedStatements.push({
      kind: statementKind,
      line: firstRow.line,
      text: firstLineText,
      normalized: normalizedStatement,
    });
  }

  if (validCount === 0) {
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

  return parsedStatements;
}

function extractBoundarySubsections({ block, file, issues }) {
  const inputBlock = {
    title: FRAMEWORK_SECTION_HEADINGS.boundaryInput,
    line: block.line,
    entries: [],
  };
  const outputBlock = {
    title: FRAMEWORK_SECTION_HEADINGS.boundaryOutput,
    line: block.line,
    entries: [],
  };
  const parameterBlock = {
    title: FRAMEWORK_SECTION_HEADINGS.boundaryParameter,
    line: block.line,
    entries: [],
  };

  let activeSubsection = "";
  const seenHeadings = new Set();

  for (const row of block.entries) {
    if (!row.trimmed) {
      if (activeSubsection === "input") {
        inputBlock.entries.push(row);
      } else if (activeSubsection === "output") {
        outputBlock.entries.push(row);
      } else if (activeSubsection === "parameter") {
        parameterBlock.entries.push(row);
      }
      continue;
    }
    if (row.trimmed.startsWith("### ")) {
      const subId = frameworkGrammar.detectFrameworkSectionIdFromHeading(row.trimmed);
      if (subId === "boundary-input") {
        activeSubsection = "input";
        inputBlock.line = row.line;
        seenHeadings.add(FRAMEWORK_SECTION_HEADINGS.boundaryInput);
        continue;
      }
      if (subId === "boundary-output") {
        activeSubsection = "output";
        outputBlock.line = row.line;
        seenHeadings.add(FRAMEWORK_SECTION_HEADINGS.boundaryOutput);
        continue;
      }
      if (subId === "boundary-parameter") {
        activeSubsection = "parameter";
        parameterBlock.line = row.line;
        seenHeadings.add(FRAMEWORK_SECTION_HEADINGS.boundaryParameter);
        continue;
      }
      issues.push(
        createIssue({
          file,
          line: row.line,
          column: headingColumn(row.text),
          code: "FWL006",
          message: `边界子章节标题错误：必须使用“${FRAMEWORK_SECTION_HEADINGS.boundaryInput} / ${FRAMEWORK_SECTION_HEADINGS.boundaryOutput} / ${FRAMEWORK_SECTION_HEADINGS.boundaryParameter}”。`,
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
          message: "边界定义中的内容必须位于 Input / Output / Parameter 子章节内。",
        })
      );
      continue;
    }

    if (activeSubsection === "input") {
      inputBlock.entries.push(row);
      continue;
    }
    if (activeSubsection === "output") {
      outputBlock.entries.push(row);
      continue;
    }
    parameterBlock.entries.push(row);
  }

  for (const heading of FRAMEWORK_REQUIRED_BOUNDARY_SECTIONS) {
    if (seenHeadings.has(heading)) {
      continue;
    }
    issues.push(
      createIssue({
        file,
        line: block.line,
        column: 1,
        code: "FWL006",
        message: `缺少必需子章节：${heading}`,
      })
    );
  }

  return {
    inputBlock: seenHeadings.has(FRAMEWORK_SECTION_HEADINGS.boundaryInput) ? inputBlock : null,
    outputBlock: seenHeadings.has(FRAMEWORK_SECTION_HEADINGS.boundaryOutput) ? outputBlock : null,
    parameterBlock: seenHeadings.has(FRAMEWORK_SECTION_HEADINGS.boundaryParameter) ? parameterBlock : null,
  };
}

function collectDefinitionSymbols(parsedSections) {
  const symbols = {
    base: new Set(),
    cs: new Set(),
    cp: {
      "cp.form": new Set(),
      "cp.sat": new Set(),
      "cp.id": new Set(),
      "cp.norm": new Set(),
    },
    bd: {
      "bd.in": new Set(),
      "bd.out": new Set(),
      "bd.param": new Set(),
    },
  };

  const visit = (statement) => {
    const definition = frameworkGrammar.getStatementDefinitionById(statement.kind);
    if (!definition) {
      return;
    }
    const match = definition.pattern.exec(statement.normalized);
    if (!match?.groups) {
      return;
    }
    const name = String(match.groups.name || "").trim();
    if (!name) {
      return;
    }
    if (statement.kind === "base") {
      symbols.base.add(name);
      return;
    }
    if (statement.kind === "cs") {
      symbols.cs.add(name);
      return;
    }
    if (statement.kind.startsWith("cp.")) {
      symbols.cp[statement.kind].add(name);
      return;
    }
    if (statement.kind.startsWith("bd.")) {
      symbols.bd[statement.kind].add(name);
    }
  };

  for (const sectionStatements of Object.values(parsedSections || {})) {
    for (const statement of sectionStatements || []) {
      visit(statement);
    }
  }
  return symbols;
}

function unresolvedSymbolIssue({ file, statement, token, message }) {
  const text = String(statement?.text || "");
  const tokenIndex = text.indexOf(token);
  return createIssue({
    file,
    line: statement.line,
    column: tokenIndex >= 0 ? tokenIndex + 1 : markerColumn(text),
    code: "FWL011",
    message,
  });
}

function lintSymbolReferences({ file, issues, parsedSections }) {
  const symbols = collectDefinitionSymbols(parsedSections);
  const allStatements = [];
  for (const sectionStatements of Object.values(parsedSections || {})) {
    allStatements.push(...sectionStatements);
  }

  for (const statement of allStatements) {
    let expression = statement.normalized;
    if (statement.kind === "cs") {
      expression = expression.replace(/^cs\.[^\s:=]+\s*:=\s*/u, "");
    }

    for (const match of expression.matchAll(SYMBOL_REFERENCE_PATTERN)) {
      const kind = String(match.groups?.kind || "").trim();
      const name = String(match.groups?.name || "").trim();
      const token = String(match[0] || "").trim();
      if (!kind || !name || !token) {
        continue;
      }

      if (kind === "base" && symbols.base.has(name)) {
        continue;
      }
      if (kind === "cs" && symbols.cs.has(name)) {
        continue;
      }
      if (kind.startsWith("cp.") && symbols.cp[kind]?.has(name)) {
        continue;
      }
      if (kind.startsWith("bd.") && symbols.bd[kind]?.has(name)) {
        continue;
      }

      issues.push(
        unresolvedSymbolIssue({
          file,
          statement,
          token,
          message: `语句引用了未定义符号 \`${token}\`。`,
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
    if (/上游模块[：:]/u.test(trimmed)) {
      issues.push(
        createIssue({
          file,
          line: index + 1,
          column: markerColumn(text),
          code: "FWL015",
          message: "禁止使用“上游模块：...”，请直接使用 grammar 里的符号引用。",
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
  const lines = frameworkGrammar.splitLines(text);
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
    if (directive.text !== FRAMEWORK_DIRECTIVE) {
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
  validateTopSectionHeadingSequence({
    lines,
    file,
    issues,
    sectionBlocks,
  });

  const goalSection = findSectionBlock(sectionBlocks, FRAMEWORK_SECTION_HEADINGS.goal);
  const baseSection = findSectionBlock(sectionBlocks, FRAMEWORK_SECTION_HEADINGS.base);
  const combinationPrinciplesSection = findSectionBlock(
    sectionBlocks,
    FRAMEWORK_SECTION_HEADINGS.combinationPrinciples
  );
  const combinationSpaceSection = findSectionBlock(
    sectionBlocks,
    FRAMEWORK_SECTION_HEADINGS.combinationSpace
  );
  const boundarySection = findSectionBlock(sectionBlocks, FRAMEWORK_SECTION_HEADINGS.boundary);

  const parsedSections = {
    goal: [],
    base: [],
    "combination-principles": [],
    "combination-space": [],
    "boundary-input": [],
    "boundary-output": [],
    "boundary-parameter": [],
  };

  if (goalSection) {
    parsedSections.goal = lintSectionStatements({
      file,
      issues,
      block: goalSection,
      sectionId: "goal",
      invalidCode: "FWL005",
      invalidMessage: "Goal 章节格式错误，必须匹配 `goal <Name> := ...`。",
    });
  }
  if (baseSection) {
    parsedSections.base = lintSectionStatements({
      file,
      issues,
      block: baseSection,
      sectionId: "base",
      invalidCode: "FWL007",
      invalidMessage: "Base 章节格式错误，必须匹配 `base <Name> := ...`。",
    });
  }
  if (combinationPrinciplesSection) {
    parsedSections["combination-principles"] = lintSectionStatements({
      file,
      issues,
      block: combinationPrinciplesSection,
      sectionId: "combination-principles",
      invalidCode: "FWL008",
      invalidMessage: "Combination Principles 章节格式错误，必须匹配 `cp.form/sat/id/norm ... on ... := ...`。",
    });
  }
  if (combinationSpaceSection) {
    parsedSections["combination-space"] = lintSectionStatements({
      file,
      issues,
      block: combinationSpaceSection,
      sectionId: "combination-space",
      invalidCode: "FWL008",
      invalidMessage: "Combination Space 章节格式错误，必须匹配 `cs.<Name> := ... by ...`。",
    });
  }

  if (boundarySection) {
    const boundarySubsections = extractBoundarySubsections({
      block: boundarySection,
      file,
      issues,
    });
    if (boundarySubsections.inputBlock) {
      parsedSections["boundary-input"] = lintSectionStatements({
        file,
        issues,
        block: boundarySubsections.inputBlock,
        sectionId: "boundary-input",
        invalidCode: "FWL006",
        invalidMessage: "Input 章节格式错误，必须匹配 `bd.in <Name> := ...`。",
      });
    }
    if (boundarySubsections.outputBlock) {
      parsedSections["boundary-output"] = lintSectionStatements({
        file,
        issues,
        block: boundarySubsections.outputBlock,
        sectionId: "boundary-output",
        invalidCode: "FWL006",
        invalidMessage: "Output 章节格式错误，必须匹配 `bd.out <Name> := ...`。",
      });
    }
    if (boundarySubsections.parameterBlock) {
      parsedSections["boundary-parameter"] = lintSectionStatements({
        file,
        issues,
        block: boundarySubsections.parameterBlock,
        sectionId: "boundary-parameter",
        invalidCode: "FWL006",
        invalidMessage: "Parameter 章节格式错误，必须匹配 `bd.param <Name> := ...`。",
      });
    }
  }

  lintSymbolReferences({
    file,
    issues,
    parsedSections,
  });

  lintForbiddenLegacyPatterns({
    lines,
    file,
    issues,
  });

  return issues;
}

function trimMarkdownLinkTarget(rawTarget) {
  let target = String(rawTarget || "").trim();
  if (target.startsWith("<") && target.endsWith(">")) {
    target = target.slice(1, -1).trim();
  }
  const titleMatch = /^(?<path>.+?)\s+["'][^"']*["']$/u.exec(target);
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

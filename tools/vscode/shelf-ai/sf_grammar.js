const SF_LANGUAGE_ID = "shelf-framework";
const SF_FILE_EXTENSION = ".sf";

const SF_MODULE_DECL_PATTERN = /^MODULE\s+(?<cn>[^:]+):(?<en>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*$/u;
const SF_GOAL_PATTERN = /^Goal\s*:=\s*"(?<body>.+)"$/u;

const SF_BLOCK_DEFINITIONS = Object.freeze([
  { id: "goal", label: "Goal", heading: "Goal" },
  { id: "base", label: "Base", heading: "Base:" },
  { id: "principles", label: "Principles", heading: "Principles:" },
  { id: "spaces", label: "Spaces", heading: "Spaces:" },
  { id: "boundary", label: "Boundary", heading: "Boundary:" },
]);

const SF_STATEMENT_DEFINITIONS = Object.freeze([
  {
    id: "set",
    sectionId: "base",
    keyword: "set",
    pattern: /^set\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "set ${1:集合基} := \"${2:集合说明}\"",
    completionLabel: "set",
    completionDetail: "插入 Base.set 声明",
  },
  {
    id: "elem",
    sectionId: "base",
    keyword: "elem",
    pattern: /^elem\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "elem ${1:结构基} := \"${2:结构说明}\"",
    completionLabel: "elem",
    completionDetail: "插入 Base.elem 声明",
  },
  {
    id: "relation",
    sectionId: "base",
    keyword: "relation",
    pattern: /^relation(?:\[(?<shape>[^\]]+)\])?\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "relation[2:1] ${1:关系基} := \"${2:关系说明}\"",
    completionLabel: "relation[2:1]",
    completionDetail: "插入 Base.relation 声明",
  },
  {
    id: "sat",
    sectionId: "principles",
    keyword: "sat",
    pattern: /^sat\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "sat ${1:成立原则} := \"${2:说明成立条件}\"",
    completionLabel: "sat",
    completionDetail: "插入 Principles.sat 声明",
  },
  {
    id: "eq",
    sectionId: "principles",
    keyword: "eq",
    pattern: /^eq\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "eq ${1:判同原则} := \"${2:说明何时归入同一结果类}\"",
    completionLabel: "eq",
    completionDetail: "插入 Principles.eq 声明",
  },
  {
    id: "comb",
    sectionId: "spaces",
    keyword: "comb",
    pattern: /^comb\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "comb ${1:组合分类} := \"${2:说明这一类组合如何得到}\"",
    completionLabel: "comb",
    completionDetail: "插入 Spaces.comb 声明",
  },
  {
    id: "seq",
    sectionId: "spaces",
    keyword: "seq",
    pattern: /^seq\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "seq ${1:候选序列} := \"${2:说明这一组候选}\"",
    completionLabel: "seq",
    completionDetail: "插入 Spaces.seq 声明",
  },
  {
    id: "in",
    sectionId: "boundary",
    keyword: "in",
    subtypeRequired: true,
    pattern: /^in<(?<subtype>[^>]+)>\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "in<view> ${1:输入边界} := \"${2:输入约束}\"",
    completionLabel: "in<schema>",
    completionDetail: "插入 Boundary.in 声明",
  },
  {
    id: "out",
    sectionId: "boundary",
    keyword: "out",
    subtypeRequired: true,
    pattern: /^out<(?<subtype>[^>]+)>\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "out<view> ${1:输出边界} := \"${2:输出约束}\"",
    completionLabel: "out<schema>",
    completionDetail: "插入 Boundary.out 声明",
  },
  {
    id: "param-enum",
    sectionId: "boundary",
    keyword: "param",
    subtypeRequired: true,
    pattern: /^param<enum>\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "param<enum> ${1:参数边界} := \"${2:{a, b}}\"",
    completionLabel: "param<enum>",
    completionDetail: "插入 Boundary.param 声明",
  },
  {
    id: "param-range",
    sectionId: "boundary",
    keyword: "param",
    subtypeRequired: true,
    pattern: /^param<range>\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "param<range> ${1:范围边界} := \"${2:[0:2]}\"",
    completionLabel: "param<range>",
    completionDetail: "插入 Boundary.param 范围声明",
  },
]);

const SF_TOP_LEVEL_TEMPLATES = Object.freeze([
  {
    id: "module",
    label: "MODULE 中文模块名:EnglishName:",
    detail: "插入模块声明",
    documentation: "独立 .sf 文件以 MODULE 声明起始。",
    insertText: "MODULE ${1:中文模块名}:${2:EnglishName}:",
  },
  {
    id: "goal",
    label: "Goal := \"...\"",
    detail: "插入 Goal 声明",
    documentation: "Goal 是模块级单例声明。",
    insertText: "Goal := \"${1:模块目标}\"",
  },
  {
    id: "base-block",
    label: "Base:",
    detail: "插入 Base block",
    documentation: "Base block 定义最小结构基。",
    insertText: "Base:",
  },
  {
    id: "principles-block",
    label: "Principles:",
    detail: "插入 Principles block",
    documentation: "Principles block 定义组合原则。",
    insertText: "Principles:",
  },
  {
    id: "spaces-block",
    label: "Spaces:",
    detail: "插入 Spaces block",
    documentation: "Spaces block 定义结果组合空间。",
    insertText: "Spaces:",
  },
  {
    id: "boundary-block",
    label: "Boundary:",
    detail: "插入 Boundary block",
    documentation: "Boundary block 定义输入、输出和参数边界。",
    insertText: "Boundary:",
  },
]);

const SF_TEMPLATE_SNIPPET_BODY = Object.freeze([
  "MODULE ${1:中文模块名}:${2:EnglishName}:",
  "    Goal := \"${3:模块目标}\"",
  "",
  "    Base:",
  "        set ${4:集合基} := \"${5:集合说明}\"",
  "        elem ${6:结构基} := \"${7:结构说明}\"",
  "        relation[2:1] ${8:关系基} := \"${9:关系说明}\"",
  "",
  "    Principles:",
  "        sat ${10:成立原则} := \"${11:说明成立条件}\"",
  "        eq ${12:判同原则} := \"${13:说明何时归入同一结果类}\"",
  "",
  "    Spaces:",
  "        comb ${14:组合分类} := \"${15:说明这一类组合如何得到}\"",
  "",
  "    Boundary:",
  "        param<enum> ${16:变量边界} := \"${17:{x, y, z}}\"",
  "        param<enum> ${18:变量取值边界} := \"${19:{0, 1}}\"",
  "        param<range> ${20:最大嵌套层数} := \"${21:[0:2]}\"",
]);

const SF_REFERENCE_PATTERN = /\b(?:Base|Principles|Spaces|Boundary)\.[^,\s，。；;:：<>(){}[\]"']+/gu;
const SF_CLAUSE_PATTERN = /$^/gu;
const SF_DECLARATION_HEAD_PATTERN = /^(?<keyword>set|elem|relation|sat|eq|comb|seq|in|out|param)(?<subtype>(?:\[[^\]]+\]|<[^>]+>))?\s/u;

const SEMANTIC_TOKEN_TYPES = Object.freeze({
  block: "type",
  statementKeyword: "keyword",
  reference: "namespace",
  clauseKeyword: "keyword",
  subtype: "type",
});

function splitLines(text) {
  return String(text || "").split(/\r?\n/u);
}

function isShelfFrameworkFilePath(filePath) {
  return String(filePath || "").toLowerCase().endsWith(SF_FILE_EXTENSION);
}

function getIndent(lineText) {
  const match = String(lineText || "").match(/^ */u);
  return match ? match[0].length : 0;
}

function trimLine(lineText) {
  return String(lineText || "").trim();
}

function detectShelfFrameworkSectionId(lineText) {
  const trimmed = trimLine(lineText);
  if (trimmed === "Base:") {
    return "base";
  }
  if (trimmed === "Principles:") {
    return "principles";
  }
  if (trimmed === "Spaces:") {
    return "spaces";
  }
  if (trimmed === "Boundary:") {
    return "boundary";
  }
  return "";
}

function detectShelfFrameworkAuthoringSection(documentText, lineNumber = 0) {
  const lines = splitLines(documentText);
  const safeLineNumber = Math.max(0, Math.min(Number(lineNumber || 0), Math.max(lines.length - 1, 0)));
  let sectionId = "";
  let hasModule = false;

  for (let index = 0; index <= safeLineNumber; index += 1) {
    const trimmed = trimLine(lines[index]);
    if (SF_MODULE_DECL_PATTERN.test(trimmed)) {
      hasModule = true;
      continue;
    }
    const detected = detectShelfFrameworkSectionId(trimmed);
    if (detected) {
      sectionId = detected;
    }
  }

  return {
    hasModule,
    sectionId,
    lineCount: lines.length,
  };
}

function getStatementDefinitionsForSection(sectionId) {
  const safeSectionId = String(sectionId || "").trim();
  return SF_STATEMENT_DEFINITIONS.filter((item) => item.sectionId === safeSectionId);
}

function collectShelfFrameworkSemanticTokens(text) {
  const tokens = [];
  const lines = splitLines(text);

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
    const line = String(lines[lineIndex] || "");
    const trimmed = trimLine(line);
    const indent = getIndent(line);

    if (lineIndex === 0 && SF_MODULE_DECL_PATTERN.test(trimmed)) {
      tokens.push({
        line: lineIndex,
        startChar: 0,
        length: "MODULE".length,
        tokenType: SEMANTIC_TOKEN_TYPES.statementKeyword,
      });
    }

    if (indent === 4) {
      if (trimmed.startsWith("Goal")) {
        tokens.push({
          line: lineIndex,
          startChar: indent,
          length: "Goal".length,
          tokenType: SEMANTIC_TOKEN_TYPES.block,
        });
      } else if (detectShelfFrameworkSectionId(trimmed)) {
        tokens.push({
          line: lineIndex,
          startChar: indent,
          length: trimmed.length,
          tokenType: SEMANTIC_TOKEN_TYPES.block,
        });
      }
    }

    if (indent === 8) {
      const headMatch = trimmed.match(SF_DECLARATION_HEAD_PATTERN);
      if (headMatch?.groups?.keyword) {
        tokens.push({
          line: lineIndex,
          startChar: indent,
          length: headMatch.groups.keyword.length,
          tokenType: SEMANTIC_TOKEN_TYPES.statementKeyword,
        });
        if (headMatch.groups.subtype) {
          tokens.push({
            line: lineIndex,
            startChar: indent + headMatch.groups.keyword.length,
            length: headMatch.groups.subtype.length,
            tokenType: SEMANTIC_TOKEN_TYPES.subtype,
          });
        }
      }
    }

    for (const match of trimmed.matchAll(SF_REFERENCE_PATTERN)) {
      if (!match[0]) {
        continue;
      }
      tokens.push({
        line: lineIndex,
        startChar: indent + Number(match.index || 0),
        length: match[0].length,
        tokenType: SEMANTIC_TOKEN_TYPES.reference,
      });
    }

    for (const match of trimmed.matchAll(SF_CLAUSE_PATTERN)) {
      if (!match[0]) {
        continue;
      }
      tokens.push({
        line: lineIndex,
        startChar: indent + Number(match.index || 0),
        length: match[0].length,
        tokenType: SEMANTIC_TOKEN_TYPES.clauseKeyword,
      });
    }
  }

  return tokens;
}

function getShelfFrameworkCompletionTriggerChars() {
  return ["M", "G", "B", "P", "S", "e", "r", "s", "q", "c", "i", "o", "p", "<", "[", ":", ".", " "];
}

module.exports = {
  SEMANTIC_TOKEN_TYPES,
  SF_BLOCK_DEFINITIONS,
  SF_FILE_EXTENSION,
  SF_GOAL_PATTERN,
  SF_LANGUAGE_ID,
  SF_MODULE_DECL_PATTERN,
  SF_REFERENCE_PATTERN,
  SF_STATEMENT_DEFINITIONS,
  SF_TEMPLATE_SNIPPET_BODY,
  SF_TOP_LEVEL_TEMPLATES,
  collectShelfFrameworkSemanticTokens,
  detectShelfFrameworkAuthoringSection,
  detectShelfFrameworkSectionId,
  getIndent,
  getShelfFrameworkCompletionTriggerChars,
  getStatementDefinitionsForSection,
  isShelfFrameworkFilePath,
  splitLines,
  trimLine,
};

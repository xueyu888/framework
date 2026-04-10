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
    id: "struct",
    sectionId: "base",
    keyword: "struct",
    pattern: /^struct\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "struct ${1:复合结构} := \"${2:结构说明}\"",
    completionLabel: "struct",
    completionDetail: "插入 Base.struct 声明",
  },
  {
    id: "seq-base",
    sectionId: "base",
    keyword: "seq",
    pattern: /^seq\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "seq ${1:有序结构基} := \"${2:有序结构说明}\"",
    completionLabel: "seq",
    completionDetail: "插入 Base.seq 声明",
  },
  {
    id: "op-base",
    sectionId: "base",
    keyword: "op",
    annotationKind: "shape",
    pattern: /^op(?:\[(?<shape>[^\]]+)\])?\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "op[2:1] ${1:操作子} := \"${2:操作子说明}\"",
    completionLabel: "op[2:1]",
    completionDetail: "插入 Base.op 声明",
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
    id: "set-spaces",
    sectionId: "spaces",
    keyword: "set",
    pattern: /^set\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "set ${1:结果集合} := \"${2:结果集合说明}\"",
    completionLabel: "set",
    completionDetail: "插入 Spaces.set 声明",
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
    annotationKind: "subtype",
    subtypeRequired: true,
    pattern: /^in<(?<subtype>[^>]+)>\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "in<subtype> ${1:输入边界} := \"${2:输入约束}\"",
    completionLabel: "in<subtype>",
    completionDetail: "插入 Boundary.in 声明",
  },
  {
    id: "out",
    sectionId: "boundary",
    keyword: "out",
    annotationKind: "subtype",
    subtypeRequired: true,
    pattern: /^out<(?<subtype>[^>]+)>\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "out<subtype> ${1:输出边界} := \"${2:输出约束}\"",
    completionLabel: "out<subtype>",
    completionDetail: "插入 Boundary.out 声明",
  },
  {
    id: "param-enum",
    sectionId: "boundary",
    keyword: "param",
    annotationKind: "subtype",
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
    annotationKind: "subtype",
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
  "        struct ${8:复合结构} := \"${9:结构说明}\"",
  "        seq ${10:有序结构基} := \"${11:有序结构说明}\"",
  "        op[2:1] ${12:操作子} := \"${13:操作子说明}\"",
  "",
  "    Principles:",
  "        sat ${14:成立原则} := \"${15:说明成立条件}\"",
  "        eq ${16:判同原则} := \"${17:说明何时归入同一结果类}\"",
  "",
  "    Spaces:",
  "        set ${18:结果集合} := \"${19:结果集合说明}\"",
  "        comb ${20:组合分类} := \"${21:说明这一类组合如何得到}\"",
  "        seq ${22:候选序列} := \"${23:说明这一组候选}\"",
  "",
  "    Boundary:",
  "        in<subtype> ${24:输入边界} := \"${25:输入约束}\"",
  "        out<subtype> ${26:输出边界} := \"${27:输出约束}\"",
  "        param<enum> ${28:变量边界} := \"${29:{x, y, z}}\"",
  "        param<range> ${30:最大嵌套层数} := \"${31:[0:2]}\"",
]);

const SF_REFERENCE_PATTERN = /\b(?:Base|Principles|Spaces|Boundary)\.[^,\s，。；;:：<>(){}[\]"']+/gu;
const SF_CLAUSE_PATTERN = /$^/gu;
const SF_DECLARATION_HEAD_PATTERN = /^(?<keyword>set|elem|struct|seq|op|sat|eq|comb|in|out|param)(?<annotation>(?:\[(?<shape>[^\]]+)\]|<(?<subtype>[^>]+)>))?(?<gap>\s+)(?<name>[^:=]+?)\s*:=\s/u;

const SEMANTIC_TOKEN_TYPES = Object.freeze({
  block: "type",
  statementKeyword: "keyword",
  reference: "namespace",
  clauseKeyword: "keyword",
  declarationName: "variable",
  shape: "operator",
  subtype: "typeParameter",
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
        const annotation = String(headMatch.groups.annotation || "");
        const gap = String(headMatch.groups.gap || "");
        const name = String(headMatch.groups.name || "");
        tokens.push({
          line: lineIndex,
          startChar: indent,
          length: headMatch.groups.keyword.length,
          tokenType: SEMANTIC_TOKEN_TYPES.statementKeyword,
        });
        if (annotation) {
          tokens.push({
            line: lineIndex,
            startChar: indent + headMatch.groups.keyword.length,
            length: annotation.length,
            tokenType: headMatch.groups.shape
              ? SEMANTIC_TOKEN_TYPES.shape
              : SEMANTIC_TOKEN_TYPES.subtype,
          });
        }
        if (name) {
          tokens.push({
            line: lineIndex,
            startChar: indent + headMatch.groups.keyword.length + annotation.length + gap.length,
            length: name.length,
            tokenType: SEMANTIC_TOKEN_TYPES.declarationName,
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

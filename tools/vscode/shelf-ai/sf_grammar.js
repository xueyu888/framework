const SF_LANGUAGE_ID = "shelf-framework";
const SF_FILE_EXTENSION = ".sf";

const SF_MODULE_DECL_PATTERN = /^module\s+(?<cn>[^:]+):(?<en>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*$/u;
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
    id: "elem",
    sectionId: "base",
    keyword: "elem",
    pattern: /^elem\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "elem ${1:结构基} := ${2:[说明](../path.md)}",
    completionLabel: "elem",
    completionDetail: "插入 Base.elem 声明",
  },
  {
    id: "rel",
    sectionId: "base",
    keyword: "rel",
    pattern: /^rel\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "rel ${1:关系基} := ${2:关系说明}",
    completionLabel: "rel",
    completionDetail: "插入 Base.rel 声明",
  },
  {
    id: "attr",
    sectionId: "base",
    keyword: "attr",
    pattern: /^attr\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "attr ${1:属性基} := ${2:属性说明}",
    completionLabel: "attr",
    completionDetail: "插入 Base.attr 声明",
  },
  {
    id: "form",
    sectionId: "principles",
    keyword: "form",
    clauseOrder: Object.freeze(["on", "body"]),
    template: [
      "form ${1:形成原则} :=",
      "    on(<${2:Base.结构基}>),",
      "    body(\"${3:说明组合如何形成}\")",
    ].join("\n"),
    completionLabel: "form",
    completionDetail: "插入 Principles.form 声明",
  },
  {
    id: "sat",
    sectionId: "principles",
    keyword: "sat",
    clauseOrder: Object.freeze(["on", "body"]),
    template: [
      "sat ${1:成立原则} :=",
      "    on(<${2:Spaces.comb.结果空间}>),",
      "    body(\"${3:说明满足条件}\")",
    ].join("\n"),
    completionLabel: "sat",
    completionDetail: "插入 Principles.sat 声明",
  },
  {
    id: "id",
    sectionId: "principles",
    keyword: "id",
    clauseOrder: Object.freeze(["on", "body"]),
    template: [
      "id ${1:判同原则} :=",
      "    on(<${2:Spaces.comb.结果空间}>),",
      "    body(\"${3:说明什么算同一个}\")",
    ].join("\n"),
    completionLabel: "id",
    completionDetail: "插入 Principles.id 声明",
  },
  {
    id: "norm",
    sectionId: "principles",
    keyword: "norm",
    clauseOrder: Object.freeze(["on", "body"]),
    template: [
      "norm ${1:规范化原则} :=",
      "    on(<${2:Spaces.comb.结果空间}>),",
      "    body(\"${3:说明标准写法}\")",
    ].join("\n"),
    completionLabel: "norm",
    completionDetail: "插入 Principles.norm 声明",
  },
  {
    id: "comb",
    sectionId: "spaces",
    keyword: "comb",
    clauseOrder: Object.freeze(["from", "by"]),
    template: [
      "comb ${1:结果组合} :=",
      "    from(<${2:Base.结构基}>),",
      "    by(<${3:Principles.form.形成原则}>)",
    ].join("\n"),
    completionLabel: "comb",
    completionDetail: "插入 Spaces.comb 声明",
  },
  {
    id: "seq",
    sectionId: "spaces",
    keyword: "seq",
    clauseOrder: Object.freeze(["from", "by"]),
    template: [
      "seq ${1:有序结果} :=",
      "    from(<${2:Base.结构基}>),",
      "    by(<${3:Principles.form.形成原则}>)",
    ].join("\n"),
    completionLabel: "seq",
    completionDetail: "插入 Spaces.seq 声明",
  },
  {
    id: "in",
    sectionId: "boundary",
    keyword: "in",
    subtypeRequired: true,
    clauseOrder: Object.freeze(["payload", "card", "to"]),
    template: [
      "in<schema> ${1:输入边界} :=",
      "    payload(${2:{...}}),",
      "    card(${3:1}),",
      "    to(${4:Spaces.comb.结果组合})",
    ].join("\n"),
    completionLabel: "in<schema>",
    completionDetail: "插入 Boundary.in 声明",
  },
  {
    id: "out",
    sectionId: "boundary",
    keyword: "out",
    subtypeRequired: true,
    clauseOrder: Object.freeze(["payload", "card", "from"]),
    template: [
      "out<schema> ${1:输出边界} :=",
      "    payload(${2:{...}}),",
      "    card(${3:1}),",
      "    from(${4:Spaces.comb.结果组合})",
    ].join("\n"),
    completionLabel: "out<schema>",
    completionDetail: "插入 Boundary.out 声明",
  },
  {
    id: "param",
    sectionId: "boundary",
    keyword: "param",
    subtypeRequired: true,
    clauseOrder: Object.freeze(["domain", "affects"]),
    template: [
      "param<enum> ${1:参数边界} :=",
      "    domain(${2:{a, b}}),",
      "    affects(<${3:Boundary.in.输入边界, Spaces.comb.结果组合}>)",
    ].join("\n"),
    completionLabel: "param<enum>",
    completionDetail: "插入 Boundary.param 声明",
  },
]);

const SF_TOP_LEVEL_TEMPLATES = Object.freeze([
  {
    id: "module",
    label: "module 中文模块名:EnglishName:",
    detail: "插入模块声明",
    documentation: "独立 .sf 文件以 module 声明起始。",
    insertText: "module ${1:中文模块名}:${2:EnglishName}:",
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
  "module ${1:中文模块名}:${2:EnglishName}:",
  "    Goal := \"${3:模块目标}\"",
  "",
  "    Base:",
  "        elem ${4:结构基} := ${5:[说明](../path.md)}",
  "",
  "    Principles:",
  "        form ${6:形成原则} :=",
  "            on(<${7:Base.结构基}>),",
  "            body(\"${8:说明组合如何形成}\")",
  "",
  "    Spaces:",
  "        comb ${9:结果组合} :=",
  "            from(<${10:Base.结构基}>),",
  "            by(<${11:Principles.form.形成原则}>)",
  "",
  "    Boundary:",
  "        in<schema> ${12:输入边界} :=",
  "            payload(${13:{...}}),",
  "            card(${14:1}),",
  "            to(${15:Spaces.comb.结果组合})",
  "",
  "        out<schema> ${16:输出边界} :=",
  "            payload(${17:{...}}),",
  "            card(${18:1}),",
  "            from(${19:Spaces.comb.结果组合})",
  "",
  "        param<enum> ${20:参数边界} :=",
  "            domain(${21:{a, b}}),",
  "            affects(<${22:Boundary.in.输入边界, Spaces.comb.结果组合}>)",
]);

const SF_REFERENCE_PATTERN = /\b(?:Base|Principles\.(?:form|sat|id|norm)|Spaces\.(?:comb|seq)|Boundary\.(?:in|out|param))\.[^,\s<>(){}[\]]+/gu;
const SF_CLAUSE_PATTERN = /\b(?:on|body|from|by|payload|card|to|from|domain|affects)\b/gu;
const SF_DECLARATION_HEAD_PATTERN = /^(?<keyword>elem|rel|attr|form|sat|id|norm|comb|seq|in|out|param)(?<subtype><(?:schema|range|enum)>)?\s/u;

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
        length: "module".length,
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
  return ["m", "G", "B", "P", "S", "i", "o", "p", "<", ":", ".", " "];
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

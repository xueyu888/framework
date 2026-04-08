const FRAMEWORK_TITLE_PATTERN = /^#\s+(?<cn>[^:]+):(?<en>.+)$/u;
const FRAMEWORK_DIRECTIVE = "@framework";

const FRAMEWORK_SECTION_HEADINGS = Object.freeze({
  goal: "## Goal",
  base: "## Base",
  combinationPrinciples: "## Combination Principles",
  combinationSpace: "## Combination Space",
  boundary: "## Boundary",
  boundaryInput: "### Input",
  boundaryOutput: "### Output",
  boundaryParameter: "### Parameter",
});

const FRAMEWORK_REQUIRED_TOP_LEVEL_SECTIONS = Object.freeze([
  FRAMEWORK_SECTION_HEADINGS.goal,
  FRAMEWORK_SECTION_HEADINGS.base,
  FRAMEWORK_SECTION_HEADINGS.combinationPrinciples,
  FRAMEWORK_SECTION_HEADINGS.combinationSpace,
  FRAMEWORK_SECTION_HEADINGS.boundary,
]);

const FRAMEWORK_REQUIRED_BOUNDARY_SECTIONS = Object.freeze([
  FRAMEWORK_SECTION_HEADINGS.boundaryInput,
  FRAMEWORK_SECTION_HEADINGS.boundaryOutput,
  FRAMEWORK_SECTION_HEADINGS.boundaryParameter,
]);

const FRAMEWORK_STATEMENT_DEFINITIONS = Object.freeze([
  {
    id: "goal",
    sectionId: "goal",
    keyword: "goal",
    pattern: /^goal\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "goal ${1:GoalName} := ${2:本模块目标说明}",
    completionLabel: "goal",
    completionDetail: "插入 Goal 语句",
  },
  {
    id: "base",
    sectionId: "base",
    keyword: "base",
    pattern: /^base\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "base ${1:BaseName} := ${2:一句定义或 Lx.My::Base.Name}",
    completionLabel: "base",
    completionDetail: "插入 Base 语句",
  },
  {
    id: "cp.form",
    sectionId: "combination-principles",
    keyword: "cp.form",
    pattern: /^cp\.form\s+(?<name>[^:=]+?)\s+on\s+(?<target>.+?)\s*:=\s*(?<body>.+)$/u,
    template: "cp.form ${1:PrincipleName} on ${2:base.Name / cs.Name / form} := ${3:什么能组成什么}",
    completionLabel: "cp.form",
    completionDetail: "插入组合形成原则",
  },
  {
    id: "cp.sat",
    sectionId: "combination-principles",
    keyword: "cp.sat",
    pattern: /^cp\.sat\s+(?<name>[^:=]+?)\s+on\s+(?<target>.+?)\s*:=\s*(?<body>.+)$/u,
    template: "cp.sat ${1:PrincipleName} on ${2:base.Name / cs.Name / form} := ${3:什么条件下成立}",
    completionLabel: "cp.sat",
    completionDetail: "插入组合成立原则",
  },
  {
    id: "cp.id",
    sectionId: "combination-principles",
    keyword: "cp.id",
    pattern: /^cp\.id\s+(?<name>[^:=]+?)\s+on\s+(?<target>.+?)\s*:=\s*(?<body>.+)$/u,
    template: "cp.id ${1:PrincipleName} on ${2:base.Name / cs.Name / form} := ${3:什么算同一个组合}",
    completionLabel: "cp.id",
    completionDetail: "插入组合同一性原则",
  },
  {
    id: "cp.norm",
    sectionId: "combination-principles",
    keyword: "cp.norm",
    pattern: /^cp\.norm\s+(?<name>[^:=]+?)\s+on\s+(?<target>.+?)\s*:=\s*(?<body>.+)$/u,
    template: "cp.norm ${1:PrincipleName} on ${2:base.Name / cs.Name / form} := ${3:同一个组合的标准写法}",
    completionLabel: "cp.norm",
    completionDetail: "插入组合规范化原则",
  },
  {
    id: "cs",
    sectionId: "combination-space",
    keyword: "cs",
    pattern: /^cs\.(?<name>[^\s:=]+)\s*:=\s*(?<expr>.+?)\s+by\s+(?<principles>.+)$/u,
    template: "cs.${1:CombinationName} := ${2:base.Name / cs.Name / ...} by ${3:cp.form.Name, cp.sat.Name, cp.id.Name, cp.norm.Name}",
    completionLabel: "cs",
    completionDetail: "插入组合空间语句",
  },
  {
    id: "bd.in",
    sectionId: "boundary-input",
    keyword: "bd.in",
    pattern: /^bd\.in\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "bd.in ${1:InputName} := payload(${2:...}), cardinality(${3:...}), to(${4:base.Name / cs.Name})",
    completionLabel: "bd.in",
    completionDetail: "插入输入边界语句",
  },
  {
    id: "bd.out",
    sectionId: "boundary-output",
    keyword: "bd.out",
    pattern: /^bd\.out\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "bd.out ${1:OutputName} := payload(${2:...}), cardinality(${3:...}), from(${4:cs.Name})",
    completionLabel: "bd.out",
    completionDetail: "插入输出边界语句",
  },
  {
    id: "bd.param",
    sectionId: "boundary-parameter",
    keyword: "bd.param",
    pattern: /^bd\.param\s+(?<name>[^:=]+?)\s*:=\s*(?<body>.+)$/u,
    template: "bd.param ${1:ParameterName} := domain(${2:...}), affects(${3:cp.form.Name / cp.sat.Name / cp.id.Name / cp.norm.Name / cs.Name / bd.in.Name / bd.out.Name})",
    completionLabel: "bd.param",
    completionDetail: "插入参数边界语句",
  },
]);

const FRAMEWORK_SECTION_ID_BY_HEADING = Object.freeze({
  [FRAMEWORK_SECTION_HEADINGS.goal]: "goal",
  [FRAMEWORK_SECTION_HEADINGS.base]: "base",
  [FRAMEWORK_SECTION_HEADINGS.combinationPrinciples]: "combination-principles",
  [FRAMEWORK_SECTION_HEADINGS.combinationSpace]: "combination-space",
  [FRAMEWORK_SECTION_HEADINGS.boundary]: "boundary",
  [FRAMEWORK_SECTION_HEADINGS.boundaryInput]: "boundary-input",
  [FRAMEWORK_SECTION_HEADINGS.boundaryOutput]: "boundary-output",
  [FRAMEWORK_SECTION_HEADINGS.boundaryParameter]: "boundary-parameter",
});

const FRAMEWORK_SECTION_COMPLETION_DEFINITIONS = Object.freeze([
  { id: "goal", heading: FRAMEWORK_SECTION_HEADINGS.goal, sectionId: "goal" },
  { id: "base", heading: FRAMEWORK_SECTION_HEADINGS.base, sectionId: "base" },
  {
    id: "combination-principles",
    heading: FRAMEWORK_SECTION_HEADINGS.combinationPrinciples,
    sectionId: "combination-principles",
  },
  {
    id: "combination-space",
    heading: FRAMEWORK_SECTION_HEADINGS.combinationSpace,
    sectionId: "combination-space",
  },
  { id: "boundary", heading: FRAMEWORK_SECTION_HEADINGS.boundary, sectionId: "boundary" },
  {
    id: "boundary-input",
    heading: FRAMEWORK_SECTION_HEADINGS.boundaryInput,
    sectionId: "boundary-input",
  },
  {
    id: "boundary-output",
    heading: FRAMEWORK_SECTION_HEADINGS.boundaryOutput,
    sectionId: "boundary-output",
  },
  {
    id: "boundary-parameter",
    heading: FRAMEWORK_SECTION_HEADINGS.boundaryParameter,
    sectionId: "boundary-parameter",
  },
]);

const FRAMEWORK_TEMPLATE_SNIPPET_BODY = Object.freeze([
  "# ${1:中文模块名}:${2:EnglishName}",
  "",
  "@framework",
  "",
  "## Goal",
  "",
  "goal ${3:GoalName} := ${4:本模块的目标是什么}",
  "",
  "## Base",
  "",
  "base ${5:BaseName} := ${6:一句定义或 Lx.My::Base.Name}",
  "",
  "## Combination Principles",
  "",
  "cp.form ${7:PrincipleName} on ${8:base.Name / cs.Name / form} := ${9:什么能组成什么}",
  "cp.sat ${10:PrincipleName} on ${11:base.Name / cs.Name / form} := ${12:什么条件下成立}",
  "cp.id ${13:PrincipleName} on ${14:base.Name / cs.Name / form} := ${15:什么算同一个组合}",
  "cp.norm ${16:PrincipleName} on ${17:base.Name / cs.Name / form} := ${18:同一个组合的标准写法}",
  "",
  "## Combination Space",
  "",
  "cs.${19:CombinationName} := ${20:base.Name / cs.Name / ...} by ${21:cp.form.Name, cp.sat.Name, cp.id.Name, cp.norm.Name}",
  "",
  "## Boundary",
  "",
  "### Input",
  "",
  "bd.in ${22:InputName} := payload(${23:...}), cardinality(${24:...}), to(${25:base.Name / cs.Name})",
  "",
  "### Output",
  "",
  "bd.out ${26:OutputName} := payload(${27:...}), cardinality(${28:...}), from(${29:cs.Name})",
  "",
  "### Parameter",
  "",
  "bd.param ${30:ParameterName} := domain(${31:...}), affects(${32:cp.form.Name / cp.sat.Name / cp.id.Name / cp.norm.Name / cs.Name / bd.in.Name / bd.out.Name})",
]);

const STATEMENT_KIND_BY_PREFIX = Object.freeze([
  { prefix: "goal ", id: "goal" },
  { prefix: "base ", id: "base" },
  { prefix: "cp.form ", id: "cp.form" },
  { prefix: "cp.sat ", id: "cp.sat" },
  { prefix: "cp.id ", id: "cp.id" },
  { prefix: "cp.norm ", id: "cp.norm" },
  { prefix: "cs.", id: "cs" },
  { prefix: "bd.in ", id: "bd.in" },
  { prefix: "bd.out ", id: "bd.out" },
  { prefix: "bd.param ", id: "bd.param" },
]);

const SEMANTIC_TOKEN_TYPES = Object.freeze({
  heading: "type",
  statementKeyword: "keyword",
  reference: "namespace",
  functionKeyword: "keyword",
});

const REFERENCE_PATTERN = /\b(?:base|cs|cp\.(?:form|sat|id|norm)|bd\.(?:in|out|param))\.[^,\s<>(){}[\]]+/gu;
const FUNCTION_KEYWORD_PATTERN = /\b(?:on|by|payload|cardinality|to|from|domain|affects)\b/gu;

function splitLines(text) {
  return String(text || "").split(/\r?\n/);
}

function normalizeInlineSpace(text) {
  return String(text || "").replace(/\s+/gu, " ").trim();
}

function detectFrameworkSectionIdFromHeading(trimmedHeading) {
  const heading = String(trimmedHeading || "").trim();
  return FRAMEWORK_SECTION_ID_BY_HEADING[heading] || "";
}

function detectStatementKind(lineText) {
  const text = String(lineText || "").trim();
  for (const candidate of STATEMENT_KIND_BY_PREFIX) {
    if (text.startsWith(candidate.prefix)) {
      return candidate.id;
    }
  }
  return "";
}

function getStatementDefinitionById(id) {
  return FRAMEWORK_STATEMENT_DEFINITIONS.find((item) => item.id === id) || null;
}

function getAllowedStatementIdsForSection(sectionId) {
  const safeSectionId = String(sectionId || "").trim();
  return FRAMEWORK_STATEMENT_DEFINITIONS
    .filter((item) => item.sectionId === safeSectionId)
    .map((item) => item.id);
}

function validateStatement(statementId, normalizedStatementText) {
  const definition = getStatementDefinitionById(statementId);
  if (!definition) {
    return false;
  }
  return definition.pattern.test(String(normalizedStatementText || "").trim());
}

function normalizeStatementLines(lines) {
  if (!Array.isArray(lines)) {
    return "";
  }
  return normalizeInlineSpace(lines.map((line) => String(line || "").trim()).join(" "));
}

function collectFrameworkSemanticTokens(text) {
  const tokens = [];
  const lines = splitLines(text);

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
    const line = String(lines[lineIndex] || "");
    const trimmed = line.trim();
    const leadingSpaces = line.length - line.trimStart().length;

    if (FRAMEWORK_SECTION_ID_BY_HEADING[trimmed]) {
      tokens.push({
        line: lineIndex,
        startChar: leadingSpaces,
        length: trimmed.length,
        tokenType: SEMANTIC_TOKEN_TYPES.heading,
      });
      continue;
    }

    const statementKind = detectStatementKind(trimmed);
    if (statementKind) {
      const keyword = statementKind === "cs" ? "cs" : statementKind;
      const keywordIndex = trimmed.indexOf(keyword);
      if (keywordIndex >= 0) {
        tokens.push({
          line: lineIndex,
          startChar: leadingSpaces + keywordIndex,
          length: keyword.length,
          tokenType: SEMANTIC_TOKEN_TYPES.statementKeyword,
        });
      }
    }

    for (const match of trimmed.matchAll(REFERENCE_PATTERN)) {
      if (!match[0]) {
        continue;
      }
      tokens.push({
        line: lineIndex,
        startChar: leadingSpaces + Number(match.index || 0),
        length: match[0].length,
        tokenType: SEMANTIC_TOKEN_TYPES.reference,
      });
    }

    for (const match of trimmed.matchAll(FUNCTION_KEYWORD_PATTERN)) {
      if (!match[0]) {
        continue;
      }
      tokens.push({
        line: lineIndex,
        startChar: leadingSpaces + Number(match.index || 0),
        length: match[0].length,
        tokenType: SEMANTIC_TOKEN_TYPES.functionKeyword,
      });
    }
  }

  return tokens;
}

function getFrameworkCompletionTriggerChars() {
  return ["@", "#", "g", "b", "c", "d", ".", " ", ":"];
}

function buildFrameworkSnippetTemplateObject() {
  return {
    prefix: "@framework",
    description: "Insert keyword-first framework module template.",
    body: [...FRAMEWORK_TEMPLATE_SNIPPET_BODY],
  };
}

module.exports = {
  FRAMEWORK_DIRECTIVE,
  FRAMEWORK_REQUIRED_BOUNDARY_SECTIONS,
  FRAMEWORK_REQUIRED_TOP_LEVEL_SECTIONS,
  FRAMEWORK_SECTION_COMPLETION_DEFINITIONS,
  FRAMEWORK_SECTION_HEADINGS,
  FRAMEWORK_STATEMENT_DEFINITIONS,
  FRAMEWORK_TEMPLATE_SNIPPET_BODY,
  FRAMEWORK_TITLE_PATTERN,
  SEMANTIC_TOKEN_TYPES,
  buildFrameworkSnippetTemplateObject,
  collectFrameworkSemanticTokens,
  detectFrameworkSectionIdFromHeading,
  detectStatementKind,
  getAllowedStatementIdsForSection,
  getFrameworkCompletionTriggerChars,
  getStatementDefinitionById,
  normalizeStatementLines,
  splitLines,
  validateStatement,
};

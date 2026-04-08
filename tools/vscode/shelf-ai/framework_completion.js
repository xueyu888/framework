const fs = require("fs");
const path = require("path");

const MARKDOWN_SNIPPETS_FILE = path.join(__dirname, "snippets", "markdown.code-snippets");
const FRAMEWORK_TEMPLATE_SNIPPET_NAME = "@framework Module Template";
const FRAMEWORK_SECTION_HEADINGS = Object.freeze({
  goal: "## 0. 目标 (Goal)",
  base: "## 1. 最小结构基（Minimal Structural Bases）",
  rule: "## 2. 基排列组合（Base Arrangement / Combination）",
  boundary: "## 3. 边界定义（Boundary）",
  boundaryPorts: "### 3.1 接口定义（IO / Ports）",
  boundaryParameters: "### 3.2 参数边界（Parameter Constraints）",
  capability: "## 4. 能力声明（Capability Statement）",
});

function splitLines(text) {
  return String(text || "").split(/\r?\n/);
}

function loadMarkdownSnippets() {
  return JSON.parse(fs.readFileSync(MARKDOWN_SNIPPETS_FILE, "utf8"));
}

function getFrameworkTemplateSnippetBody() {
  const snippets = loadMarkdownSnippets();
  const snippet = snippets[FRAMEWORK_TEMPLATE_SNIPPET_NAME];
  if (!snippet || !Array.isArray(snippet.body) || snippet.body.length === 0) {
    throw new Error(`missing snippet body for ${FRAMEWORK_TEMPLATE_SNIPPET_NAME}`);
  }
  return snippet.body.slice();
}

function getFrameworkTemplateSnippetText() {
  return getFrameworkTemplateSnippetBody().join("\n");
}

function detectSectionIdFromHeading(trimmedHeading) {
  const heading = String(trimmedHeading || "").trim();
  if (heading === FRAMEWORK_SECTION_HEADINGS.goal) {
    return "goal";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.base) {
    return "base";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.rule) {
    return "rule";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.boundary) {
    return "boundary";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.boundaryPorts) {
    return "boundary-ports";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.boundaryParameters) {
    return "boundary-parameters";
  }
  if (heading === FRAMEWORK_SECTION_HEADINGS.capability) {
    return "capability";
  }
  return "";
}

function detectFrameworkAuthoringState(documentText, lineNumber = 0) {
  const lines = splitLines(documentText);
  const safeLineNumber = Math.max(0, Math.min(Number(lineNumber || 0), Math.max(0, lines.length - 1)));
  let sectionId = "";

  for (let index = 0; index <= safeLineNumber; index += 1) {
    const trimmed = lines[index].trim();
    if (trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
      const detected = detectSectionIdFromHeading(trimmed);
      if (detected) {
        sectionId = detected;
      }
    }
  }

  return {
    sectionId,
    lineCount: lines.length,
  };
}

function collectNextSymbolNumbers(documentText) {
  const text = String(documentText || "");
  const maxima = {
    C: 0,
    P: 0,
    B: 0,
    R: 0,
    N: 0,
  };
  const symbolPattern = /`([CPBRN])(\d+)(?:\.\d+)?`/g;
  for (const match of text.matchAll(symbolPattern)) {
    const symbol = String(match[1] || "");
    const number = Number(match[2] || 0);
    if (!Number.isInteger(number) || number <= 0 || !Object.prototype.hasOwnProperty.call(maxima, symbol)) {
      continue;
    }
    if (number > maxima[symbol]) {
      maxima[symbol] = number;
    }
  }
  return {
    C: maxima.C + 1,
    P: maxima.P + 1,
    B: maxima.B + 1,
    R: maxima.R + 1,
    N: maxima.N + 1,
  };
}

function findNearestRuleNumber(documentText, lineNumber = 0) {
  const lines = splitLines(documentText);
  const safeLineNumber = Math.max(0, Math.min(Number(lineNumber || 0), Math.max(0, lines.length - 1)));
  for (let index = safeLineNumber; index >= 0; index -= 1) {
    const trimmed = lines[index].trim();
    if (index !== safeLineNumber && trimmed.startsWith("## ")) {
      break;
    }
    const ruleMatch = /^-\s+`R(\d+)`\s+/.exec(trimmed);
    if (ruleMatch) {
      return Number(ruleMatch[1]);
    }
  }
  return null;
}

function createCompletionDefinitions(dynamic = {}) {
  const next = {
    C: Number(dynamic.nextNumbers?.C || 1),
    P: Number(dynamic.nextNumbers?.P || 1),
    B: Number(dynamic.nextNumbers?.B || 1),
    R: Number(dynamic.nextNumbers?.R || 1),
    N: Number(dynamic.nextNumbers?.N || 1),
  };
  return [
    {
      id: "framework-title",
      label: "# 中文模块名:EnglishName",
      detail: "插入框架模块双语标题",
      documentation: "框架标题必须遵守 `中文名:EnglishName` 格式。",
      insertText: "# ${1:中文模块名}:${2:EnglishName}",
      contexts: ["hash", "framework-file-empty"],
    },
    {
      id: "framework-module-template",
      label: "@framework 标准模块模板",
      detail: "插入完整框架标准模板",
      documentation: "覆盖 0~4 主章节、边界子章节、能力与非职责声明。",
      insertText: getFrameworkTemplateSnippetText(),
      contexts: ["at", "framework-file-empty"],
    },
    {
      id: "framework-directive",
      label: "@framework",
      detail: "插入 plain @framework 指令",
      documentation: "框架文件必须使用无参数的 plain `@framework` 指令。",
      insertText: "@framework",
      contexts: ["at", "framework-file-empty"],
    },
    {
      id: "section-goal",
      label: "## 0. 目标 (Goal)",
      detail: "插入目标主章节",
      documentation: "固定框架章节：目标。",
      insertText: "## 0. 目标 (Goal)",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-base",
      label: "## 1. 最小结构基（Minimal Structural Bases）",
      detail: "插入最小结构基主章节",
      documentation: "固定框架章节：最小结构基。",
      insertText: "## 1. 最小结构基（Minimal Structural Bases）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-rule",
      label: "## 2. 基排列组合（Base Arrangement / Combination）",
      detail: "插入基排列组合主章节",
      documentation: "固定框架章节：基排列组合。",
      insertText: "## 2. 基排列组合（Base Arrangement / Combination）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-boundary",
      label: "## 3. 边界定义（Boundary）",
      detail: "插入边界定义主章节",
      documentation: "固定框架章节：边界定义。",
      insertText: "## 3. 边界定义（Boundary）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "section-capability",
      label: "## 4. 能力声明（Capability Statement）",
      detail: "插入能力声明主章节",
      documentation: "固定框架章节：能力声明。",
      insertText: "## 4. 能力声明（Capability Statement）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "subsection-boundary-ports",
      label: "### 3.1 接口定义（IO / Ports）",
      detail: "插入边界接口定义子章节",
      documentation: "边界章节固定子章节：接口定义。",
      insertText: "### 3.1 接口定义（IO / Ports）",
      contexts: ["hash", "framework-file-empty", "section", "section-boundary"],
    },
    {
      id: "subsection-boundary-parameters",
      label: "### 3.2 参数边界（Parameter Constraints）",
      detail: "插入边界参数约束子章节",
      documentation: "边界章节固定子章节：参数边界。",
      insertText: "### 3.2 参数边界（Parameter Constraints）",
      contexts: ["hash", "framework-file-empty", "section"],
    },
    {
      id: "goal-item",
      label: "目标条目",
      detail: "插入目标说明条目",
      documentation: "用于 `## 0. 目标` 章节。",
      insertText: "- ${1:目标说明。}",
      contexts: ["list", "framework-file-empty", "section-goal"],
    },
    {
      id: "capability-item",
      label: "C 条目",
      detail: "插入能力声明条目",
      documentation: "用于 `C*` 能力声明。",
      insertText: `- \`C\${1:${next.C}}\` \${2:能力名}：\${3:待补充结构能力说明}。`,
      contexts: ["list", "capability-symbol", "framework-file-empty", "section-capability"],
    },
    {
      id: "non-responsibility-item",
      label: "N 条目",
      detail: "插入非职责声明条目",
      documentation: "用于 `N*` 非职责声明。",
      insertText: `- \`N\${1:${next.N}}\` \${2:非职责声明}：\${3:待补充非职责范围}。`,
      contexts: [
        "list",
        "non-responsibility-symbol",
        "framework-file-empty",
        "section-capability",
      ],
    },
    {
      id: "port-item",
      label: "接口条目",
      detail: "插入 IO / Ports 条目",
      documentation: "用于边界接口定义（3.1）。",
      insertText: "- `${1:PORT_IN}`：${2:运行时输入接口，待补充接口说明。}",
      contexts: ["list", "boundary-symbol", "framework-file-empty", "section-boundary-ports"],
    },
    {
      id: "boundary-item",
      label: "参数条目",
      detail: "插入参数边界条目",
      documentation: "用于边界参数约束（3.2）。",
      insertText: `- \`\${1:P${next.P}}\` \${2:参数名}：\${3:待定义参数约束}。`,
      contexts: [
        "list",
        "boundary-symbol",
        "framework-file-empty",
        "section-boundary",
        "section-boundary-parameters",
      ],
    },
    {
      id: "base-item",
      label: "B 条目",
      detail: "插入最小结构基条目",
      documentation: "用于 `B*` 结构基定义。",
      insertText: `- \`B\${1:${next.B}}\` \${2:结构基名}：\${3:待定义结构说明}。`,
      contexts: ["list", "base-symbol", "framework-file-empty", "section-base"],
    },
    {
      id: "rule-item",
      label: "R 条目",
      detail: "插入基排列组合条目",
      documentation: "用于 `R*` 单行规则条目。",
      insertText: `- \`R\${1:${next.R}}\` \`\${2:规则名}\`：由 \`\${3:{B1, B2}}\` 形成 \`\${4:结果}\`，导出 \`\${5:C1}\`。`,
      contexts: ["list", "rule-symbol", "framework-file-empty", "section-rule"],
    },
  ];
}

function detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile, authoringState = {}) {
  const normalizedLine = linePrefix || "";
  const trimmed = normalizedLine.trimStart();
  const compact = trimmed.replace(/[`。\s]/g, "");
  const upperWord = String(wordPrefix || "").toUpperCase();
  const contexts = new Set();
  const sectionId = String(authoringState.sectionId || "").trim();

  if (isFrameworkFile && trimmed === "") {
    contexts.add("framework-file-empty");
  }
  if (trimmed.startsWith("@")) {
    contexts.add("at");
  }
  if (trimmed.startsWith("#")) {
    contexts.add("hash");
  }
  if (trimmed.startsWith("##")) {
    contexts.add("section");
  }
  if (trimmed.startsWith("-") || trimmed.startsWith("`")) {
    contexts.add("list");
  }
  if (/^C\d*$/.test(upperWord) || compact.startsWith("-C") || compact.startsWith("C")) {
    contexts.add("capability-symbol");
  }
  if (
    /^(P\d*|[A-Z_]{2,})$/.test(upperWord) ||
    compact.startsWith("-P") ||
    compact.startsWith("P") ||
    compact.startsWith("-SURFACE") ||
    compact.startsWith("SURFACE")
  ) {
    contexts.add("boundary-symbol");
  }
  if (/^B\d*$/.test(upperWord) || compact.startsWith("-B") || compact.startsWith("B")) {
    contexts.add("base-symbol");
  }
  if (/^R\d*$/.test(upperWord) || compact.startsWith("-R") || compact.startsWith("R")) {
    contexts.add("rule-symbol");
  }
  if (/^N\d*$/.test(upperWord) || compact.startsWith("-N") || compact.startsWith("N")) {
    contexts.add("non-responsibility-symbol");
  }
  if (sectionId) {
    contexts.add(`section-${sectionId}`);
  }

  return contexts;
}

function getFrameworkCompletionEntries(linePrefix, wordPrefix, isFrameworkFile, options = {}) {
  const documentText = String(options.documentText || "");
  const lineNumber = Number(options.lineNumber || 0);
  const authoringState = detectFrameworkAuthoringState(documentText, lineNumber);
  const nextNumbers = collectNextSymbolNumbers(documentText);
  const nearestRuleNumber = findNearestRuleNumber(documentText, lineNumber);
  const contexts = detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile, authoringState);
  if (contexts.size === 0) {
    return [];
  }
  const activeSectionContext = [...contexts].find((item) => item.startsWith("section-")) || "";
  const symbolContexts = new Set([...contexts].filter((item) => item.endsWith("-symbol")));
  const allDefinitions = createCompletionDefinitions({
    nextNumbers,
    nearestRuleNumber,
  });

  return allDefinitions.filter((entry) => {
    const hasDirectContext = entry.contexts.some((context) => contexts.has(context));
    if (!hasDirectContext) {
      return false;
    }
    if (!activeSectionContext || contexts.has("framework-file-empty")) {
      return true;
    }
    if (entry.contexts.includes(activeSectionContext)) {
      return true;
    }
    if (symbolContexts.size > 0 && entry.contexts.some((context) => symbolContexts.has(context))) {
      return true;
    }
    if (entry.contexts.includes("at") || entry.contexts.includes("hash") || entry.contexts.includes("section")) {
      return true;
    }
    return false;
  });
}

function getFrameworkDashAutoExpansion(linePrefix, isFrameworkFile, options = {}) {
  if (!isFrameworkFile) {
    return null;
  }
  const normalizedLinePrefix = String(linePrefix || "");
  if (!/^\s*-\s*$/.test(normalizedLinePrefix)) {
    return null;
  }
  const documentText = String(options.documentText || "");
  const lineNumber = Number(options.lineNumber || 0);
  const authoringState = detectFrameworkAuthoringState(documentText, lineNumber);
  if (authoringState.sectionId !== "boundary-parameters") {
    return null;
  }
  const entries = getFrameworkCompletionEntries(
    normalizedLinePrefix,
    "",
    true,
    {
      documentText,
      lineNumber,
    }
  );
  const boundaryEntry = entries.find((entry) => entry.id === "boundary-item");
  if (!boundaryEntry || typeof boundaryEntry.insertText !== "string" || !boundaryEntry.insertText.startsWith("-")) {
    return null;
  }
  return {
    entryId: boundaryEntry.id,
    insertText: boundaryEntry.insertText.slice(1),
  };
}

module.exports = {
  FRAMEWORK_TEMPLATE_SNIPPET_NAME,
  FRAMEWORK_SECTION_HEADINGS,
  detectFrameworkAuthoringState,
  detectFrameworkCompletionContexts,
  getFrameworkDashAutoExpansion,
  getFrameworkCompletionEntries,
  getFrameworkTemplateSnippetBody,
  getFrameworkTemplateSnippetText,
};

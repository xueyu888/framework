const frameworkGrammar = require("./framework_grammar");

const FRAMEWORK_TEMPLATE_SNIPPET_NAME = "@framework Module Template";
const FRAMEWORK_SECTION_HEADINGS = frameworkGrammar.FRAMEWORK_SECTION_HEADINGS;

function splitLines(text) {
  return frameworkGrammar.splitLines(text);
}

function getFrameworkTemplateSnippetBody() {
  return [...frameworkGrammar.FRAMEWORK_TEMPLATE_SNIPPET_BODY];
}

function getFrameworkTemplateSnippetText() {
  return getFrameworkTemplateSnippetBody().join("\n");
}

function detectFrameworkAuthoringState(documentText, lineNumber = 0) {
  const lines = splitLines(documentText);
  const safeLineNumber = Math.max(0, Math.min(Number(lineNumber || 0), Math.max(0, lines.length - 1)));
  let sectionId = "";

  for (let index = 0; index <= safeLineNumber; index += 1) {
    const trimmed = lines[index].trim();
    if (!trimmed.startsWith("#")) {
      continue;
    }
    const detected = frameworkGrammar.detectFrameworkSectionIdFromHeading(trimmed);
    if (detected) {
      sectionId = detected;
    }
  }

  return {
    sectionId,
    lineCount: lines.length,
  };
}

function createCompletionDefinitions() {
  const entries = [
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
      documentation: "使用与 lint/highlight 同源 grammar 的模板。",
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
  ];

  for (const heading of frameworkGrammar.FRAMEWORK_SECTION_COMPLETION_DEFINITIONS) {
    entries.push({
      id: `heading-${heading.id}`,
      label: heading.heading,
      detail: "插入章节标题",
      documentation: "章节标题来自共享 grammar 定义。",
      insertText: heading.heading,
      contexts: ["hash", "heading", "framework-file-empty"],
    });
  }

  for (const definition of frameworkGrammar.FRAMEWORK_STATEMENT_DEFINITIONS) {
    entries.push({
      id: `statement-${definition.id}`,
      label: definition.completionLabel,
      detail: definition.completionDetail,
      documentation: "语句模板来自共享 grammar 定义。",
      insertText: definition.template,
      contexts: ["line", `section-${definition.sectionId}`],
    });
  }

  return entries;
}

function detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile, authoringState = {}) {
  const normalizedLine = String(linePrefix || "");
  const trimmed = normalizedLine.trimStart();
  const sectionId = String(authoringState.sectionId || "").trim();
  const compactWord = String(wordPrefix || "").trim().toLowerCase();
  const contexts = new Set();

  if (isFrameworkFile && trimmed === "") {
    contexts.add("framework-file-empty");
  }
  if (trimmed.startsWith("@")) {
    contexts.add("at");
  }
  if (trimmed.startsWith("#")) {
    contexts.add("hash");
  }
  if (trimmed.startsWith("##") || trimmed.startsWith("###")) {
    contexts.add("heading");
  }
  if (trimmed === "" || /^[a-zA-Z]/.test(trimmed) || compactWord) {
    contexts.add("line");
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
  const contexts = detectFrameworkCompletionContexts(linePrefix, wordPrefix, isFrameworkFile, authoringState);
  if (contexts.size === 0) {
    return [];
  }
  const activeSectionContext = [...contexts].find((item) => item.startsWith("section-")) || "";
  const allDefinitions = createCompletionDefinitions();

  return allDefinitions.filter((entry) => {
    if (!entry.contexts.some((context) => contexts.has(context))) {
      return false;
    }
    if (!activeSectionContext || contexts.has("framework-file-empty")) {
      return true;
    }
    if (entry.contexts.includes(activeSectionContext)) {
      return true;
    }
    return entry.contexts.includes("at")
      || entry.contexts.includes("hash")
      || entry.contexts.includes("heading");
  });
}

function getFrameworkDashAutoExpansion() {
  return null;
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

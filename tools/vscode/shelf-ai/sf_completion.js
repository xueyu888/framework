const sfGrammar = require("./sf_grammar");

const SF_TEMPLATE_SNIPPET_NAME = "Shelf Framework Template";

function getShelfFrameworkTemplateSnippetBody() {
  return [...sfGrammar.SF_TEMPLATE_SNIPPET_BODY];
}

function getShelfFrameworkTemplateSnippetText() {
  return getShelfFrameworkTemplateSnippetBody().join("\n");
}

function createCompletionEntries() {
  const entries = [
    {
      id: "sf-template",
      label: "shelf-framework 标准模板",
      detail: "插入完整 .sf 模板",
      documentation: "使用与 lint/highlight 同源的 .sf grammar。",
      insertText: getShelfFrameworkTemplateSnippetText(),
      contexts: ["file-empty", "module-line"],
    },
  ];

  for (const definition of sfGrammar.SF_TOP_LEVEL_TEMPLATES) {
    entries.push({
      id: definition.id,
      label: definition.label,
      detail: definition.detail,
      documentation: definition.documentation,
      insertText: definition.insertText,
      contexts: ["top-level", "module-line"],
    });
  }

  for (const definition of sfGrammar.SF_STATEMENT_DEFINITIONS) {
    entries.push({
      id: `statement-${definition.id}`,
      label: definition.completionLabel,
      detail: definition.completionDetail,
      documentation: "语句模板来自共享 .sf grammar 定义。",
      insertText: definition.template,
      contexts: [`section-${definition.sectionId}`],
    });
  }

  return entries;
}

function detectShelfFrameworkCompletionContexts(linePrefix, documentText, lineNumber = 0) {
  const authoringState = sfGrammar.detectShelfFrameworkAuthoringSection(documentText, lineNumber);
  const indent = sfGrammar.getIndent(linePrefix);
  const trimmed = sfGrammar.trimLine(linePrefix);
  const contexts = new Set();

  if (!sfGrammar.trimLine(documentText)) {
    contexts.add("file-empty");
  }

  if (!authoringState.hasModule || lineNumber === 0 || /^MODULE\b/u.test(trimmed)) {
    contexts.add("module-line");
  }

  if (authoringState.hasModule && indent <= 4) {
    contexts.add("top-level");
  }

  if (authoringState.sectionId && indent >= 8) {
    contexts.add(`section-${authoringState.sectionId}`);
  }

  return {
    contexts,
    authoringState,
  };
}

function getShelfFrameworkCompletionEntries(linePrefix, wordPrefix, options = {}) {
  const documentText = String(options.documentText || "");
  const lineNumber = Number(options.lineNumber || 0);
  const safePrefix = String(wordPrefix || "").trim().toLowerCase();
  const { contexts } = detectShelfFrameworkCompletionContexts(linePrefix, documentText, lineNumber);
  const entries = createCompletionEntries().filter((entry) => entry.contexts.some((item) => contexts.has(item)));

  if (!safePrefix) {
    return entries;
  }

  return entries.filter((entry) => String(entry.label || "").toLowerCase().includes(safePrefix));
}

module.exports = {
  SF_TEMPLATE_SNIPPET_NAME,
  detectShelfFrameworkCompletionContexts,
  getShelfFrameworkCompletionEntries,
  getShelfFrameworkTemplateSnippetBody,
  getShelfFrameworkTemplateSnippetText,
};

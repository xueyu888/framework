const sfGrammar = require("./sf_grammar");

function escapeRegexLiteral(value) {
  return String(value || "").replace(/[|\\{}()[\]^$+*?.]/gu, "\\$&");
}

function buildAlternation(values) {
  return values.map((value) => escapeRegexLiteral(value)).join("|");
}

function buildShelfFrameworkTextMateGrammar() {
  const blockHeadings = sfGrammar.SF_BLOCK_DEFINITIONS
    .filter((definition) => definition.id !== "goal")
    .map((definition) => definition.heading);
  const shapeKeywords = Array.from(
    new Set(
      sfGrammar.SF_STATEMENT_DEFINITIONS
        .filter((definition) => definition.annotationKind === "shape")
        .map((definition) => definition.keyword)
    )
  );
  const subtypeKeywords = Array.from(
    new Set(
      sfGrammar.SF_STATEMENT_DEFINITIONS
        .filter((definition) => definition.annotationKind === "subtype")
        .map((definition) => definition.keyword)
    )
  );
  const plainKeywords = Array.from(
    new Set(
      sfGrammar.SF_STATEMENT_DEFINITIONS
        .filter((definition) => !definition.annotationKind)
        .map((definition) => definition.keyword)
    )
  );

  return {
    $schema: "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
    name: "Shelf Framework",
    scopeName: "source.shelf-framework",
    fileTypes: ["sf"],
    patterns: [
      { include: "#module" },
      { include: "#goal" },
      { include: "#block" },
      { include: "#declaration-shape" },
      { include: "#declaration-subtype" },
      { include: "#declaration-plain" },
      { include: "#string" },
      { include: "#reference" },
    ],
    repository: {
      module: {
        match: "^(MODULE)(\\s+)([^:]+)(:)([A-Za-z_][A-Za-z0-9_]*)(\\s*:\\s*)$",
        captures: {
          1: { name: "keyword.control.shelf-framework" },
          3: { name: "entity.name.section.shelf-framework" },
          5: { name: "entity.name.type.shelf-framework" },
        },
      },
      goal: {
        begin: "^(\\s{4})(Goal)(\\s*:=\\s*)",
        beginCaptures: {
          2: { name: "entity.name.section.shelf-framework" },
          3: { name: "keyword.operator.assignment.shelf-framework" },
        },
        end: "$",
        patterns: [
          { include: "#string" },
          { include: "#reference" },
        ],
      },
      block: {
        match: `^(\\s{4})(${buildAlternation(blockHeadings)})$`,
        captures: {
          2: { name: "entity.name.section.shelf-framework" },
        },
      },
      declarationShape: {
        begin: `^(\\s{8})(${buildAlternation(shapeKeywords)})(\\[[^\\]]+\\])?(\\s+)([^:=]+?)(\\s*:=\\s*)`,
        beginCaptures: {
          2: { name: "keyword.control.shelf-framework" },
          3: { name: "keyword.operator.shelf-framework" },
          5: { name: "variable.other.shelf-framework" },
          6: { name: "keyword.operator.assignment.shelf-framework" },
        },
        end: "$",
        patterns: [
          { include: "#string" },
          { include: "#reference" },
        ],
      },
      declarationSubtype: {
        begin: `^(\\s{8})(${buildAlternation(subtypeKeywords)})(<[^>]+>)(\\s+)([^:=]+?)(\\s*:=\\s*)`,
        beginCaptures: {
          2: { name: "keyword.control.shelf-framework" },
          3: { name: "storage.type.annotation.shelf-framework" },
          5: { name: "variable.other.shelf-framework" },
          6: { name: "keyword.operator.assignment.shelf-framework" },
        },
        end: "$",
        patterns: [
          { include: "#string" },
          { include: "#reference" },
        ],
      },
      declarationPlain: {
        begin: `^(\\s{8})(${buildAlternation(plainKeywords)})(\\s+)([^:=]+?)(\\s*:=\\s*)`,
        beginCaptures: {
          2: { name: "keyword.control.shelf-framework" },
          4: { name: "variable.other.shelf-framework" },
          5: { name: "keyword.operator.assignment.shelf-framework" },
        },
        end: "$",
        patterns: [
          { include: "#string" },
          { include: "#reference" },
        ],
      },
      string: {
        name: "string.quoted.double.shelf-framework",
        begin: "\"",
        end: "\"",
        patterns: [
          {
            match: "\\\\.",
            name: "constant.character.escape.shelf-framework",
          },
          { include: "#reference" },
        ],
      },
      reference: {
        name: "entity.name.namespace.shelf-framework",
        match: sfGrammar.SF_REFERENCE_PATTERN.source,
      },
    },
  };
}

module.exports = {
  buildShelfFrameworkTextMateGrammar,
};

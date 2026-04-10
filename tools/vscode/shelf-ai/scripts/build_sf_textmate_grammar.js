const fs = require("fs");
const path = require("path");

const { buildShelfFrameworkTextMateGrammar } = require("../sf_textmate_grammar");

const outputPath = path.join(__dirname, "..", "languages", "shelf-framework.tmLanguage.json");
const grammar = buildShelfFrameworkTextMateGrammar();

fs.writeFileSync(outputPath, `${JSON.stringify(grammar, null, 2)}\n`, "utf8");
console.log(`wrote ${path.relative(process.cwd(), outputPath)}`);

const fs = require("fs");
const path = require("path");

const FRAMEWORK_FILE_PATH_PATTERN = /^framework\/([^/]+)\/L(\d+)-M(\d+)-[^/]+\.md$/;
const MODULE_REF_WITH_RULES_PATTERN =
  /(?:(?<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?<level>\d+)\.M(?<module>\d+)\[(?<rules>[^\]]+)\]/g;
const MODULE_REF_PATTERN = /(?:(?<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?<level>\d+)\.M(?<module>\d+)/g;
const RULE_TOKEN_PATTERN = /R\d+(?:\.\d+)?/g;
const CORE_TOKEN_PATTERN = /R\d+\.\d+|R\d+|B\d+|C\d+|V\d+/g;
const UPPER_SYMBOL_PATTERN = /[A-Z][A-Z0-9_]+/g;
const BACKTICK_SEGMENT_PATTERN = /`([^`]+)`/g;
const SYMBOL_TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9_]*/g;

const SECTION_PREFIXES = [
  ["## 1. 能力声明", "capability"],
  ["## 2. 边界定义", "boundary"],
  ["## 3. 最小可行基", "base"],
  ["## 4. 基组合原则", "rule"],
  ["## 5. 验证", "verification"],
];

function normalizePathSlashes(value) {
  return value.replace(/\\/g, "/");
}

function getFrameworkDocumentInfo(filePath, repoRoot) {
  const relativePath = normalizePathSlashes(path.relative(repoRoot, filePath));
  const match = FRAMEWORK_FILE_PATH_PATTERN.exec(relativePath);
  if (!match) {
    return null;
  }
  return {
    relativePath,
    frameworkName: match[1],
    level: `L${match[2]}`,
    moduleId: `M${match[3]}`,
  };
}

function isFrameworkMarkdownFile(filePath, repoRoot) {
  return getFrameworkDocumentInfo(filePath, repoRoot) !== null;
}

function detectSection(lineText) {
  for (const [prefix, section] of SECTION_PREFIXES) {
    if (lineText.startsWith(prefix)) {
      return section;
    }
  }
  return "";
}

function registerSymbol(symbols, token, line, character) {
  if (!token || symbols.has(token)) {
    return;
  }
  symbols.set(token, {
    line,
    character,
    length: token.length,
  });
}

function buildDefinitionIndex(text) {
  const symbols = new Map();
  const boundaryIds = new Set();
  const lines = text.split(/\r?\n/);
  let section = "";
  let header = null;

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
    const lineText = lines[lineIndex];
    const trimmed = lineText.trim();
    const sectionName = detectSection(trimmed);
    if (sectionName) {
      section = sectionName;
    } else if (trimmed.startsWith("## ")) {
      section = "";
    }

    if (!header) {
      const headingMatch = /^\s*#\s+/.exec(lineText);
      if (headingMatch) {
        header = {
          line: lineIndex,
          character: headingMatch[0].length,
          length: Math.max(1, lineText.trim().length - 2),
        };
      }
    }

    if (section === "capability") {
      const match = /^\s*[-*]\s*`(C\d+)`/.exec(lineText);
      if (match) {
        registerSymbol(symbols, match[1], lineIndex, match.index + match[0].indexOf(match[1]));
      }
      continue;
    }

    if (section === "boundary") {
      const match = /^\s*[-*]\s*`([A-Za-z][A-Za-z0-9_]*)`/.exec(lineText);
      if (match) {
        boundaryIds.add(match[1]);
        registerSymbol(symbols, match[1], lineIndex, match.index + match[0].indexOf(match[1]));
      }
      continue;
    }

    if (section === "base") {
      const match = /^\s*[-*]\s*`(B\d+)`/.exec(lineText);
      if (match) {
        registerSymbol(symbols, match[1], lineIndex, match.index + match[0].indexOf(match[1]));
      }
      continue;
    }

    if (section === "rule") {
      const topMatch = /^\s*[-*]\s*`(R\d+)`\s*/.exec(lineText);
      if (topMatch) {
        registerSymbol(symbols, topMatch[1], lineIndex, topMatch.index + topMatch[0].indexOf(topMatch[1]));
        continue;
      }

      const childMatch = /^\s*[-*]\s*`(R\d+\.\d+)`\s*/.exec(lineText);
      if (childMatch) {
        registerSymbol(symbols, childMatch[1], lineIndex, childMatch.index + childMatch[0].indexOf(childMatch[1]));
        if (lineText.includes("输出结构")) {
          for (const segmentMatch of lineText.matchAll(BACKTICK_SEGMENT_PATTERN)) {
            const segment = segmentMatch[1];
            const segmentOffset = (segmentMatch.index || 0) + 1;
            for (const tokenMatch of segment.matchAll(SYMBOL_TOKEN_PATTERN)) {
              const token = tokenMatch[0];
              if (
                /^C\d+$/.test(token) ||
                /^B\d+$/.test(token) ||
                /^V\d+$/.test(token) ||
                /^R\d+(?:\.\d+)?$/.test(token) ||
                boundaryIds.has(token)
              ) {
                continue;
              }
              registerSymbol(symbols, token, lineIndex, segmentOffset + (tokenMatch.index || 0));
            }
          }
        }
      }
      continue;
    }

    if (section === "verification") {
      const match = /^\s*[-*]\s*`(V\d+)`/.exec(lineText);
      if (match) {
        registerSymbol(symbols, match[1], lineIndex, match.index + match[0].indexOf(match[1]));
      }
    }
  }

  return {
    header,
    symbols,
  };
}

function containsPosition(start, end, character) {
  return character >= start && character < end;
}

function findTokenContext(lineText, character) {
  for (const match of lineText.matchAll(MODULE_REF_WITH_RULES_PATTERN)) {
    const moduleRefText = match[0].slice(0, match[0].indexOf("["));
    const start = match.index || 0;
    const ruleBlockStart = start + moduleRefText.length + 1;
    const rulesText = match.groups?.rules || "";
    for (const ruleMatch of rulesText.matchAll(RULE_TOKEN_PATTERN)) {
      const ruleStart = ruleBlockStart + (ruleMatch.index || 0);
      const ruleEnd = ruleStart + ruleMatch[0].length;
      if (!containsPosition(ruleStart, ruleEnd, character)) {
        continue;
      }
      return {
        kind: "moduleRule",
        token: ruleMatch[0],
        start: ruleStart,
        end: ruleEnd,
        frameworkName: match.groups?.framework || null,
        level: `L${match.groups?.level || ""}`,
        moduleId: `M${match.groups?.module || ""}`,
      };
    }
  }

  for (const match of lineText.matchAll(MODULE_REF_PATTERN)) {
    const start = match.index || 0;
    const end = start + match[0].length;
    if (!containsPosition(start, end, character)) {
      continue;
    }
    return {
      kind: "moduleRef",
      token: match[0],
      start,
      end,
      frameworkName: match.groups?.framework || null,
      level: `L${match.groups?.level || ""}`,
      moduleId: `M${match.groups?.module || ""}`,
    };
  }

  for (const match of lineText.matchAll(CORE_TOKEN_PATTERN)) {
    const start = match.index || 0;
    const end = start + match[0].length;
    if (!containsPosition(start, end, character)) {
      continue;
    }
    return {
      kind: "localSymbol",
      token: match[0],
      start,
      end,
    };
  }

  for (const match of lineText.matchAll(UPPER_SYMBOL_PATTERN)) {
    const start = match.index || 0;
    const end = start + match[0].length;
    if (!containsPosition(start, end, character)) {
      continue;
    }
    return {
      kind: "localSymbol",
      token: match[0],
      start,
      end,
    };
  }

  return null;
}

function resolveModuleFile(repoRoot, currentFrameworkName, refFrameworkName, level, moduleId) {
  const frameworkName = refFrameworkName || currentFrameworkName;
  if (!frameworkName || !level || !moduleId) {
    return null;
  }

  const moduleDir = path.join(repoRoot, "framework", frameworkName);
  if (!fs.existsSync(moduleDir) || !fs.statSync(moduleDir).isDirectory()) {
    return null;
  }

  const prefix = `${level}-${moduleId}-`;
  for (const entry of fs.readdirSync(moduleDir)) {
    if (!entry.endsWith(".md")) {
      continue;
    }
    if (entry.startsWith(prefix)) {
      return path.join(moduleDir, entry);
    }
  }
  return null;
}

function resolveLocalSymbol(index, token) {
  const direct = index.symbols.get(token);
  if (direct) {
    return direct;
  }
  if (/^R\d+\.\d+$/.test(token)) {
    return index.symbols.get(token.split(".", 1)[0]) || null;
  }
  return null;
}

function resolveDefinitionTarget({ repoRoot, filePath, text, line, character }) {
  const documentInfo = getFrameworkDocumentInfo(filePath, repoRoot);
  if (!documentInfo) {
    return null;
  }

  const lines = text.split(/\r?\n/);
  const lineText = lines[line] || "";
  const tokenContext = findTokenContext(lineText, character);
  if (!tokenContext) {
    return null;
  }

  if (tokenContext.kind === "moduleRef" || tokenContext.kind === "moduleRule") {
    const targetFilePath = resolveModuleFile(
      repoRoot,
      documentInfo.frameworkName,
      tokenContext.frameworkName,
      tokenContext.level,
      tokenContext.moduleId
    );
    if (!targetFilePath || !fs.existsSync(targetFilePath)) {
      return null;
    }
    const targetText = fs.readFileSync(targetFilePath, "utf8");
    const targetIndex = buildDefinitionIndex(targetText);
    if (tokenContext.kind === "moduleRef") {
      if (!targetIndex.header) {
        return null;
      }
      return {
        filePath: targetFilePath,
        line: targetIndex.header.line,
        character: targetIndex.header.character,
        length: targetIndex.header.length,
      };
    }
    const resolvedSymbol = resolveLocalSymbol(targetIndex, tokenContext.token);
    if (!resolvedSymbol) {
      return null;
    }
    return {
      filePath: targetFilePath,
      line: resolvedSymbol.line,
      character: resolvedSymbol.character,
      length: resolvedSymbol.length,
    };
  }

  const index = buildDefinitionIndex(text);
  const resolvedLocal = resolveLocalSymbol(index, tokenContext.token);
  if (!resolvedLocal) {
    return null;
  }
  return {
    filePath,
    line: resolvedLocal.line,
    character: resolvedLocal.character,
    length: resolvedLocal.length,
  };
}

module.exports = {
  buildDefinitionIndex,
  findTokenContext,
  getFrameworkDocumentInfo,
  isFrameworkMarkdownFile,
  resolveDefinitionTarget,
};

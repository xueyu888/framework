const fs = require("fs");
const path = require("path");
const correspondenceRuntime = require("./correspondence_runtime");
const evidenceTree = require("./evidence_tree");
const workspaceGuard = require("./guarding");

const MODULE_ID_PATTERN = /^(?<framework>[A-Za-z][A-Za-z0-9_]*)\.L(?<level>\d+)\.M(?<module>\d+)$/;
const MODULE_FILE_PATTERN = /^L(?<level>\d+)-M(?<module>\d+)-/;
const BASE_TOKEN_PATTERN = /\b(B\d+)\b/g;
const RULE_TOKEN_PATTERN = /\b(R\d+(?:\.\d+)?)\b/g;
const MODULE_REF_PATTERN = /\bL(?<level>\d+)\.M(?<module>\d+)\b/g;

/**
 * @typedef {Object} HoverItem
 * @property {string} token
 * @property {string} text
 */

/**
 * @typedef {Object} RuntimeTreeNode
 * @property {string} id
 * @property {string} label
 * @property {string} detail
 * @property {string} file
 * @property {number} line
 * @property {number} depth
 * @property {string} kind
 * @property {string} [group]
 * @property {number} [order]
 * @property {string} [title]
 * @property {string} [moduleName]
 * @property {string} [moduleRef]
 * @property {number} [sourceLine]
 * @property {number} [docLine]
 * @property {string} [hoverKicker]
 * @property {HoverItem[]} [capabilityItems]
 * @property {HoverItem[]} [baseItems]
 * @property {string} [objectId]
 * @property {Record<string, unknown>} [defaultTarget]
 * @property {Record<string, unknown>} [editTarget]
 * @property {Record<string, unknown>} [correspondenceAnchor]
 * @property {Record<string, unknown>} [implementationAnchor]
 * @property {Record<string, unknown>[]} [secondaryTargets]
 * @property {string[]} [relatedObjectIds]
 */

/**
 * @typedef {Object} RuntimeTreeEdge
 * @property {string} id
 * @property {string} from
 * @property {string} to
 * @property {string} relation
 * @property {string} [rules]
 * @property {string} [terms]
 * @property {string} [file]
 * @property {number} [line]
 */

/**
 * @typedef {Object} RuntimeFrameworkGroup
 * @property {string} name
 * @property {number} order
 * @property {number[]} localLevels
 * @property {Record<number, number>} levelNodeCounts
 */

/**
 * @typedef {Object} RuntimeTreeModel
 * @property {string} title
 * @property {string} description
 * @property {("framework"|"evidence")} kind
 * @property {RuntimeTreeNode[]} nodes
 * @property {RuntimeTreeEdge[]} edges
 * @property {string} [footText]
 * @property {"global_levels"|"framework_columns"} [layoutMode]
 * @property {Record<number, string>} [levelLabels]
 * @property {RuntimeFrameworkGroup[]} [frameworkGroups]
 * @property {Record<string, number>} [relationCounts]
 * @property {Record<string, unknown>} [objectIndex]
 * @property {Record<string, unknown>} [validationSummary]
 */

/**
 * @typedef {{ frameworkName: string, level: number, module: number }} ParsedModuleId
 */

/**
 * @param {unknown} value
 * @returns {string}
 */
function asText(value) {
  return String(value ?? "").trim();
}

/**
 * @param {unknown} value
 * @param {number} fallback
 * @returns {number}
 */
function asPositiveInt(value, fallback) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.max(1, Math.floor(parsed));
}

/**
 * @param {string} moduleId
 * @returns {ParsedModuleId | null}
 */
function parseModuleId(moduleId) {
  const match = MODULE_ID_PATTERN.exec(moduleId);
  if (!match || !match.groups) {
    return null;
  }
  return {
    frameworkName: String(match.groups.framework || ""),
    level: asPositiveInt(match.groups.level, 0),
    module: asPositiveInt(match.groups.module, 0),
  };
}

/**
 * @param {string} fileName
 * @returns {{ level: number, module: number } | null}
 */
function parseModuleFileName(fileName) {
  const match = MODULE_FILE_PATTERN.exec(fileName);
  if (!match || !match.groups) {
    return null;
  }
  return {
    level: asPositiveInt(match.groups.level, 0),
    module: asPositiveInt(match.groups.module, 0),
  };
}

/**
 * @param {string} filePath
 * @returns {{ title: string, line: number }}
 */
function firstMarkdownHeading(filePath) {
  try {
    const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
    for (let index = 0; index < lines.length; index += 1) {
      const match = /^\s*#\s+(.+)\s*$/.exec(lines[index] || "");
      if (match) {
        return {
          title: String(match[1] || "").trim(),
          line: index + 1,
        };
      }
    }
  } catch {
    return { title: "", line: 1 };
  }
  return { title: "", line: 1 };
}

/**
 * @param {string} moduleId
 * @param {string} baseId
 * @returns {string}
 */
function baseNodeId(moduleId, baseId) {
  return `${moduleId}.base.${baseId}`;
}

/**
 * @param {string} value
 * @returns {Set<string>}
 */
function extractBaseTokens(value) {
  const tokens = new Set();
  const text = asText(value);
  for (const match of text.matchAll(BASE_TOKEN_PATTERN)) {
    const token = asText(match[1]).toUpperCase();
    if (token) {
      tokens.add(token);
    }
  }
  return tokens;
}

/**
 * @param {string} value
 * @returns {Set<string>}
 */
function extractRuleTokens(value) {
  const tokens = new Set();
  const text = asText(value);
  for (const match of text.matchAll(RULE_TOKEN_PATTERN)) {
    const token = asText(match[1]).toUpperCase();
    if (token) {
      tokens.add(token);
    }
  }
  return tokens;
}

/**
 * @param {string} text
 * @param {string} frameworkName
 * @returns {string[]}
 */
function extractModuleRefsFromText(text, frameworkName) {
  const refs = new Set();
  const source = String(text || "");
  for (const match of source.matchAll(MODULE_REF_PATTERN)) {
    const level = asPositiveInt(match.groups?.level, 0);
    const module = asPositiveInt(match.groups?.module, 0);
    refs.add(`${frameworkName}.L${level}.M${module}`);
  }
  return [...refs];
}

/**
 * @param {string} filePath
 * @returns {string[]}
 */
function readMarkdownLines(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  } catch {
    return [];
  }
}

/**
 * @param {string[]} lines
 * @param {string} frameworkName
 * @returns {{
 *   bases: Array<{ baseId: string, detail: string, line: number, upstreamModuleIds: string[] }>,
 *   ruleBaseRefs: Map<string, Set<string>>,
 * }}
 */
function parseAuthorFrameworkBasesAndRules(lines, frameworkName) {
  /** @type {Array<{ baseId: string, detail: string, line: number, upstreamModuleIds: string[] }>} */
  const bases = [];
  /** @type {Map<string, Set<string>>} */
  const ruleBaseRefs = new Map();

  for (let index = 0; index < lines.length; index += 1) {
    const lineText = String(lines[index] || "");

    const baseMatch = /^\s*-\s*`(B\d+)`\s*(.*)$/.exec(lineText);
    if (baseMatch) {
      const baseId = asText(baseMatch[1]).toUpperCase();
      const detail = asText(baseMatch[2]).replace(/^[:：]\s*/, "");
      bases.push({
        baseId,
        detail,
        line: index + 1,
        upstreamModuleIds: extractModuleRefsFromText(lineText, frameworkName),
      });
    }

    const ruleTokens = extractRuleTokens(lineText);
    if (!ruleTokens.size) {
      continue;
    }
    const baseTokens = extractBaseTokens(lineText);
    if (!baseTokens.size) {
      continue;
    }
    for (const ruleToken of ruleTokens) {
      const topLevelRuleId = asText(ruleToken.split(".")[0]).toUpperCase();
      if (!topLevelRuleId) {
        continue;
      }
      if (!ruleBaseRefs.has(topLevelRuleId)) {
        ruleBaseRefs.set(topLevelRuleId, new Set());
      }
      const usedBases = ruleBaseRefs.get(topLevelRuleId);
      for (const baseToken of baseTokens) {
        usedBases?.add(baseToken);
      }
    }
  }

  return {
    bases,
    ruleBaseRefs,
  };
}

/**
 * @param {number[]} values
 * @returns {Record<number, string>}
 */
function authorLevelLabelsFor(values) {
  const pairs = [];
  const seen = new Set();
  for (const depth of values) {
    const normalizedDepth = Math.max(0, Math.floor(Number(depth) || 0));
    if (seen.has(normalizedDepth)) {
      continue;
    }
    seen.add(normalizedDepth);
    const level = Math.floor(normalizedDepth / 2);
    const suffix = normalizedDepth % 2 === 0 ? "模块层" : "基层";
    pairs.push([normalizedDepth, `L${level} ${suffix}`]);
  }
  pairs.sort((left, right) => Number(left[0]) - Number(right[0]));
  return Object.fromEntries(pairs);
}

/**
 * @param {unknown} sourceRef
 * @returns {{ filePath: string, line: number }}
 */
function sourceRefInfo(sourceRef) {
  return {
    filePath: workspaceGuard.normalizeRelPath(asText(sourceRef && typeof sourceRef === "object" ? sourceRef.file_path : "")),
    line: asPositiveInt(sourceRef && typeof sourceRef === "object" ? sourceRef.line : 1, 1),
  };
}

/**
 * @param {unknown[]} entries
 * @param {string} tokenKey
 * @param {(entry: Record<string, unknown>) => string} textBuilder
 * @returns {HoverItem[]}
 */
function hoverItems(entries, tokenKey, textBuilder) {
  /** @type {HoverItem[]} */
  const items = [];
  for (const entry of entries) {
    if (!entry || typeof entry !== "object") {
      continue;
    }
    const token = asText(entry[tokenKey]);
    const text = asText(textBuilder(/** @type {Record<string, unknown>} */ (entry)));
    if (!token && !text) {
      continue;
    }
    items.push({
      token,
      text: text || token,
    });
  }
  return items;
}

/**
 * @param {Map<string, Map<number, number>>} countsByFramework
 * @returns {RuntimeFrameworkGroup[]}
 */
function frameworkGroupsFromCounts(countsByFramework) {
  return [...countsByFramework.entries()]
    .sort((left, right) => left[0].localeCompare(right[0]))
    .map(([frameworkName, levelCounts], index) => ({
      name: frameworkName,
      order: index,
      localLevels: [...levelCounts.keys()].sort((left, right) => left - right),
      levelNodeCounts: Object.fromEntries(
        [...levelCounts.entries()].sort((left, right) => left[0] - right[0])
      ),
    }));
}

/**
 * @param {Iterable<number>} levels
 * @returns {Record<number, string>}
 */
function levelLabelsFor(levels) {
  return Object.fromEntries(
    [...new Set(levels)]
      .sort((left, right) => left - right)
      .map((level) => [level, `L${level} 标准层`])
  );
}

/**
 * @param {Record<string, unknown> | null | undefined} entry
 * @returns {string[]}
 */
function flattenModuleRelatedObjectIds(entry) {
  if (!entry || typeof entry !== "object") {
    return [];
  }
  const keys = ["bases", "rules", "boundaries", "static_params", "runtime_params"];
  const values = [];
  for (const key of keys) {
    const entries = entry[key];
    if (!Array.isArray(entries)) {
      continue;
    }
    for (const value of entries) {
      const objectId = asText(value);
      if (objectId) {
        values.push(objectId);
      }
    }
  }
  return values;
}

/**
 * @param {string} repoRoot
 * @returns {{ payload: Record<string, unknown>, treeEntriesByModuleId: Map<string, Record<string, unknown>> } | null}
 */
function loadFrameworkCorrespondenceProjection(repoRoot) {
  const projectFilePath = correspondenceRuntime.resolvePreferredProjectFile(repoRoot);
  if (!projectFilePath) {
    return null;
  }
  const canonical = correspondenceRuntime.readProjectCanonical(projectFilePath);
  if (!canonical || !canonical.correspondence) {
    return null;
  }
  const endpoints = correspondenceRuntime.resolveCorrespondenceApiPaths(canonical);
  const payload = correspondenceRuntime.readCorrespondenceApi(
    repoRoot,
    endpoints.root,
    { projectFilePath }
  );
  const treePayload = correspondenceRuntime.readCorrespondenceApi(
    repoRoot,
    endpoints.tree,
    { projectFilePath }
  );
  if (!payload || !treePayload || typeof payload !== "object") {
    return null;
  }
  const treeEntries = Array.isArray(treePayload.tree)
    ? treePayload.tree.filter((item) => item && typeof item === "object")
    : [];
  const treeEntriesByModuleId = new Map();
  const objectIndex = payload.object_index && typeof payload.object_index === "object"
    ? { ...payload.object_index }
    : {};
  for (const entry of treeEntries) {
    const moduleId = asText(entry.module_id);
    if (moduleId) {
      treeEntriesByModuleId.set(moduleId, entry);
    }
    const moduleObjectId = asText(entry.module_object_id);
    if (moduleObjectId) {
      const moduleObject = correspondenceRuntime.readCorrespondenceApi(
        repoRoot,
        `${endpoints.objectBase}${encodeURIComponent(moduleObjectId)}`,
        { projectFilePath }
      );
      if (moduleObject && typeof moduleObject === "object") {
        objectIndex[moduleObjectId] = moduleObject;
      }
    }
  }
  return {
    payload,
    objectIndex,
    treeEntriesByModuleId,
  };
}

/**
 * @param {string} repoRoot
 * @returns {{ modules: Record<string, unknown>[], staleProjectIds: string[], excludedProjectIds: string[] }}
 */
function collectCanonicalFrameworkModulesForTree(repoRoot) {
  const freshnessSummary = workspaceGuard.summarizeCanonicalFreshness(repoRoot);
  /** @type {Map<string, Record<string, unknown>>} */
  const moduleById = new Map();
  const staleProjectIds = new Set();
  const excludedProjectIds = new Set();

  for (const project of freshnessSummary.projects) {
    if (project.status === "missing" || project.status === "invalid") {
      excludedProjectIds.add(String(project.projectId || ""));
      continue;
    }
    if (project.status === "stale") {
      staleProjectIds.add(String(project.projectId || ""));
    }
    try {
      const canonical = JSON.parse(fs.readFileSync(project.canonicalPath, "utf8"));
      const rawModules = Array.isArray(canonical?.framework?.modules)
        ? canonical.framework.modules
        : [];
      for (const rawModule of rawModules) {
        if (!rawModule || typeof rawModule !== "object") {
          continue;
        }
        const moduleId = asText(rawModule.module_id);
        if (!moduleId || moduleById.has(moduleId)) {
          continue;
        }
        moduleById.set(moduleId, rawModule);
      }
    } catch {
      staleProjectIds.delete(String(project.projectId || ""));
      excludedProjectIds.add(String(project.projectId || ""));
    }
  }

  return {
    modules: [...moduleById.values()],
    staleProjectIds: [...staleProjectIds].filter(Boolean).sort(),
    excludedProjectIds: [...excludedProjectIds].filter(Boolean).sort(),
  };
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel | null}
 */
function buildCanonicalFrameworkTreeModel(repoRoot) {
  const collected = collectCanonicalFrameworkModulesForTree(repoRoot);
  if (!collected.modules.length) {
    return null;
  }
  const correspondenceProjection = loadFrameworkCorrespondenceProjection(repoRoot);
  const objectIndex = correspondenceProjection
    && correspondenceProjection.objectIndex
    && typeof correspondenceProjection.objectIndex === "object"
      ? correspondenceProjection.objectIndex
      : {};

  const orderedModules = collected.modules
    .map((item) => {
      const moduleId = asText(item.module_id);
      const parsed = parseModuleId(moduleId);
      if (!parsed) {
        return null;
      }
      return {
        raw: item,
        moduleId,
        ...parsed,
      };
    })
    .filter(Boolean)
    .sort((left, right) => {
      if (!left || !right) {
        return 0;
      }
      if (left.frameworkName !== right.frameworkName) {
        return left.frameworkName.localeCompare(right.frameworkName);
      }
      if (left.level !== right.level) {
        return left.level - right.level;
      }
      return left.module - right.module;
    });

  /** @type {RuntimeTreeNode[]} */
  const nodes = [];
  /** @type {RuntimeTreeEdge[]} */
  const edges = [];
  /** @type {Map<string, Map<number, number>>} */
  const frameworkCounts = new Map();
  /** @type {Record<string, number>} */
  const relationCounts = {};

  for (const item of orderedModules) {
    if (!item) {
      continue;
    }
    const moduleSource = sourceRefInfo(item.raw.source_ref);
    const exportSource = sourceRefInfo(item.raw.export_surface && typeof item.raw.export_surface === "object"
      ? item.raw.export_surface.source_ref
      : null);
    const sourceFile = moduleSource.filePath || exportSource.filePath || workspaceGuard.normalizeRelPath(asText(item.raw.framework_file));
    const docLine = moduleSource.line || exportSource.line || 1;
    const sourceLine = exportSource.line || moduleSource.line || 1;
    const title = asText(item.raw.title_cn) || asText(item.raw.title_en) || item.moduleId;
    const moduleObject = objectIndex && typeof objectIndex === "object"
      ? objectIndex[item.moduleId]
      : null;
    const moduleTreeEntry = correspondenceProjection?.treeEntriesByModuleId.get(item.moduleId) || null;
    const defaultTarget = correspondenceRuntime.resolvePrimaryNavigationTarget(moduleObject);
    const editTarget = correspondenceRuntime.resolvePrimaryEditTarget(moduleObject);
    const secondaryTargets = correspondenceRuntime.resolveSecondaryTargets(moduleObject);
    const relatedObjectIds = flattenModuleRelatedObjectIds(moduleTreeEntry);
    const capabilities = hoverItems(
      Array.isArray(item.raw.capabilities) ? item.raw.capabilities : [],
      "capability_id",
      (entry) => {
        const name = asText(entry.name);
        const statement = asText(entry.statement);
        return [name, statement].filter(Boolean).join("：");
      }
    );
    const bases = hoverItems(
      Array.isArray(item.raw.bases) ? item.raw.bases : [],
      "base_id",
      (entry) => {
        const name = asText(entry.name);
        const statement = asText(entry.statement);
        return [name, statement].filter(Boolean).join("：");
      }
    );

    if (!frameworkCounts.has(item.frameworkName)) {
      frameworkCounts.set(item.frameworkName, new Map());
    }
    const levelCounts = frameworkCounts.get(item.frameworkName);
    if (levelCounts) {
      levelCounts.set(item.level, (levelCounts.get(item.level) || 0) + 1);
    }

    nodes.push({
      id: item.moduleId,
      label: `L${item.level}.${item.frameworkName}.M${item.module}`,
      detail: title,
      file: sourceFile,
      line: docLine,
      depth: item.level,
      kind: "framework_module",
      group: item.frameworkName,
      order: item.module,
      title,
      moduleName: item.frameworkName,
      moduleRef: `L${item.level}.M${item.module}`,
      sourceLine,
      docLine,
      hoverKicker: "Framework Module",
      capabilityItems: capabilities,
      baseItems: bases,
      ...(moduleObject ? {
        objectId: moduleObject.object_id,
        defaultTarget,
        editTarget,
        correspondenceAnchor: moduleObject.correspondence_anchor || null,
        implementationAnchor: moduleObject.implementation_anchor || null,
        secondaryTargets,
        relatedObjectIds,
      } : {}),
    });

    const exportSurface = item.raw.export_surface && typeof item.raw.export_surface === "object"
      ? item.raw.export_surface
      : {};
    const upstreamIds = Array.isArray(exportSurface.upstream_module_ids)
      ? exportSurface.upstream_module_ids.map((value) => asText(value)).filter(Boolean)
      : [];
    const ruleIds = Array.isArray(exportSurface.rule_ids)
      ? exportSurface.rule_ids.map((value) => asText(value)).filter(Boolean)
      : [];

    for (const upstreamId of upstreamIds) {
      relationCounts.framework_module_growth = (relationCounts.framework_module_growth || 0) + 1;
      edges.push({
        id: `${upstreamId}=>${item.moduleId}`,
        from: upstreamId,
        to: item.moduleId,
        relation: "framework_module_growth",
        rules: ruleIds.join(", "),
        terms: upstreamId,
        file: sourceFile,
        line: sourceLine,
      });
    }
  }

  const nodeIds = new Set(nodes.map((node) => node.id));
  const filteredEdges = edges.filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to));
  const descriptionParts = [
    "Runtime projection from fresh canonical framework modules.",
    "Interactive graph only; no persisted tree artifact.",
  ];
  if (correspondenceProjection) {
    descriptionParts.push("Correspondence protocol is the primary navigation source; legacy canonical fields remain fallback-only.");
  }
  if (collected.staleProjectIds.length) {
    descriptionParts.push(
      `Stale canonical topology is shown for framework authoring (projects: ${collected.staleProjectIds.slice(0, 3).join(", ")}).`
    );
    if (!correspondenceProjection) {
      descriptionParts.push("Cross-layer correspondence targets are temporarily disabled until canonical becomes fresh.");
    }
  }
  if (collected.excludedProjectIds.length) {
    descriptionParts.push(
      `Projects excluded from canonical projection (missing/invalid): ${collected.excludedProjectIds.slice(0, 3).join(", ")}.`
    );
  }

  return {
    title: "Shelf Framework Tree",
    description: descriptionParts.join(" "),
    kind: "framework",
    nodes,
    edges: filteredEdges,
    footText: "Grouped by framework; each panel keeps its own local Lx bands.",
    layoutMode: "framework_columns",
    levelLabels: levelLabelsFor(nodes.map((node) => node.depth)),
    frameworkGroups: frameworkGroupsFromCounts(frameworkCounts),
    relationCounts,
    ...(correspondenceProjection ? {
      objectIndex,
      validationSummary: correspondenceProjection.payload.validation_summary || null,
    } : {}),
  };
}

/**
 * @param {string} repoRoot
 * @returns {{
 *   edges: RuntimeTreeEdge[],
 *   hasCanonicalModules: boolean,
 *   staleProjectIds: string[],
 *   excludedProjectIds: string[],
 * }}
 */
function collectCanonicalGrowthEdges(repoRoot) {
  const collected = collectCanonicalFrameworkModulesForTree(repoRoot);
  /** @type {RuntimeTreeEdge[]} */
  const edges = [];
  const seenEdgeIds = new Set();

  for (const rawModule of collected.modules) {
    if (!rawModule || typeof rawModule !== "object") {
      continue;
    }
    const moduleId = asText(rawModule.module_id);
    if (!moduleId) {
      continue;
    }
    const exportSurface = rawModule.export_surface && typeof rawModule.export_surface === "object"
      ? rawModule.export_surface
      : {};
    const upstreamIds = Array.isArray(exportSurface.upstream_module_ids)
      ? exportSurface.upstream_module_ids.map((value) => asText(value)).filter(Boolean)
      : [];
    if (!upstreamIds.length) {
      continue;
    }
    const sourceInfo = sourceRefInfo(exportSurface.source_ref);
    const sourceFile = sourceInfo.filePath || workspaceGuard.normalizeRelPath(asText(rawModule.framework_file));
    const sourceLine = sourceInfo.line || 1;
    const ruleIds = Array.isArray(exportSurface.rule_ids)
      ? exportSurface.rule_ids.map((value) => asText(value)).filter(Boolean)
      : [];
    for (const upstreamId of upstreamIds) {
      const edgeId = `${upstreamId}=>${moduleId}`;
      if (seenEdgeIds.has(edgeId)) {
        continue;
      }
      seenEdgeIds.add(edgeId);
      edges.push({
        id: edgeId,
        from: upstreamId,
        to: moduleId,
        relation: "framework_module_growth",
        rules: ruleIds.join(", "),
        terms: upstreamId,
        file: sourceFile,
        line: sourceLine,
      });
    }
  }

  return {
    edges,
    hasCanonicalModules: collected.modules.length > 0,
    staleProjectIds: collected.staleProjectIds,
    excludedProjectIds: collected.excludedProjectIds,
  };
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel}
 */
function buildAuthorFallbackFrameworkTreeModel(repoRoot) {
  const frameworkRoot = path.join(repoRoot, "framework");
  if (!fs.existsSync(frameworkRoot) || !fs.statSync(frameworkRoot).isDirectory()) {
    throw new Error("framework/ directory is missing");
  }

  /** @type {RuntimeTreeNode[]} */
  const nodes = [];
  /** @type {RuntimeTreeEdge[]} */
  const edges = [];
  /** @type {Map<string, Map<number, number>>} */
  const frameworkCounts = new Map();
  const relationCounts = {
    module_contains_base: 0,
    base_composition: 0,
    framework_module_growth: 0,
  };
  const edgeIds = new Set();

  const frameworkDirs = fs.readdirSync(frameworkRoot)
    .map((entry) => ({
      name: entry,
      absPath: path.join(frameworkRoot, entry),
    }))
    .filter((entry) => fs.existsSync(entry.absPath) && fs.statSync(entry.absPath).isDirectory())
    .sort((left, right) => left.name.localeCompare(right.name));

  for (const frameworkDir of frameworkDirs) {
    const moduleFiles = fs.readdirSync(frameworkDir.absPath)
      .filter((entry) => entry.endsWith(".md"))
      .sort((left, right) => left.localeCompare(right));

    if (!frameworkCounts.has(frameworkDir.name)) {
      frameworkCounts.set(frameworkDir.name, new Map());
    }
    const levelCounts = frameworkCounts.get(frameworkDir.name);

    for (const fileName of moduleFiles) {
      const parsed = parseModuleFileName(fileName);
      if (!parsed) {
        continue;
      }
      const absPath = path.join(frameworkDir.absPath, fileName);
      const relPath = workspaceGuard.normalizeRelPath(path.relative(repoRoot, absPath));
      const heading = firstMarkdownHeading(absPath);
      const lines = readMarkdownLines(absPath);
      const parsedParts = parseAuthorFrameworkBasesAndRules(lines, frameworkDir.name);

      const moduleDepth = Math.max(0, parsed.level * 2);
      const baseDepth = moduleDepth + 1;
      levelCounts?.set(moduleDepth, (levelCounts?.get(moduleDepth) || 0) + 1);
      const moduleId = `${frameworkDir.name}.L${parsed.level}.M${parsed.module}`;
      nodes.push({
        id: moduleId,
        label: `L${parsed.level}.${frameworkDir.name}.M${parsed.module}`,
        detail: heading.title || fileName,
        file: relPath,
        line: heading.line,
        depth: moduleDepth,
        kind: "framework_module",
        group: frameworkDir.name,
        order: parsed.module,
        title: heading.title || fileName,
        moduleName: frameworkDir.name,
        moduleRef: `L${parsed.level}.M${parsed.module}`,
        sourceLine: heading.line,
        docLine: heading.line,
        hoverKicker: "Framework Module (Author Source)",
        capabilityItems: [],
        baseItems: [],
      });

      const baseById = new Map();
      for (const base of parsedParts.bases) {
        const normalizedBaseId = asText(base.baseId).toUpperCase();
        if (!normalizedBaseId) {
          continue;
        }
        const numericMatch = /B(\d+)/.exec(normalizedBaseId);
        const baseOrder = numericMatch ? asPositiveInt(numericMatch[1], 1) : 1;
        const baseId = baseNodeId(moduleId, normalizedBaseId);
        levelCounts?.set(baseDepth, (levelCounts?.get(baseDepth) || 0) + 1);
        baseById.set(normalizedBaseId, {
          nodeId: baseId,
          upstreamModuleIds: base.upstreamModuleIds,
          line: base.line,
        });
        nodes.push({
          id: baseId,
          label: `${frameworkDir.name}.L${parsed.level}.M${parsed.module}.${normalizedBaseId}`,
          detail: base.detail || normalizedBaseId,
          file: relPath,
          line: base.line,
          depth: baseDepth,
          kind: "framework_base",
          group: frameworkDir.name,
          order: parsed.module * 100 + baseOrder,
          title: normalizedBaseId,
          moduleName: frameworkDir.name,
          moduleRef: `L${parsed.level}.M${parsed.module}`,
          sourceLine: base.line,
          docLine: base.line,
          hoverKicker: "Framework Base",
          capabilityItems: [],
          baseItems: [],
        });

        const containEdgeId = `${moduleId}->${baseId}`;
        if (!edgeIds.has(containEdgeId)) {
          edgeIds.add(containEdgeId);
          edges.push({
            id: containEdgeId,
            from: moduleId,
            to: baseId,
            relation: "module_contains_base",
            file: relPath,
            line: base.line,
            terms: normalizedBaseId,
          });
          relationCounts.module_contains_base += 1;
        }
      }

      for (const [ruleId, baseIds] of parsedParts.ruleBaseRefs.entries()) {
        const resolved = [...new Set(
          [...baseIds]
            .map((baseId) => baseById.get(asText(baseId).toUpperCase())?.nodeId || "")
            .filter(Boolean)
        )].sort();
        for (let left = 0; left < resolved.length; left += 1) {
          for (let right = left + 1; right < resolved.length; right += 1) {
            const from = resolved[left];
            const to = resolved[right];
            const ruleEdgeId = `${moduleId}:${ruleId}:${from}->${to}`;
            if (edgeIds.has(ruleEdgeId)) {
              continue;
            }
            edgeIds.add(ruleEdgeId);
            edges.push({
              id: ruleEdgeId,
              from,
              to,
              relation: "base_composition",
              rules: ruleId,
              terms: `${from} + ${to}`,
              file: relPath,
              line: 1,
            });
            relationCounts.base_composition += 1;
          }
        }
      }

      for (const [baseId, baseInfo] of baseById.entries()) {
        for (const upstreamModuleId of baseInfo.upstreamModuleIds) {
          const growthEdgeId = `${upstreamModuleId}=>${moduleId}`;
          if (edgeIds.has(growthEdgeId)) {
            continue;
          }
          edgeIds.add(growthEdgeId);
          edges.push({
            id: growthEdgeId,
            from: upstreamModuleId,
            to: moduleId,
            relation: "framework_module_growth",
            terms: baseId,
            file: relPath,
            line: baseInfo.line || 1,
          });
          relationCounts.framework_module_growth += 1;
        }
      }
    }
  }

  const nodeIds = new Set(nodes.map((node) => node.id));
  const filteredEdges = edges.filter((edge) => nodeIds.has(edge.from) && nodeIds.has(edge.to));
  const compactRelationCounts = Object.fromEntries(
    Object.entries(relationCounts).filter(([, count]) => count > 0)
  );

  const descriptionParts = [
    "Author graph projection from framework markdown.",
    "Only module/base definitions and base-composition rules are used; no project config selection is required.",
  ];
  descriptionParts.push("Module nodes, base nodes, and rule-level base composition edges are rendered from author source.");

  return {
    title: "Shelf Framework Tree",
    description: descriptionParts.join(" "),
    kind: "framework",
    nodes,
    edges: filteredEdges,
    footText: "Author graph: module -> base containment, base composition, and upstream module references declared in base definitions.",
    layoutMode: "framework_columns",
    levelLabels: authorLevelLabelsFor(nodes.map((node) => node.depth)),
    frameworkGroups: frameworkGroupsFromCounts(frameworkCounts),
    relationCounts: compactRelationCounts,
  };
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel}
 */
function buildRuntimeFrameworkTreeModel(repoRoot) {
  return buildAuthorFallbackFrameworkTreeModel(repoRoot);
}

/**
 * @param {string} repoRoot
 * @returns {RuntimeTreeModel}
 */
function buildRuntimeEvidenceTreeModel(repoRoot) {
  const payload = evidenceTree.readEvidenceTree(repoRoot, "");
  const rawNodes = Array.isArray(payload?.root?.nodes) ? payload.root.nodes : [];
  /** @type {RuntimeTreeNode[]} */
  const nodes = rawNodes
    .filter((node) => node && typeof node === "object")
    .map((node) => {
      const nodeId = asText(node.id);
      const nodeKind = asText(node.node_kind) || "evidence_node";
      const sourceInfo = sourceRefInfo(node.source_ref);
      const sourceFile = sourceInfo.filePath || workspaceGuard.normalizeRelPath(asText(node.source_file));
      return {
        id: nodeId,
        label: asText(node.label) || nodeId || "node",
        detail: asText(node.description) || nodeKind,
        file: sourceFile,
        line: sourceInfo.line || 1,
        depth: Math.max(0, Number(node.level || 0)),
        kind: nodeKind,
        group: nodeKind.split(":")[0] || "evidence",
        title: asText(node.label) || nodeId,
      };
    })
    .filter((node) => node.id)
    .sort((left, right) => {
      if (left.depth !== right.depth) {
        return left.depth - right.depth;
      }
      return left.label.localeCompare(right.label);
    });

  const nodeIds = new Set(nodes.map((node) => node.id));
  const rawEdges = Array.isArray(payload?.root?.edges) ? payload.root.edges : [];
  /** @type {RuntimeTreeEdge[]} */
  const edges = rawEdges
    .filter((edge) => edge && String(edge.relation || "") === "tree_child")
    .map((edge, index) => {
      const sourceInfo = sourceRefInfo(edge.source_ref);
      return {
        id: asText(edge.id) || `${index}:${asText(edge.from)}=>${asText(edge.to)}`,
        from: asText(edge.from),
        to: asText(edge.to),
        relation: "tree_child",
        file: sourceInfo.filePath || workspaceGuard.normalizeRelPath(asText(edge.source_file)),
        line: sourceInfo.line || 1,
      };
    })
    .filter((edge) => edge.from && edge.to && nodeIds.has(edge.from) && nodeIds.has(edge.to));

  return {
    title: "Shelf Evidence Tree",
    description: "Runtime projection from canonical graph. Interactive graph, no persisted tree artifact.",
    kind: "evidence",
    nodes,
    edges,
    footText: "Evidence tree remains canonical-derived and opens only when canonical is fresh.",
    layoutMode: "global_levels",
    levelLabels: levelLabelsFor(nodes.map((node) => node.depth)),
    relationCounts: Object.fromEntries(
      edges.reduce((counts, edge) => {
        counts.set(edge.relation, (counts.get(edge.relation) || 0) + 1);
        return counts;
      }, new Map())
    ),
  };
}

/**
 * @param {string} repoRoot
 * @param {"framework"|"evidence"} kind
 * @returns {RuntimeTreeModel}
 */
function buildRuntimeTreeModel(repoRoot, kind) {
  return kind === "evidence"
    ? buildRuntimeEvidenceTreeModel(repoRoot)
    : buildRuntimeFrameworkTreeModel(repoRoot);
}

module.exports = {
  buildRuntimeEvidenceTreeModel,
  buildRuntimeFrameworkTreeModel,
  buildRuntimeTreeModel,
};

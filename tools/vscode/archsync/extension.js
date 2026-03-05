const cp = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const WATCH_PREFIXES = ["framework/", "specs/", "mapping/", "src/", "docs/"];
const WATCH_FILES = new Set([
  "AGENTS.md",
  "README.md",
  "scripts/validate_strict_mapping.py",
  "scripts/generate_framework_tree_hierarchy.py"
]);

const STANDARDS_TREE_FILE = path.join("specs", "规范总纲与树形结构.md");
const REGISTRY_FILE = path.join("mapping", "mapping_registry.json");
const DEFAULT_FRAMEWORK_TREE_HTML = path.join("docs", "hierarchy", "shelf_framework_tree.html");
const DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND =
  "uv run python scripts/generate_framework_tree_hierarchy.py --registry mapping/mapping_registry.json --output-json docs/hierarchy/shelf_framework_tree.json --output-html docs/hierarchy/shelf_framework_tree.html";
const DEFAULT_FRAMEWORK_SCAFFOLD_SCRIPT = path.join("scripts", "generate_framework_scaffold.py");
const MODULE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
const LEVEL_PATTERN = /^L\d+$/i;
const FRAMEWORK_DIRECTIVE_PREFIX = "@framework";

function activate(context) {
  const output = vscode.window.createOutputChannel("ArchSync");
  const diagnostics = vscode.languages.createDiagnosticCollection("archsync-mapping");
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.text = "$(check) ArchSync idle";
  status.tooltip = "ArchSync";
  status.command = "archSync.showIssues";
  status.backgroundColor = undefined;
  status.color = undefined;
  status.show();

  context.subscriptions.push(output, diagnostics, status);

  let running = false;
  let pending = null;
  let timer = null;
  let lastFailureSignature = "";
  let lastRunIssues = [];
  let lastRepoRoot = "";
  let mappingValidationActive = true;
  let frameworkTreePanel = null;

  const runValidation = async (options = { mode: "change", triggerUri: null, notifyOnFail: false }) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const repoRoot = folder.uri.fsPath;

    if (!hasStandardsTree(repoRoot)) {
      mappingValidationActive = false;
      lastRepoRoot = repoRoot;
      lastRunIssues = [];
      lastFailureSignature = "";
      diagnostics.clear();
      setStatusDisabled(status, repoRoot);
      return;
    }
    mappingValidationActive = true;

    const config = vscode.workspace.getConfiguration("archSync");
    const command = options.mode === "full"
      ? config.get("fullValidationCommand")
      : config.get("changeValidationCommand");

    if (!command || typeof command !== "string") {
      return;
    }

    status.text = "$(sync~spin) ArchSync validating";
    status.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    status.color = new vscode.ThemeColor("statusBarItem.warningForeground");
    output.clear();
    output.appendLine(`[run] ${command}`);

    const execResult = await execCommand(command, repoRoot);
    output.appendLine(execResult.stdout || "");
    output.appendLine(execResult.stderr || "");

    const parsed = parseResult(execResult.stdout, execResult.stderr, execResult.code);
    lastRunIssues = parsed.errors;
    lastRepoRoot = repoRoot;
    applyDiagnostics(parsed, diagnostics, repoRoot, options.triggerUri);
    output.appendLine(`[result] passed=${parsed.passed} errors=${parsed.errors.length}`);

    if (parsed.passed) {
      status.text = "$(check) ArchSync OK";
      status.tooltip = "ArchSync: no mapping issues";
      status.backgroundColor = undefined;
      status.color = undefined;
      lastFailureSignature = "";
    } else {
      status.text = "$(error) ArchSync issues";
      status.tooltip = buildTooltip(parsed.errors);
      status.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
      status.color = new vscode.ThemeColor("statusBarItem.errorForeground");

      const shouldNotify = options.notifyOnFail || config.get("notifyOnAutoFail");
      if (shouldNotify && shouldNotifyFailure(parsed.errors, lastFailureSignature)) {
        lastFailureSignature = signature(parsed.errors);
        const action = await vscode.window.showErrorMessage(
          `ArchSync mapping validation failed (${parsed.errors.length} issue(s)).`,
          "Open Problems",
          "Open Log"
        );
        if (action === "Open Problems") {
          await vscode.commands.executeCommand("workbench.actions.view.problems");
        } else if (action === "Open Log") {
          output.show(true);
        }
      }
    }
  };

  const scheduleValidation = (options) => {
    if (pending) {
      pending = {
        mode: pending.mode === "full" || options.mode === "full" ? "full" : "change",
        triggerUri: options.triggerUri || pending.triggerUri,
        notifyOnFail: pending.notifyOnFail || options.notifyOnFail
      };
    } else {
      pending = options;
    }

    if (timer) {
      clearTimeout(timer);
    }

    timer = setTimeout(async () => {
      if (running || !pending) {
        return;
      }
      running = true;
      const task = pending;
      pending = null;
      try {
        await runValidation(task);
      } finally {
        running = false;
        if (pending) {
          scheduleValidation(pending);
        }
      }
    }, 250);
  };

  const ensureFrameworkTreePanel = () => {
    if (!frameworkTreePanel) {
      frameworkTreePanel = vscode.window.createWebviewPanel(
        "archSyncFrameworkTree",
        "ArchSync · Framework Tree",
        vscode.ViewColumn.Active,
        {
          enableScripts: true,
          retainContextWhenHidden: true
        }
      );
      frameworkTreePanel.onDidDispose(() => {
        frameworkTreePanel = null;
      });
    } else {
      frameworkTreePanel.reveal(vscode.ViewColumn.Active, true);
    }
    return frameworkTreePanel;
  };

  const openFrameworkTree = async (options = { regenerateIfMissing: false }) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("ArchSync: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const config = vscode.workspace.getConfiguration("archSync");
    const htmlPath = resolveFrameworkTreeHtmlPath(repoRoot, config.get("frameworkTreeHtmlPath"));

    if (options.regenerateIfMissing && !fs.existsSync(htmlPath)) {
      const generateCommand = config.get("frameworkTreeGenerateCommand") || DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND;
      await generateFrameworkTree(repoRoot, String(generateCommand), output);
    }

    const panel = ensureFrameworkTreePanel();
    panel.webview.html = buildFrameworkTreeFallbackHtml(
      `Loading ${toWorkspaceRelative(htmlPath, repoRoot)} ...`
    );

    if (!fs.existsSync(htmlPath)) {
      panel.webview.html = buildFrameworkTreeFallbackHtml(
        `Framework tree HTML not found: ${toWorkspaceRelative(htmlPath, repoRoot)}`
      );
      return;
    }

    try {
      panel.webview.html = fs.readFileSync(htmlPath, "utf8");
    } catch (error) {
      panel.webview.html = buildFrameworkTreeFallbackHtml(
        `Failed to read framework tree HTML: ${String(error)}`
      );
    }
  };

  const validateNowDisposable = vscode.commands.registerCommand("archSync.validateNow", async () => {
    scheduleValidation({ mode: "full", triggerUri: null, notifyOnFail: true });
  });

  const showIssuesDisposable = vscode.commands.registerCommand("archSync.showIssues", async () => {
    if (!mappingValidationActive && lastRepoRoot) {
      vscode.window.showInformationMessage(
        `ArchSync mapping guard is disabled: missing ${STANDARDS_TREE_FILE} in this workspace.`
      );
      return;
    }

    if (!lastRunIssues.length) {
      await vscode.commands.executeCommand("workbench.actions.view.problems");
      return;
    }

    if (lastRunIssues.length === 1 && lastRepoRoot) {
      await revealIssue(lastRunIssues[0], lastRepoRoot);
      return;
    }

    const picks = lastRunIssues.map((issue) => {
      const resolved = resolveIssueFile(issue.file, lastRepoRoot);
      const displayPath = resolved ? toWorkspaceRelative(resolved, lastRepoRoot) : "unknown";
      return {
        label: issue.message,
        description: `${displayPath}:${Number(issue.line || 1)}`,
        detail: issue.code ? `[${issue.code}]` : "",
        issue
      };
    });

    const selected = await vscode.window.showQuickPick(picks, {
      title: `ArchSync Mapping Issues (${lastRunIssues.length})`,
      placeHolder: "Select an issue to jump to its location"
    });

    if (selected && lastRepoRoot) {
      await revealIssue(selected.issue, lastRepoRoot);
    }
  });

  const openFrameworkTreeDisposable = vscode.commands.registerCommand("archSync.openFrameworkTree", async () => {
    await openFrameworkTree({ regenerateIfMissing: true });
  });

  const refreshFrameworkTreeDisposable = vscode.commands.registerCommand("archSync.refreshFrameworkTree", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("ArchSync: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const config = vscode.workspace.getConfiguration("archSync");
    const generateCommand = String(
      config.get("frameworkTreeGenerateCommand") || DEFAULT_FRAMEWORK_TREE_GENERATE_COMMAND
    );

    const ok = await generateFrameworkTree(repoRoot, generateCommand, output);
    if (!ok) {
      await vscode.window.showErrorMessage("ArchSync: failed to refresh framework tree.", "Open Log").then((action) => {
        if (action === "Open Log") {
          output.show(true);
        }
      });
      return;
    }

    await openFrameworkTree({ regenerateIfMissing: false });
  });

  const generateFrameworkScaffoldDisposable = vscode.commands.registerCommand("archSync.generateFrameworkScaffold", async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      vscode.window.showWarningMessage("ArchSync: no workspace is open.");
      return;
    }

    const repoRoot = folder.uri.fsPath;
    const editor = vscode.window.activeTextEditor;
    const inferred = inferFrameworkDefaults(editor?.document.uri.fsPath, repoRoot);

    const moduleId = await promptScaffoldValue({
      title: "ArchSync: module id",
      prompt: "Canonical module id used in node ids (Lx.Mmodule.By)",
      value: inferred.module,
      validateInput: (value) => (MODULE_ID_PATTERN.test(value.trim()) ? null : "Use [A-Za-z0-9_-], e.g. frontend")
    });
    if (!moduleId) {
      return;
    }

    const moduleDisplay = await promptScaffoldValue({
      title: "ArchSync: module display name",
      prompt: "Display name shown in markdown title",
      value: inferred.moduleDisplay
    });
    if (!moduleDisplay) {
      return;
    }

    const level = await promptScaffoldValue({
      title: "ArchSync: level",
      prompt: "Layer level, e.g. L4",
      value: inferred.level,
      validateInput: (value) => (LEVEL_PATTERN.test(value.trim()) ? null : "Use L<number>, e.g. L4")
    });
    if (!level) {
      return;
    }

    const title = await promptScaffoldValue({
      title: "ArchSync: layer title",
      prompt: "Markdown title and default filename stem",
      value: inferred.title,
      validateInput: (value) => validateScaffoldTitle(value)
    });
    if (!title) {
      return;
    }

    const subtitle = await promptScaffoldValue({
      title: "ArchSync: goal subtitle",
      prompt: "Short subtitle for Goal section",
      value: "一句话描述该层要解决的问题。"
    });
    if (!subtitle) {
      return;
    }

    const baseCountRaw = await promptScaffoldValue({
      title: "ArchSync: base count",
      prompt: "Placeholder base count when custom bases are not provided",
      value: "3",
      validateInput: (value) => validatePositiveInt(value)
    });
    if (!baseCountRaw) {
      return;
    }
    const baseCount = Number(baseCountRaw.trim());

    const targetOptions = [
      {
        label: "Write current file",
        description: "Overwrite active markdown file",
        value: "current"
      },
      {
        label: "Write default path",
        description: "framework/<module>/<level>/<title>.md",
        value: "default"
      }
    ];
    const targetPick = await vscode.window.showQuickPick(targetOptions, {
      title: "ArchSync: scaffold output",
      placeHolder: "Choose where to write scaffold"
    });
    if (!targetPick) {
      return;
    }

    if (targetPick.value === "current" && !editor) {
      vscode.window.showWarningMessage("ArchSync: no active editor for current-file output.");
      return;
    }

    const args = [
      "run",
      "python",
      DEFAULT_FRAMEWORK_SCAFFOLD_SCRIPT,
      "--module",
      moduleId.trim(),
      "--module-display",
      moduleDisplay.trim(),
      "--level",
      level.trim().toUpperCase(),
      "--title",
      title.trim(),
      "--subtitle",
      subtitle.trim(),
      "--base-count",
      String(baseCount)
    ];

    let outputFilePath = null;
    if (targetPick.value === "current" && editor) {
      const rel = path.relative(repoRoot, editor.document.uri.fsPath).replace(/\\/g, "/");
      args.push("--output", rel, "--overwrite");
      outputFilePath = editor.document.uri.fsPath;
    }

    output.appendLine(`[framework-scaffold] uv ${args.join(" ")}`);
    const result = await execCommandArgs("uv", args, repoRoot);
    output.appendLine(result.stdout || "");
    output.appendLine(result.stderr || "");
    output.appendLine(`[framework-scaffold] exit=${result.code}`);

    if (result.code !== 0) {
      await vscode.window.showErrorMessage(
        "ArchSync: failed to generate framework scaffold.",
        "Open Log"
      ).then((action) => {
        if (action === "Open Log") {
          output.show(true);
        }
      });
      return;
    }

    if (!outputFilePath) {
      const resolvedFromOutput = extractGeneratedPath(result.stdout, repoRoot);
      if (resolvedFromOutput) {
        outputFilePath = resolvedFromOutput;
      }
    }

    if (outputFilePath) {
      try {
        const uri = vscode.Uri.file(outputFilePath);
        const doc = await vscode.workspace.openTextDocument(uri);
        await vscode.window.showTextDocument(doc, { preview: false });
      } catch (error) {
        output.appendLine(`[framework-scaffold] open file failed: ${String(error)}`);
      }
    }

    vscode.window.showInformationMessage("ArchSync: framework scaffold generated.");
  });

  const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    const config = vscode.workspace.getConfiguration("archSync");
    if (!config.get("enableOnSave")) {
      return;
    }

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const rel = path.relative(folder.uri.fsPath, doc.uri.fsPath).replace(/\\/g, "/");
    if (!isWatchedPath(rel)) {
      return;
    }

    scheduleValidation({ mode: "change", triggerUri: doc.uri, notifyOnFail: false });
  });

  const willSaveDisposable = vscode.workspace.onWillSaveTextDocument((event) => {
    const config = vscode.workspace.getConfiguration("archSync");
    if (!config.get("autoExpandFrameworkDirective")) {
      return;
    }

    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const doc = event.document;
    if (doc.languageId !== "markdown") {
      return;
    }

    const relPath = path.relative(folder.uri.fsPath, doc.uri.fsPath).replace(/\\/g, "/");
    if (!relPath.startsWith("framework/")) {
      return;
    }

    const directive = parseFrameworkDirective(doc.getText());
    if (!directive) {
      return;
    }

    event.waitUntil((async () => {
      const defaults = inferFrameworkDefaults(doc.uri.fsPath, folder.uri.fsPath);
      const resolved = resolveFrameworkDirectiveConfig(directive, defaults);
      if (resolved.error) {
        vscode.window.showErrorMessage(`ArchSync: ${resolved.error}`);
        return [];
      }

      const args = [
        "run",
        "python",
        DEFAULT_FRAMEWORK_SCAFFOLD_SCRIPT,
        "--module",
        resolved.module,
        "--module-display",
        resolved.moduleDisplay,
        "--level",
        resolved.level,
        "--title",
        resolved.title,
        "--subtitle",
        resolved.subtitle,
        "--base-count",
        String(resolved.baseCount),
        "--stdout"
      ];

      if (resolved.upstreamLevel) {
        args.push("--upstream-level", resolved.upstreamLevel);
      }

      output.appendLine(`[framework-directive] uv ${args.join(" ")}`);
      const result = await execCommandArgs("uv", args, folder.uri.fsPath);
      output.appendLine(result.stdout || "");
      output.appendLine(result.stderr || "");
      output.appendLine(`[framework-directive] exit=${result.code}`);

      if (result.code !== 0) {
        vscode.window.showErrorMessage(
          "ArchSync: @framework expansion failed. Check ArchSync output log."
        );
        return [];
      }

      const generated = String(result.stdout || "");
      if (!generated.trim()) {
        return [];
      }

      const fullRange = new vscode.Range(
        doc.positionAt(0),
        doc.positionAt(doc.getText().length)
      );
      return [vscode.TextEdit.replace(fullRange, generated)];
    })());
  });

  const createDisposable = vscode.workspace.onDidCreateFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    if (anyWatchedUris(event.files, folder.uri.fsPath)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
    }
  });

  const deleteDisposable = vscode.workspace.onDidDeleteFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    if (anyWatchedUris(event.files, folder.uri.fsPath)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
    }
  });

  const renameDisposable = vscode.workspace.onDidRenameFiles(async (event) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }
    const uris = [];
    for (const item of event.files) {
      uris.push(item.oldUri, item.newUri);
    }
    if (anyWatchedUris(uris, folder.uri.fsPath)) {
      scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
    }
  });

  const focusDisposable = vscode.window.onDidChangeWindowState(async (state) => {
    if (!state.focused) {
      return;
    }
    scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
  });

  const fileWatcherDisposables = [];
  const watcherFolder = vscode.workspace.workspaceFolders?.[0];
  if (watcherFolder) {
    const watcherPatterns = [
      "framework/**",
      "specs/**",
      "mapping/**",
      "src/**",
      "docs/**",
      "AGENTS.md",
      "README.md",
      "scripts/validate_strict_mapping.py",
      "scripts/generate_framework_tree_hierarchy.py"
    ];

    for (const pattern of watcherPatterns) {
      const watcher = vscode.workspace.createFileSystemWatcher(
        new vscode.RelativePattern(watcherFolder, pattern)
      );

      const triggerIfWatched = (uri) => {
        if (isWatchedUri(uri, watcherFolder.uri.fsPath)) {
          scheduleValidation({ mode: "change", triggerUri: uri, notifyOnFail: false });
        }
      };

      watcher.onDidChange(triggerIfWatched);
      watcher.onDidCreate(triggerIfWatched);
      watcher.onDidDelete(triggerIfWatched);
      fileWatcherDisposables.push(watcher);
    }
  }

  context.subscriptions.push(
    validateNowDisposable,
    showIssuesDisposable,
    openFrameworkTreeDisposable,
    refreshFrameworkTreeDisposable,
    generateFrameworkScaffoldDisposable,
    willSaveDisposable,
    saveDisposable,
    createDisposable,
    deleteDisposable,
    renameDisposable,
    focusDisposable,
    ...fileWatcherDisposables
  );

  scheduleValidation({ mode: "change", triggerUri: null, notifyOnFail: false });
}

function deactivate() {}

function isWatchedPath(relPath) {
  if (!relPath || relPath.startsWith("..")) {
    return false;
  }

  if (WATCH_FILES.has(relPath)) {
    return true;
  }

  return WATCH_PREFIXES.some((prefix) => relPath.startsWith(prefix));
}

function anyWatchedUris(uris, workspaceRoot) {
  for (const uri of uris) {
    if (isWatchedUri(uri, workspaceRoot)) {
      return true;
    }
  }
  return false;
}

function isWatchedUri(uri, workspaceRoot) {
  const rel = path.relative(workspaceRoot, uri.fsPath).replace(/\\/g, "/");
  return isWatchedPath(rel);
}

function execCommand(command, cwd) {
  return new Promise((resolve) => {
    cp.exec(command, { cwd, maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
      resolve({
        code: error ? error.code ?? 1 : 0,
        stdout: stdout || "",
        stderr: stderr || ""
      });
    });
  });
}

function execCommandArgs(command, args, cwd) {
  return new Promise((resolve) => {
    cp.execFile(command, args, { cwd, maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
      resolve({
        code: error ? error.code ?? 1 : 0,
        stdout: stdout || "",
        stderr: stderr || ""
      });
    });
  });
}

async function promptScaffoldValue(options) {
  const value = await vscode.window.showInputBox({
    title: options.title,
    prompt: options.prompt,
    value: options.value || "",
    validateInput: options.validateInput
      ? (raw) => {
        const result = options.validateInput(raw);
        return result || undefined;
      }
      : undefined,
    ignoreFocusOut: true
  });

  if (value === undefined) {
    return null;
  }
  const cleaned = value.trim();
  return cleaned || null;
}

function validateScaffoldTitle(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Title cannot be empty.";
  }
  if (trimmed.includes("/") || trimmed.includes("\\")) {
    return "Title cannot contain path separators.";
  }
  return null;
}

function validatePositiveInt(value) {
  const n = Number(value.trim());
  if (!Number.isInteger(n) || n < 1) {
    return "Use integer >= 1.";
  }
  return null;
}

function inferFrameworkDefaults(activeFilePath, repoRoot) {
  const defaults = {
    module: "frontend",
    moduleDisplay: "前端",
    level: "L4",
    title: "状态与数据编排层"
  };

  if (!activeFilePath) {
    return defaults;
  }

  const relPath = path.relative(repoRoot, activeFilePath).replace(/\\/g, "/");
  const match = /^framework\/([^/]+)\/(L\d+)\/([^/]+)\.md$/i.exec(relPath);
  if (!match) {
    return defaults;
  }

  const moduleName = match[1];
  return {
    module: moduleName,
    moduleDisplay: moduleDisplayName(moduleName),
    level: match[2].toUpperCase(),
    title: match[3]
  };
}

function moduleDisplayName(moduleName) {
  const lower = String(moduleName || "").toLowerCase();
  if (lower === "frontend") {
    return "前端";
  }
  if (lower === "shelf") {
    return "置物架";
  }
  if (lower === "curtain") {
    return "窗帘";
  }
  return moduleName;
}

function extractGeneratedPath(stdout, repoRoot) {
  const match = /generated scaffold:\s*([^\n\r]+)/i.exec(String(stdout || ""));
  if (!match) {
    return null;
  }
  const rel = match[1].trim();
  if (!rel) {
    return null;
  }
  return path.join(repoRoot, rel);
}

function parseFrameworkDirective(documentText) {
  const lines = String(documentText || "").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith(FRAMEWORK_DIRECTIVE_PREFIX)) {
      continue;
    }

    const rest = trimmed.slice(FRAMEWORK_DIRECTIVE_PREFIX.length).trim();
    if (!rest) {
      return { params: {}, error: null };
    }

    const params = {};
    const tokenPattern = /([A-Za-z_][A-Za-z0-9_]*)=("([^"\\]|\\.)*"|'([^'\\]|\\.)*'|[^\s;]+)/g;
    let match = null;
    while ((match = tokenPattern.exec(rest)) !== null) {
      const key = match[1];
      const rawValue = match[2];
      params[key] = unquoteDirectiveValue(rawValue);
    }

    if (!Object.keys(params).length) {
      return {
        params: {},
        error: "invalid @framework format. Use: @framework module=frontend level=L4 title=\"状态层\""
      };
    }

    return { params, error: null };
  }

  return null;
}

function unquoteDirectiveValue(rawValue) {
  const value = String(rawValue || "").trim();
  if (
    (value.startsWith("\"") && value.endsWith("\"")) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

function resolveFrameworkDirectiveConfig(directive, defaults) {
  if (directive?.error) {
    return { error: directive.error };
  }

  const params = directive?.params || {};
  const module = String(params.module || defaults.module || "").trim();
  const moduleDisplay = String(
    params.module_display || params.moduleDisplay || defaults.moduleDisplay || moduleDisplayName(module)
  ).trim();
  const level = String(params.level || defaults.level || "").trim().toUpperCase();
  const title = String(params.title || defaults.title || "").trim();
  const subtitle = String(params.subtitle || "一句话描述该层要解决的问题。").trim();
  const baseCountRaw = String(params.base_count || "3").trim();
  const upstreamLevelRaw = params.upstream_level ? String(params.upstream_level).trim().toUpperCase() : "";

  if (!MODULE_ID_PATTERN.test(module)) {
    return { error: "directive module must match [A-Za-z0-9_-], e.g. frontend" };
  }
  if (!LEVEL_PATTERN.test(level)) {
    return { error: "directive level must be L<number>, e.g. L4" };
  }
  if (!title || title.includes("/") || title.includes("\\")) {
    return { error: "directive title is required and cannot contain path separators" };
  }
  if (!moduleDisplay) {
    return { error: "directive module_display cannot be empty" };
  }

  const baseCount = Number(baseCountRaw);
  if (!Number.isInteger(baseCount) || baseCount < 1) {
    return { error: "directive base_count must be integer >= 1" };
  }

  let upstreamLevel = null;
  if (upstreamLevelRaw) {
    if (!LEVEL_PATTERN.test(upstreamLevelRaw)) {
      return { error: "directive upstream_level must be L<number>, e.g. L5" };
    }

    const sourceNum = Number(level.slice(1));
    const upstreamNum = Number(upstreamLevelRaw.slice(1));
    if (upstreamNum !== sourceNum + 1) {
      return { error: `directive upstream_level must be adjacent to ${level}, expected L${sourceNum + 1}` };
    }
    upstreamLevel = upstreamLevelRaw;
  }

  return {
    error: null,
    module,
    moduleDisplay,
    level,
    title,
    subtitle,
    baseCount,
    upstreamLevel
  };
}

async function generateFrameworkTree(repoRoot, command, output) {
  output.appendLine(`[framework-tree] ${command}`);
  const result = await execCommand(command, repoRoot);
  output.appendLine(result.stdout || "");
  output.appendLine(result.stderr || "");
  output.appendLine(`[framework-tree] exit=${result.code}`);
  return result.code === 0;
}

function parseResult(stdout, stderr, code) {
  const text = [stdout, stderr].filter(Boolean).join("\n").trim();

  try {
    const data = JSON.parse(stdout || stderr || "{}");
    if (typeof data.passed === "boolean" && Array.isArray(data.errors)) {
      return {
        passed: data.passed,
        errors: data.errors.map(normalizeIssue)
      };
    }
  } catch (_) {
    // Fallback to text parsing below.
  }

  const errors = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      errors.push(normalizeIssue(trimmed.slice(2)));
    }
  }

  if (!errors.length && code !== 0 && text) {
    errors.push(normalizeIssue(text));
  }

  return {
    passed: code === 0 && errors.length === 0,
    errors
  };
}

function applyDiagnostics(parsed, collection, repoRoot, triggerUri) {
  collection.clear();
  if (parsed.passed) {
    return;
  }

  const grouped = new Map();

  for (const issue of parsed.errors) {
    const candidateTarget = resolveIssueFile(issue.file, repoRoot);
    const target = (candidateTarget && fs.existsSync(candidateTarget))
      ? candidateTarget
      : (triggerUri
        ? triggerUri.fsPath
        : path.join(repoRoot, REGISTRY_FILE));

    if (!grouped.has(target)) {
      grouped.set(target, []);
    }

    const startLine = Math.max(0, Number(issue.line || 1) - 1);
    const startCol = Math.max(0, Number(issue.column || 1) - 1);
    const range = new vscode.Range(startLine, startCol, startLine, startCol + 1);
    const diag = new vscode.Diagnostic(
      range,
      `[archsync] ${issue.message}`,
      vscode.DiagnosticSeverity.Error
    );

    if (issue.code) {
      diag.code = issue.code;
    }

    if (Array.isArray(issue.related) && issue.related.length) {
      const relatedInfo = [];
      for (const rel of issue.related) {
        const relFile = resolveIssueFile(rel.file, repoRoot);
        if (!relFile) {
          continue;
        }
        const relLine = Math.max(0, Number(rel.line || 1) - 1);
        const relCol = Math.max(0, Number(rel.column || 1) - 1);
        const relRange = new vscode.Range(relLine, relCol, relLine, relCol + 1);
        const relMessage = rel.message || "Related location";
        relatedInfo.push(
          new vscode.DiagnosticRelatedInformation(
            new vscode.Location(vscode.Uri.file(relFile), relRange),
            relMessage
          )
        );
      }
      if (relatedInfo.length) {
        diag.relatedInformation = relatedInfo;
      }
    }

    grouped.get(target).push(diag);
  }

  for (const [filePath, diagnostics] of grouped.entries()) {
    collection.set(vscode.Uri.file(filePath), diagnostics);
  }
}

function resolveIssueFile(file, repoRoot) {
  if (!file || typeof file !== "string") {
    return null;
  }
  if (path.isAbsolute(file)) {
    return file;
  }
  return path.join(repoRoot, file);
}

function resolveFrameworkTreeHtmlPath(repoRoot, configuredPath) {
  if (typeof configuredPath !== "string" || !configuredPath.trim()) {
    return path.join(repoRoot, DEFAULT_FRAMEWORK_TREE_HTML);
  }
  if (path.isAbsolute(configuredPath)) {
    return configuredPath;
  }
  return path.join(repoRoot, configuredPath);
}

function toWorkspaceRelative(filePath, repoRoot) {
  const rel = path.relative(repoRoot, filePath).replace(/\\/g, "/");
  return rel.startsWith("..") ? filePath : rel;
}

function buildFrameworkTreeFallbackHtml(message) {
  const escaped = String(message)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ArchSync · Framework Tree</title>
  <style>
    body { font-family: sans-serif; margin: 0; padding: 20px; color: #183249; background: #f2f7fb; }
    .card { max-width: 900px; margin: 0 auto; background: #fff; border: 1px solid #d6e2ec; border-radius: 12px; padding: 18px; }
    h1 { margin: 0 0 10px; font-size: 22px; }
    p { margin: 0; line-height: 1.6; }
    code { background: #edf5fb; padding: 2px 6px; border-radius: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>ArchSync · Framework Tree</h1>
    <p>${escaped}</p>
    <p style="margin-top:10px;">Try command <code>ArchSync: Refresh Framework Tree</code>.</p>
  </div>
</body>
</html>`;
}

async function revealIssue(issue, repoRoot) {
  const candidate = resolveIssueFile(issue.file, repoRoot);
  const target = (candidate && fs.existsSync(candidate))
    ? candidate
    : path.join(repoRoot, REGISTRY_FILE);
  const uri = vscode.Uri.file(target);
  const doc = await vscode.workspace.openTextDocument(uri);
  const line = Math.max(0, Number(issue.line || 1) - 1);
  const col = Math.max(0, Number(issue.column || 1) - 1);
  const safeLine = Math.min(line, Math.max(doc.lineCount - 1, 0));
  const lineText = doc.lineAt(safeLine).text;
  const safeCol = Math.min(col, lineText.length);
  const pos = new vscode.Position(safeLine, safeCol);
  const editor = await vscode.window.showTextDocument(doc, { preview: false });
  editor.selection = new vscode.Selection(pos, pos);
  editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
}

function normalizeIssue(item) {
  if (typeof item === "string") {
    return {
      message: item,
      file: null,
      line: 1,
      column: 1,
      code: "ARCHSYNC_MAPPING",
      related: []
    };
  }

  if (!item || typeof item !== "object") {
    return {
      message: String(item),
      file: null,
      line: 1,
      column: 1,
      code: "ARCHSYNC_MAPPING",
      related: []
    };
  }

  return {
    message: String(item.message || "ArchSync mapping issue"),
    file: item.file || null,
    line: Number(item.line || 1),
    column: Number(item.column || 1),
    code: item.code || "ARCHSYNC_MAPPING",
    related: Array.isArray(item.related) ? item.related : []
  };
}

function signature(errors) {
  return [...errors]
    .map((e) => `${e.file || ""}:${e.line || 1}:${e.message}`)
    .sort()
    .join("||");
}

function shouldNotifyFailure(errors, prevSignature) {
  return signature(errors) !== prevSignature;
}

function buildTooltip(errors) {
  if (!errors.length) {
    return "ArchSync";
  }
  const preview = errors.slice(0, 3).map((e) => `• ${e.message}`).join("\n");
  const more = errors.length > 3 ? `\n... +${errors.length - 3} more` : "";
  return `ArchSync\n${preview}${more}\n(click to open Problems)`;
}

function hasStandardsTree(repoRoot) {
  return fs.existsSync(path.join(repoRoot, STANDARDS_TREE_FILE));
}

function setStatusDisabled(status, repoRoot) {
  status.text = "$(circle-slash) ArchSync n/a";
  status.tooltip = `ArchSync mapping guard disabled: ${toWorkspaceRelative(
    path.join(repoRoot, STANDARDS_TREE_FILE),
    repoRoot
  )} not found`;
  status.backgroundColor = undefined;
  status.color = undefined;
}

module.exports = {
  activate,
  deactivate
};

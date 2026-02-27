const cp = require("child_process");
const path = require("path");
const vscode = require("vscode");

const WATCH_PREFIXES = ["standards/", "src/", "docs/"];
const WATCH_FILES = new Set([
  "AGENTS.md",
  "README.md",
  "scripts/validate_strict_mapping.py"
]);

function activate(context) {
  const output = vscode.window.createOutputChannel("Strict Mapping Guard");
  const diagnostics = vscode.languages.createDiagnosticCollection("strict-mapping");
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.text = "$(check) Mapping idle";
  status.tooltip = "Strict Mapping Guard";
  status.show();

  context.subscriptions.push(output, diagnostics, status);

  const runValidation = async (options = { full: false, triggerUri: null }) => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      return;
    }

    const config = vscode.workspace.getConfiguration("strictMappingGuard");
    const command = options.full
      ? config.get("fullValidationCommand")
      : config.get("changeValidationCommand");

    if (!command || typeof command !== "string") {
      return;
    }

    status.text = "$(sync~spin) Mapping validating";
    output.clear();
    output.appendLine(`[run] ${command}`);

    const execResult = await execCommand(command, folder.uri.fsPath);
    output.appendLine(execResult.stdout || "");
    output.appendLine(execResult.stderr || "");

    const parsed = parseResult(execResult.stdout, execResult.stderr, execResult.code);
    applyDiagnostics(parsed, diagnostics, folder.uri.fsPath, options.triggerUri);

    if (parsed.passed) {
      status.text = "$(check) Mapping OK";
    } else {
      status.text = "$(error) Mapping issues";
      if (options.full) {
        vscode.window.showWarningMessage("Strict mapping validation failed. Check Problems panel.");
      }
    }
  };

  const commandDisposable = vscode.commands.registerCommand("strictMapping.validateNow", async () => {
    await runValidation({ full: true, triggerUri: null });
  });

  const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    const config = vscode.workspace.getConfiguration("strictMappingGuard");
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

    await runValidation({ full: false, triggerUri: doc.uri });
  });

  context.subscriptions.push(commandDisposable, saveDisposable);
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

function parseResult(stdout, stderr, code) {
  const text = [stdout, stderr].filter(Boolean).join("\n").trim();

  try {
    const data = JSON.parse(stdout || stderr || "{}");
    if (typeof data.passed === "boolean" && Array.isArray(data.errors)) {
      return {
        passed: data.passed,
        errors: data.errors
      };
    }
  } catch (_) {
    // Fallback to text parsing below.
  }

  const errors = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      errors.push(trimmed.slice(2));
    }
  }

  if (!errors.length && code !== 0 && text) {
    errors.push(text);
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

  for (const message of parsed.errors) {
    const target = inferTargetFile(message, repoRoot) || (triggerUri ? triggerUri.fsPath : path.join(repoRoot, "standards", "mapping_registry.json"));
    if (!grouped.has(target)) {
      grouped.set(target, []);
    }

    const range = new vscode.Range(0, 0, 0, 1);
    const diag = new vscode.Diagnostic(range, `[strict-mapping] ${message}`, vscode.DiagnosticSeverity.Error);
    grouped.get(target).push(diag);
  }

  for (const [filePath, diagnostics] of grouped.entries()) {
    collection.set(vscode.Uri.file(filePath), diagnostics);
  }
}

function inferTargetFile(message, repoRoot) {
  const fileInMessage = message.match(/in ([\w./-]+\.(md|py|json))/);
  if (fileInMessage) {
    return path.join(repoRoot, fileInMessage[1]);
  }

  const requiredFile = message.match(/missing required file: (.+)$/);
  if (requiredFile) {
    return requiredFile[1];
  }

  return null;
}

module.exports = {
  activate,
  deactivate
};

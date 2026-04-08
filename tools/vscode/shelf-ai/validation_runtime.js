const cp = require("child_process");

const DEFAULT_COMMAND_TIMEOUT_MS = 120 * 1000;

function parseCommandResult(stdout, stderr, code, options = {}) {
  const normalizeIssue = typeof options.normalizeIssue === "function"
    ? options.normalizeIssue
    : (issue) => issue;
  const text = [stdout, stderr].filter(Boolean).join("\n").trim();

  try {
    const data = JSON.parse(stdout || stderr || "{}");
    if (typeof data.passed === "boolean") {
      const rawErrors = Array.isArray(data.errors) ? data.errors : [];
      return {
        passed: data.passed,
        errors: rawErrors.map(normalizeIssue),
      };
    }
  } catch (_) {
    // Fallback to text parsing below.
  }

  if (code === 0 && /\bbootstrap_mode=True\b/.test(text)) {
    return {
      passed: true,
      errors: [],
    };
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
    errors,
  };
}

function execCommand(command, cwd, options = {}) {
  const timeoutMs = Number.isFinite(Number(options.timeoutMs))
    ? Math.max(1, Number(options.timeoutMs))
    : DEFAULT_COMMAND_TIMEOUT_MS;
  const execImpl = typeof options.execImpl === "function" ? options.execImpl : cp.exec;

  return new Promise((resolve) => {
    let child = null;
    child = execImpl(
      command,
      { cwd, maxBuffer: 1024 * 1024, timeout: timeoutMs },
      (error, stdout, stderr) => {
        const timedOut = Boolean(
          error && (
            Boolean(error.killed)
            || String(error.signal || "").toUpperCase() === "SIGTERM"
            || /timed out/i.test(String(error.message || ""))
          )
        );
        const result = {
          code: error ? (typeof error.code === "number" ? error.code : (timedOut ? 124 : 1)) : 0,
          stdout: stdout || "",
          stderr: stderr || "",
          timedOut,
          timeoutMs,
          signal: error ? String(error.signal || "") : "",
        };
        if (typeof options.onExit === "function") {
          options.onExit(child, result);
        }
        resolve(result);
      }
    );
    if (typeof options.onSpawn === "function") {
      options.onSpawn(child);
    }
  });
}

function createActiveCommandTracker(options = {}) {
  const now = typeof options.now === "function" ? options.now : () => Date.now();
  let active = null;

  const trackChild = (label, child) => {
    if (!child || typeof child.kill !== "function") {
      return;
    }
    active = {
      label: String(label || "command"),
      child,
      startedAt: now(),
    };
  };

  const clearChild = (child) => {
    if (!active || active.child !== child) {
      return;
    }
    active = null;
  };

  const snapshot = () => {
    if (!active) {
      return null;
    }
    return {
      label: active.label,
      startedAt: active.startedAt,
      elapsedMs: Math.max(0, now() - active.startedAt),
    };
  };

  const restartIfStale = (thresholdMs) => {
    if (!active) {
      return {
        restarted: false,
        reason: "idle",
      };
    }
    const elapsedMs = Math.max(0, now() - active.startedAt);
    if (!Number.isFinite(Number(thresholdMs)) || elapsedMs < Number(thresholdMs)) {
      return {
        restarted: false,
        reason: "fresh",
        label: active.label,
        elapsedMs,
      };
    }
    try {
      active.child.kill();
      return {
        restarted: true,
        label: active.label,
        elapsedMs,
      };
    } catch (error) {
      return {
        restarted: false,
        reason: "kill_failed",
        label: active.label,
        elapsedMs,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  };

  return {
    trackChild,
    clearChild,
    snapshot,
    restartIfStale,
  };
}

module.exports = {
  DEFAULT_COMMAND_TIMEOUT_MS,
  createActiveCommandTracker,
  execCommand,
  parseCommandResult,
};

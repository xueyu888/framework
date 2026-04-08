const assert = require("assert");
const path = require("path");

const {
  DEFAULT_COMMAND_TIMEOUT_MS,
  createActiveCommandTracker,
  execCommand,
  parseCommandResult,
} = require("./validation_runtime");

async function testExecCommandTimesOut() {
  const result = await execCommand("sleep 2", process.cwd(), { timeoutMs: 50 });
  assert.strictEqual(result.code, 124);
  assert.strictEqual(result.timedOut, true);
  assert.strictEqual(result.timeoutMs, 50);
}

function testParseCommandResultTreatsBootstrapTextAsSuccess() {
  const result = parseCommandResult(
    [
      "[validate] passed=True bootstrap_mode=True project=",
      "- no projects/*/project.toml found; repository remains in bootstrap/no-project mode until a project config exists",
    ].join("\n"),
    "",
    0,
    {
      normalizeIssue(issue) {
        return { message: String(issue) };
      },
    }
  );
  assert.strictEqual(result.passed, true);
  assert.deepStrictEqual(result.errors, []);
}

function testParseCommandResultAcceptsJsonWithoutErrorsArray() {
  const result = parseCommandResult(
    JSON.stringify({
      passed: true,
      bootstrap_mode: true,
      scopes: {},
    }),
    "",
    0,
    {
      normalizeIssue(issue) {
        return { message: String(issue) };
      },
    }
  );
  assert.strictEqual(result.passed, true);
  assert.deepStrictEqual(result.errors, []);
}

function testTrackerRestartsOnlyWhenStale() {
  let now = 10_000;
  let killed = 0;
  const tracker = createActiveCommandTracker({ now: () => now });
  const child = {
    kill() {
      killed += 1;
    },
  };

  tracker.trackChild("validate", child);
  let result = tracker.restartIfStale(20_000);
  assert.strictEqual(result.restarted, false);
  assert.strictEqual(killed, 0);

  now = 40_500;
  result = tracker.restartIfStale(20_000);
  assert.strictEqual(result.restarted, true);
  assert.strictEqual(result.label, "validate");
  assert(result.elapsedMs >= 30_000);
  assert.strictEqual(killed, 1);

  tracker.clearChild(child);
  assert.strictEqual(tracker.snapshot(), null);
}

async function main() {
  assert(DEFAULT_COMMAND_TIMEOUT_MS >= 60_000);
  await testExecCommandTimesOut();
  testTrackerRestartsOnlyWhenStale();
  testParseCommandResultTreatsBootstrapTextAsSuccess();
  testParseCommandResultAcceptsJsonWithoutErrorsArray();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

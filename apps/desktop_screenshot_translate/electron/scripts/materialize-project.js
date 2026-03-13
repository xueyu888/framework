const { spawnSync } = require('node:child_process');
const path = require('node:path');

function resolveRepoRoot() {
  return path.resolve(__dirname, '../../../../');
}

function main() {
  const repoRoot = resolveRepoRoot();
  const env = { ...process.env };

  // Windows frequently shares this repo with a WSL-created `.venv`.
  // Use a dedicated environment directory unless the caller already chose one.
  if (process.platform === 'win32' && !env.UV_PROJECT_ENVIRONMENT) {
    env.UV_PROJECT_ENVIRONMENT = '.venv-win';
  }

  const result = spawnSync(
    'uv',
    [
      'run',
      'python',
      'scripts/materialize_project.py',
      '--project',
      'projects/desktop_screenshot_translate/product_spec.toml',
    ],
    {
      cwd: repoRoot,
      env,
      stdio: 'inherit',
    },
  );

  if (result.error) {
    throw result.error;
  }

  if (typeof result.status === 'number' && result.status !== 0) {
    process.exitCode = result.status;
  }
}

main();

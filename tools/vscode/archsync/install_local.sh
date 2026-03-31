#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
TARGET_SCRIPT="${REPO_ROOT}/tools/vscode/shelf-ai/install_local.sh"

if [[ ! -f "${TARGET_SCRIPT}" ]]; then
  echo "Maintained Shelf AI installer not found: ${TARGET_SCRIPT}" >&2
  exit 1
fi

echo "ArchSync has been renamed to Shelf AI."
echo "Delegating local update to ${TARGET_SCRIPT}..."
exec bash "${TARGET_SCRIPT}"

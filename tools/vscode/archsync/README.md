# ArchSync (Legacy Entry)

ArchSync has been renamed to Shelf AI.

This directory is kept only as a compatibility and migration entry for existing local users who still reach for the old `tools/vscode/archsync/...` path.

## Current Maintained Extension

- Maintained source: `tools/vscode/shelf-ai`
- Current local install/update command: `bash tools/vscode/shelf-ai/install_local.sh`
- Legacy shortcut still supported: `bash tools/vscode/archsync/install_local.sh`

Running the legacy install script now delegates to the maintained Shelf AI installer, which packages and installs the current successor extension.

## Why This Exists

- Git history shows ArchSync was formally renamed to Shelf AI.
- The maintained VSCode workbench, validation flow, tree runtime, evidence views, and governed-task guard now live under `tools/vscode/shelf-ai`.
- New extension changes should target Shelf AI, not the old ArchSync implementation directory.

## If You Need To Update The Extension

Use either of these:

- `bash tools/vscode/shelf-ai/install_local.sh`
- `bash tools/vscode/archsync/install_local.sh`

Both paths now update the maintained Shelf AI extension locally.

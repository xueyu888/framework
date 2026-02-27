# Strict Mapping Guard (VSCode Extension)

## What It Does
- Runs strict mapping validation on save for relevant files.
- Shows validation issues in VSCode Problems panel.
- Provides manual command: `Strict Mapping: Validate Now`.

## Install (Local)
1. Open `tools/vscode/strict-mapping-guard` in VSCode.
2. Press `F5` to launch Extension Development Host.
3. Open the repository in the launched host window.

## Commands
- `Strict Mapping: Validate Now`

## Configuration
- `strictMappingGuard.enableOnSave`
- `strictMappingGuard.changeValidationCommand`
- `strictMappingGuard.fullValidationCommand`

Default commands use the repository validator:
- `uv run python scripts/validate_strict_mapping.py --check-changes --json`
- `uv run python scripts/validate_strict_mapping.py --json`

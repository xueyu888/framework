# Contributing to Shelf

Shelf is a structure-first repository.

The main convergence chain is:

`Framework -> Product Spec -> Implementation Config -> Code -> Evidence`

Contributions should preserve that direction.

## Read This First

- [specs/规范总纲与树形结构.md](./specs/规范总纲与树形结构.md)
- [specs/框架设计核心标准.md](./specs/框架设计核心标准.md)
- [projects/README.md](./projects/README.md)
- [AGENTS.md](./AGENTS.md)

## Environment

Use `uv` for Python dependencies and execution:

```bash
uv sync
bash scripts/install_git_hooks.sh
```

If you work from WSL, run these commands inside WSL. For VS Code workflows, prefer a VS Code window connected to the same WSL workspace.

## Required Checks

Run these before pushing changes that affect standards, scripts, or runtime behavior:

```bash
uv run mypy
uv run python scripts/materialize_project.py
uv run python scripts/validate_strict_mapping.py
uv run python scripts/validate_strict_mapping.py --check-changes
```

## Source-Of-Truth Rules

- Do not manually edit `projects/<project_id>/generated/*`.
- If project behavior changes, update `framework/*.md`, `product_spec.toml`, or `implementation_config.toml` first.
- `Product Spec` defines product truth.
- `Implementation Config` defines one technical realization path.
- Code and generated artifacts must not become the primary source of truth for higher layers.

## Framework Authoring Rules

Framework modules should remain explicit about:

- capability
- boundary
- minimal viable bases
- combination rules
- verification

The repository authoring entrypoint for framework modules is the `@framework` template and the Shelf AI insertion command.

## Project Authoring Rules

Project instance files should keep comments clear and layered:

- `projects/<project_id>/product_spec.toml`
  - explain product truth
- `projects/<project_id>/implementation_config.toml`
  - explain implementation refinement

When practical, prefer detailed Chinese comments over minimal labels.

## Good Contribution Areas

- framework module quality
- project templates and examples
- mapping validation and materialization
- runtime templates
- Shelf AI navigation and validation UX
- public docs and onboarding

## Pull Request Notes

When opening a PR, explain:

- which layer changed
- why the change belongs to that layer
- which validations were run
- whether the change affects generated artifacts

Shelf is not optimized for "quick patch first, structure later".

It is optimized for getting the structure right first and keeping the implementation aligned.

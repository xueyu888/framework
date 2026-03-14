# Changelog

## 0.1.0 - 2026-03-14

- Raised the extension version to `0.1.0` to match the repository-wide architecture rewrite instead of treating it as another `0.0.x` patch.
- Kept the extension aligned with the rewritten mainline:
  `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`.
- Kept project navigation, auto-materialization, generated-artifact guarding, and validation centered on `projects/*/project.toml` and canonical-derived views.
- Clarified the current state in repository docs: the new main skeleton is live, but remaining scene-level runtime aggregation is documented explicitly instead of being overstated as fully removed.

## 0.0.48 - 2026-03-14

- Rebased Shelf AI on the rewritten repository architecture:
  `Framework Markdown -> Package Registry -> Project Config -> Code -> Evidence`.
- Switched project navigation from the removed dual-track config path to unified `projects/*/project.toml`.
- Switched generated-artifact guarding and auto-materialization to discovered `project.toml` files.
- Dropped extension-side dependence on the removed legacy mapping list and old scaffold-project commands.
- Clarified that `projects/*/generated/canonical_graph.json` is the sole machine truth and all governance views are derived from it.

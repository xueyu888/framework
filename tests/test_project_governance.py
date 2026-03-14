from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from project_runtime import discover_framework_driven_projects


class ProjectGovernanceTest(unittest.TestCase):
    def test_project_discovery_prefers_canonical_graph_file_over_schema_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_dir = Path(temp_dir) / "projects"
            project_dir = projects_dir / "legacy_project"
            generated_dir = project_dir / "generated"
            generated_dir.mkdir(parents=True)
            (project_dir / "project.toml").write_text("", encoding="utf-8")
            (generated_dir / "canonical_graph.json").write_text(
                json.dumps(
                    {
                        "schema_version": "legacy-custom-canonical/v1",
                        "project": {
                            "project_id": "legacy_project",
                            "runtime_scene": "package_export_runtime",
                        },
                        "layers": {
                            "framework": {
                                "selection": {
                                    "root_modules": {
                                        "frontend": "framework/frontend/L2-M0-前端框架标准模块.md",
                                    }
                                }
                            },
                            "evidence": {
                                "generated_artifacts": {
                                    "directory": "projects/legacy_project/generated",
                                    "canonical_graph_json": "projects/legacy_project/generated/canonical_graph.json",
                                    "derived_governance_tree_json": "projects/legacy_project/generated/governance_tree.json",
                                }
                            },
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            projects = discover_framework_driven_projects(projects_dir)

        self.assertEqual(len(projects), 1)
        project = projects[0]
        self.assertEqual(project.project_id, "legacy_project")
        self.assertEqual(project.runtime_scene, "package_export_runtime")
        self.assertEqual(
            project.canonical_graph_path,
            (generated_dir / "canonical_graph.json").resolve().as_posix(),
        )
        self.assertEqual(
            project.artifact_contract["derived_governance_tree_json"],
            "governance_tree.json",
        )


if __name__ == "__main__":
    unittest.main()

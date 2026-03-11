from __future__ import annotations

import unittest

from project_runtime import discover_framework_driven_projects
from project_runtime.governance import build_governance_closure
from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    load_knowledge_base_project,
)


class ProjectGovernanceTest(unittest.TestCase):
    def test_discover_framework_driven_projects_reports_registered_projects(self) -> None:
        discovered = discover_framework_driven_projects()
        project_ids = {item.project_id for item in discovered}

        self.assertIn("knowledge_base_basic", project_ids)
        knowledge_base = next(item for item in discovered if item.project_id == "knowledge_base_basic")
        self.assertEqual(knowledge_base.template_id, "knowledge_base_workbench")
        self.assertTrue(knowledge_base.discovery_reasons)
        self.assertIn("framework/knowledge_base/L2-M0-知识库工作台场景模块.md", knowledge_base.framework_refs)
        self.assertIn("governance_tree.json", knowledge_base.artifact_contract)

    def test_build_governance_closure_derives_object_first_strict_zone(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        closure = build_governance_closure(project)
        object_ids = {item.object_id for item in closure.structural_objects}
        strict_zone_files = {item.file for item in closure.strict_zone}
        classifications = {item.classification for item in closure.candidates}

        self.assertIn("kb.runtime.page_routes", object_ids)
        self.assertIn("kb.api.chat_contract", object_ids)
        self.assertIn("knowledge_base_basic.config_effect.backend.transport", object_ids)
        self.assertIn("src/knowledge_base_runtime/app.py", strict_zone_files)
        self.assertIn("src/knowledge_base_runtime/backend.py", strict_zone_files)
        self.assertIn("src/project_runtime/knowledge_base.py", strict_zone_files)
        self.assertIn("src/project_runtime/governance.py", strict_zone_files)
        self.assertIn("governed", classifications)
        self.assertTrue(all(item.status == "satisfied" for item in closure.role_bindings))
        self.assertTrue(all(item.classification in {"governed", "attached", "internal"} for item in closure.candidates))


if __name__ == "__main__":
    unittest.main()

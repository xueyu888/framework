from __future__ import annotations

import unittest

from project_runtime.compiler import compile_project_runtime


PROJECT_FILE = "projects/zz_chunk_tagging_basic/project.toml"


class ChunkTaggingProjectTest(unittest.TestCase):
    def test_chunk_tagging_project_compiles_with_module_scoped_boundaries(self) -> None:
        assembly = compile_project_runtime(PROJECT_FILE)
        self.assertEqual(assembly.metadata.project_id, "chunk_tagging_basic")

        framework_module_ids = tuple(
            module["module_id"]
            for module in assembly.canonical["framework"]["modules"]
            if isinstance(module, dict)
        )
        self.assertEqual(
            framework_module_ids,
            (
                "Chunk_Tagging.L0.M0",
                "Chunk_Tagging.L1.M0",
                "Chunk_Tagging.L1.M1",
                "Chunk_Tagging.L1.M2",
                "Chunk_Tagging.L2.M0",
                "Chunk_Tagging.L2.M1",
                "Chunk_Tagging.L2.M2",
                "Chunk_Tagging.L3.M0",
            ),
        )

        config_modules = {
            module["module_id"]: module
            for module in assembly.canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        l0_bindings = config_modules["Chunk_Tagging.L0.M0"]["compiled_config_export"]["boundary_bindings"]
        l1_bindings = config_modules["Chunk_Tagging.L1.M0"]["compiled_config_export"]["boundary_bindings"]
        l0_p1 = next(item for item in l0_bindings if item["boundary_id"] == "P1")
        l1_p1 = next(item for item in l1_bindings if item["boundary_id"] == "P1")

        self.assertEqual(l0_p1["primary_exact_path"], "exact.Chunk_Tagging.l0_m0.p1")
        self.assertEqual(l1_p1["primary_exact_path"], "exact.Chunk_Tagging.l1_m0.p1")
        self.assertNotEqual(l0_p1["primary_exact_path"], l1_p1["primary_exact_path"])

        failed_scope_ids = {
            scope_id
            for scope_id, summary in assembly.validation_reports.scopes.items()
            if any(not outcome.passed for outcome in summary.rules)
        }
        self.assertEqual(failed_scope_ids, set())


if __name__ == "__main__":
    unittest.main()

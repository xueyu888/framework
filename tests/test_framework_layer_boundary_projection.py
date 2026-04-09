from __future__ import annotations

import unittest

from framework_ir import load_framework_catalog
from project_runtime.framework_layer import load_framework_file_index, resolve_selected_framework_modules
from project_runtime.models import SelectedFrameworkModule


class FrameworkLayerBoundaryProjectionTest(unittest.TestCase):
    def test_unique_boundary_id_keeps_framework_level_path(self) -> None:
        message_queue_module = load_framework_file_index()[
            "framework/message_queue/L0-M0-消息队列抽象结构模块.md"
        ]
        projection = message_queue_module.boundary_projection_map["MESSAGEFORM"]
        self.assertEqual(projection["primary_exact_path"], "exact.message_queue.messageform")
        self.assertEqual(
            projection["primary_communication_path"],
            "communication.message_queue.messageform",
        )

    def test_duplicate_boundary_id_uses_module_scoped_path(self) -> None:
        tag_definition_module = load_framework_file_index()[
            "framework/Chunk_Tagging/L0-M0-标签定义.md"
        ]
        scoring_interface_module = load_framework_file_index()[
            "framework/Chunk_Tagging/L1-M0-匹配程度评分接口.md"
        ]

        tag_projection = tag_definition_module.boundary_projection_map["P1"]
        scoring_projection = scoring_interface_module.boundary_projection_map["P1"]

        self.assertEqual(tag_projection["primary_exact_path"], "exact.Chunk_Tagging.l0_m0.p1")
        self.assertEqual(
            tag_projection["primary_communication_path"],
            "communication.Chunk_Tagging.l0_m0.p1",
        )
        self.assertEqual(
            scoring_projection["primary_exact_path"],
            "exact.Chunk_Tagging.l1_m0.p1",
        )
        self.assertEqual(
            scoring_projection["primary_communication_path"],
            "communication.Chunk_Tagging.l1_m0.p1",
        )
        self.assertNotEqual(
            tag_projection["primary_exact_path"],
            scoring_projection["primary_exact_path"],
        )

    def test_inline_sentence_refs_are_captured_as_upstream_links(self) -> None:
        modules = {
            module.module_id: module
            for module in load_framework_catalog().modules
            if module.framework == "Chunk_Tagging"
        }
        self.assertEqual(
            modules["Chunk_Tagging.L2.M0"].export_surface().upstream_module_ids,
            ("Chunk_Tagging.L1.M0", "Chunk_Tagging.L1.M1"),
        )
        self.assertEqual(
            modules["Chunk_Tagging.L3.M0"].export_surface().upstream_module_ids,
            ("Chunk_Tagging.L2.M0", "Chunk_Tagging.L2.M1", "Chunk_Tagging.L2.M2"),
        )

    def test_root_resolution_collects_transitive_chunk_tagging_dependencies(self) -> None:
        framework_modules, root_module_ids = resolve_selected_framework_modules(
            (
                SelectedFrameworkModule(
                    role="tagging_review_flow",
                    framework_file="framework/Chunk_Tagging/L3-M0-标注审核模块.md",
                ),
            )
        )

        self.assertEqual(root_module_ids["tagging_review_flow"], "Chunk_Tagging.L3.M0")
        self.assertEqual(
            tuple(module.module_id for module in framework_modules),
            (
                "Chunk_Tagging.L0.M0",
                "Chunk_Tagging.L1.M0",
                "Chunk_Tagging.L1.M1",
                "Chunk_Tagging.L2.M0",
                "Chunk_Tagging.L2.M1",
                "Chunk_Tagging.L2.M2",
                "Chunk_Tagging.L3.M0",
            ),
        )


if __name__ == "__main__":
    unittest.main()

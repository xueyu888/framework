from __future__ import annotations

import unittest

from scripts.generate_framework_scaffold import (
    build_framework_scaffold,
    default_base_definitions,
)


class FrameworkScaffoldGeneratorTest(unittest.TestCase):
    def test_non_top_level_contains_layer_base_and_compose_tags(self) -> None:
        scaffold = build_framework_scaffold(
            module="frontend",
            module_display="前端",
            level="L4",
            title="状态与数据编排层",
            subtitle="统一状态、数据与副作用编排。",
            bases=default_base_definitions(2),
        )

        self.assertIn("<!--@layer module=frontend; level=L4-->", scaffold)
        self.assertIn("<!--@base id=B1; name=BASE_1; capability=todo_capability_1-->", scaffold)
        self.assertIn("<!--@compose from=L4.Mfrontend.B1; to=L5.Mfrontend.B1;", scaffold)

    def test_top_level_l7_omits_compose_tag(self) -> None:
        scaffold = build_framework_scaffold(
            module="frontend",
            module_display="前端",
            level="L7",
            title="体验目标与验证层",
            subtitle="定义顶层体验目标。",
            bases=default_base_definitions(1),
        )

        self.assertIn("`L7` 为模块上游根层", scaffold)
        self.assertNotIn("@compose", scaffold)


if __name__ == "__main__":
    unittest.main()

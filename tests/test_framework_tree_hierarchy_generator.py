from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.generate_framework_tree_hierarchy import REPO_ROOT, build_payload_from_framework


class FrameworkTreeHierarchyGeneratorTest(unittest.TestCase):
    def test_only_accepts_lx_mn_filenames(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            module_dir = framework_dir / "frontend"
            module_dir.mkdir(parents=True, exist_ok=True)

            (module_dir / "L0-基础层.md").write_text(
                "\n".join(
                    [
                        "# 基础层:Foundation",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 输入原子：定义输入结构。来源：`C1 + A`。",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Lx-Mn"):
                build_payload_from_framework(framework_dir)

    def test_inline_upstream_expr_generates_edges(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            module_dir = framework_dir / "frontend_login"
            module_dir.mkdir(parents=True, exist_ok=True)

            (module_dir / "L0-M0-输入模块.md").write_text(
                "\n".join(
                    [
                        "# 输入模块:InputModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 输入基：定义输入结构。来源：`C1 + INPUT`。",
                    ]
                ),
                encoding="utf-8",
            )
            (module_dir / "L0-M1-反馈模块.md").write_text(
                "\n".join(
                    [
                        "# 反馈模块:FeedbackModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 反馈基：定义反馈结构。来源：`C1 + FEEDBACK`。",
                    ]
                ),
                encoding="utf-8",
            )
            (module_dir / "L1-M0-登录模块.md").write_text(
                "\n".join(
                    [
                        "# 登录模块:LoginModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 登录闭环基：L0.M0[R1,R2] + L0.M1[R1]。来源：`C1 + FORM`。",
                    ]
                ),
                encoding="utf-8",
            )

            payload, warnings = build_payload_from_framework(framework_dir)
            root = payload["root"]
            labels = {node["label"] for node in root["nodes"]}
            growth_edges = [edge for edge in root["edges"] if edge["relation"] == "framework_module_growth"]
            edge_pairs = {(edge["source_ref"], edge["target_ref"]) for edge in growth_edges}

            self.assertIn("L0.frontend_login.M0", labels)
            self.assertIn("L0.frontend_login.M1", labels)
            self.assertIn("L1.frontend_login.M0", labels)
            self.assertIn(("L0.M0", "L1.M0"), edge_pairs)
            self.assertIn(("L0.M1", "L1.M0"), edge_pairs)
            self.assertEqual([], [w for w in warnings if "upstream source" in w])

    def test_missing_explicit_upstream_refs_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            module_dir = framework_dir / "frontend_login"
            module_dir.mkdir(parents=True, exist_ok=True)

            (module_dir / "L0-M0-输入模块.md").write_text(
                "\n".join(
                    [
                        "# 输入模块:InputModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 输入基：定义输入结构。来源：`C1 + INPUT`。",
                    ]
                ),
                encoding="utf-8",
            )
            (module_dir / "L1-M0-登录模块.md").write_text(
                "\n".join(
                    [
                        "# 登录模块:LoginModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 登录闭环基：定义登录结构。来源：`C1 + FORM`。",
                    ]
                ),
                encoding="utf-8",
            )

            _, warnings = build_payload_from_framework(framework_dir)
            self.assertTrue(any("no explicit upstream module refs" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()

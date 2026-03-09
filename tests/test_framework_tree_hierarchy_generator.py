from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_framework_tree_hierarchy import REPO_ROOT, build_payload_from_framework
from scripts.generate_module_hierarchy_html import load_hierarchy, render_html


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
            module_dir = framework_dir / "knowledge_base"
            module_dir.mkdir(parents=True, exist_ok=True)

            (module_dir / "L0-M0-检索模块.md").write_text(
                "\n".join(
                    [
                        "# 检索模块:SearchModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 检索基：定义检索结构。来源：`C1 + SEARCH`。",
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
            (module_dir / "L1-M0-工作台模块.md").write_text(
                "\n".join(
                    [
                        "# 工作台模块:WorkspaceModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 工作台闭环基：L0.M0[R1,R2] + L0.M1[R1]。来源：`C1 + WORKSPACE`。",
                    ]
                ),
                encoding="utf-8",
            )

            payload, warnings = build_payload_from_framework(framework_dir)
            root = payload["root"]
            labels = {node["label"] for node in root["nodes"]}
            growth_edges = [edge for edge in root["edges"] if edge["relation"] == "framework_module_growth"]
            edge_pairs = {(edge["source_ref"], edge["target_ref"]) for edge in growth_edges}

            self.assertIn("L0.knowledge_base.M0", labels)
            self.assertIn("L0.knowledge_base.M1", labels)
            self.assertIn("L1.knowledge_base.M0", labels)
            self.assertIn(("L0.M0", "L1.M0"), edge_pairs)
            self.assertIn(("L0.M1", "L1.M0"), edge_pairs)
            self.assertEqual([], [w for w in warnings if "upstream source" in w])

    def test_missing_explicit_upstream_refs_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            module_dir = framework_dir / "knowledge_base"
            module_dir.mkdir(parents=True, exist_ok=True)

            (module_dir / "L0-M0-检索模块.md").write_text(
                "\n".join(
                    [
                        "# 检索模块:SearchModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 检索基：定义检索结构。来源：`C1 + SEARCH`。",
                    ]
                ),
                encoding="utf-8",
            )
            (module_dir / "L1-M0-工作台模块.md").write_text(
                "\n".join(
                    [
                        "# 工作台模块:WorkspaceModule",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 工作台闭环基：定义工作台结构。来源：`C1 + WORKSPACE`。",
                    ]
                ),
                encoding="utf-8",
            )

            _, warnings = build_payload_from_framework(framework_dir)
            self.assertTrue(any("no explicit upstream module refs" in warning for warning in warnings))

    def test_cross_framework_foundation_ref_generates_edge(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            frontend_dir = framework_dir / "frontend"
            knowledge_dir = framework_dir / "knowledge_base"
            frontend_dir.mkdir(parents=True, exist_ok=True)
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            (frontend_dir / "L1-M0-按钮原子模块.md").write_text(
                "\n".join(
                    [
                        "# 按钮原子模块:ButtonAtoms",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 按钮外壳结构基：由内容槽位构成。来源：`C1 + BUTTON`。",
                    ]
                ),
                encoding="utf-8",
            )
            (knowledge_dir / "L0-M0-文件库原子模块.md").write_text(
                "\n".join(
                    [
                        "# 文件库原子模块:FileLibraryAtoms",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 文件目录结构基：frontend.L1.M0[R1]。来源：`C1 + FILESET`。",
                    ]
                ),
                encoding="utf-8",
            )

            payload, warnings = build_payload_from_framework(framework_dir)
            root = payload["root"]
            growth_edges = [edge for edge in root["edges"] if edge["relation"] == "framework_module_growth"]
            edge_pairs = {(edge["source_ref"], edge["target_ref"]) for edge in growth_edges}

            self.assertIn(("frontend.L1.M0", "L0.M0"), edge_pairs)
            self.assertEqual([], [w for w in warnings if "foundation ref ignored" in w])

    def test_rendered_html_contains_framework_group_controls(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            frontend_dir = framework_dir / "frontend"
            knowledge_dir = framework_dir / "knowledge_base"
            frontend_dir.mkdir(parents=True, exist_ok=True)
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            (frontend_dir / "L0-M0-承载原子模块.md").write_text(
                "\n".join(
                    [
                        "# 承载原子模块:SurfaceAtoms",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 承载基：定义界面承载结构。来源：`C1 + SURFACE`。",
                    ]
                ),
                encoding="utf-8",
            )
            (knowledge_dir / "L0-M0-知识库原子模块.md").write_text(
                "\n".join(
                    [
                        "# 知识库原子模块:KnowledgeAtoms",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 知识库入口基：frontend.L0.M0[R1]。来源：`C1 + LIBRARY`。",
                    ]
                ),
                encoding="utf-8",
            )

            payload, _ = build_payload_from_framework(framework_dir)
            json_path = Path(tmp_dir) / "tree.json"
            html_path = Path(tmp_dir) / "tree.html"
            json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            graph = load_hierarchy(json_path)
            render_html(graph, html_path)
            html = html_path.read_text(encoding="utf-8")

            self.assertIn('id="resetLayoutButton"', html)
            self.assertIn("恢复布局", html)
            self.assertIn("data-framework-toggle", html)
            self.assertIn("data-framework-handle", html)
            self.assertIn("data-pan-ignore", html)
            self.assertIn("左键拖动画布", html)
            self.assertIn("[data-node-hit='1']", html)
            self.assertIn("[data-edge-hit='1']", html)
            self.assertIn('markerWidth="14"', html)
            self.assertIn("stroke-width: 2.15;", html)

    def test_rendered_html_preserves_interaction_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp_dir:
            framework_dir = Path(tmp_dir) / "framework"
            frontend_dir = framework_dir / "frontend"
            knowledge_dir = framework_dir / "knowledge_base"
            frontend_dir.mkdir(parents=True, exist_ok=True)
            knowledge_dir.mkdir(parents=True, exist_ok=True)

            (frontend_dir / "L0-M0-承载原子模块.md").write_text(
                "\n".join(
                    [
                        "# 承载原子模块:SurfaceAtoms",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 承载基：定义界面承载结构。来源：`C1 + SURFACE`。",
                    ]
                ),
                encoding="utf-8",
            )
            (knowledge_dir / "L0-M0-知识库原子模块.md").write_text(
                "\n".join(
                    [
                        "# 知识库原子模块:KnowledgeAtoms",
                        "@framework",
                        "## 3. 最小可行基（Minimum Viable Bases）",
                        "- `B1` 知识库入口基：frontend.L0.M0[R1]。来源：`C1 + LIBRARY`。",
                    ]
                ),
                encoding="utf-8",
            )

            payload, _ = build_payload_from_framework(framework_dir)
            json_path = Path(tmp_dir) / "tree.json"
            html_path = Path(tmp_dir) / "tree.html"
            json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            graph = load_hierarchy(json_path)
            render_html(graph, html_path)
            html = html_path.read_text(encoding="utf-8")

            self.assertIn("Interaction contract:", html)
            self.assertIn("background drag pans the canvas", html)
            self.assertIn("node / edge click keeps relationship selection working", html)
            self.assertIn("graphScrollEl.addEventListener(\"pointerdown\", beginPan);", html)
            self.assertIn("selectNode(node.id);", html)
            self.assertIn("selectEdge(edgeKey);", html)
            self.assertIn("data-pan-ignore", html)
            self.assertIn("[data-node-hit='1']", html)
            self.assertIn("[data-node-group='1']", html)
            self.assertIn("[data-edge-hit='1']", html)


if __name__ == "__main__":
    unittest.main()

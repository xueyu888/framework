from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from fastapi.testclient import TestClient

from project_runtime.app_factory import build_project_app
from project_runtime.knowledge_base import DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE, load_knowledge_base_project


class ProjectRuntimeTest(unittest.TestCase):
    def test_load_default_project_config(self) -> None:
        config = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE)

        self.assertEqual(config.metadata.project_id, "knowledge_base_basic")
        self.assertEqual(config.metadata.template, "knowledge_base_workbench")
        self.assertEqual(config.route_boundary_values.workbench, "/knowledge-base")
        self.assertEqual(config.route_boundary_values.api_prefix, "/api/knowledge")
        self.assertEqual(len(config.scenes), 4)
        self.assertEqual(len(config.seed_articles), 3)

    def test_generic_project_app_factory_uses_project_config(self) -> None:
        client = TestClient(build_project_app(DEFAULT_KNOWLEDGE_BASE_PROJECT_FILE))

        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project"]["project"]["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["frontend"], "/knowledge-base")
        self.assertEqual(payload["workspace_flow"], "/api/knowledge/workspace-flow")

    def test_custom_project_config_changes_routes_and_write_surface(self) -> None:
        project_toml = textwrap.dedent(
            """
            [project]
            project_id = "knowledge_base_public"
            template = "knowledge_base_workbench"
            display_name = "Knowledge Base Public"
            description = "Published-only knowledge base workbench."
            version = "0.1.0"

            [framework_refs]
            frontend = "framework/frontend/L2-M0-前端框架标准模块.md"
            workspace = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
            backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"

            [composition_profile]
            surface = "single_page_workbench"
            detail_flow = "read_panel"
            write_flow = "compose_panel"
            supports_edit = false
            supports_draft = false

            [boundary_values.routes]
            home = "/"
            workbench = "/public-knowledge"
            api_prefix = "/api/public-knowledge"
            workspace_flow = "/api/public-knowledge/workspace-flow"

            [boundary_values.frontend]
            page_title = "Public Knowledge Base"
            hero_kicker = "Published-only project"
            hero_title = "Public Knowledge Base"
            hero_copy = "A published-only knowledge surface instantiated from project configuration."
            contract_title = "Workbench Contract"
            contract_value = "List + Detail + Publish"
            contract_meta = "Published articles only, with no edit route and no draft button."
            boundary_title = "Project Boundary"
            boundary_meta = "Routes, statuses, and write surface are all fixed by the project instance."
            search_title = "Search"
            read_title = "Read"
            compose_title = "Compose"
            query_button_label = "Query"
            reset_button_label = "Reset"
            save_draft_label = "Save Draft"
            publish_label = "Publish"
            clear_label = "Clear"
            edit_label = "Edit in Compose"
            keyword_placeholder = "Search title, summary, or body"
            title_placeholder = "Write a focused title"
            summary_placeholder = "Capture the problem and the conclusion"
            body_placeholder = "Write the reusable explanation or procedure"
            tags_placeholder = "comma,separated,tags"
            list_empty_title = "No results"
            list_empty_description = "Adjust filters or create a new article."
            list_error_title = "List unavailable"
            list_error_description = "The article list could not be loaded."
            detail_empty_title = "Knowledge detail will appear here."
            detail_empty_description = "Choose a result card to inspect title, metadata, body, and related articles."
            detail_no_selection_title = "Nothing selected"
            detail_no_selection_description = "The current query returned no readable article."

            [constraint_profile.backend]
            default_page_size = 8
            max_page_size = 12
            max_tags_per_article = 4
            min_title_length = 3
            max_title_length = 80
            min_summary_length = 10
            max_summary_length = 180
            min_body_length = 30
            max_body_length = 2000
            allowed_statuses = ["published"]

            [[scenes]]
            scene_id = "browse"
            title = "Browse"
            steps = ["open workspace", "apply filters", "scan list", "select article"]
            entry_path = "/public-knowledge"
            return_path = "/public-knowledge"

            [[scenes]]
            scene_id = "read"
            title = "Read"
            steps = ["load detail", "inspect related articles", "return to list"]
            entry_path = "/public-knowledge?focus=detail&slug=public-guidance"
            return_path = "/public-knowledge"

            [[scenes]]
            scene_id = "write"
            title = "Write"
            steps = ["open compose panel", "fill title and summary", "publish"]
            entry_path = "/public-knowledge?mode=create"
            return_path = "/public-knowledge"

            [[seed_articles]]
            slug = "public-guidance"
            title = "Public guidance"
            summary = "Explain how a published-only project instance changes the generated surface."
            body = "A published-only project keeps one workbench but removes draft and edit branches from the write surface."
            tags = ["public", "project"]
            status = "published"
            updated_at = "2026-03-07"
            related_slugs = []
            """
        ).strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_file = Path(temp_dir) / "project.toml"
            project_file.write_text(project_toml, encoding="utf-8")

            config = load_knowledge_base_project(project_file)
            self.assertEqual(config.backend_constraint_profile.allowed_statuses, ("published",))
            self.assertFalse(config.composition_profile.supports_edit)
            self.assertFalse(config.composition_profile.supports_draft)

            client = TestClient(build_project_app(project_file))

            root_response = client.get("/")
            self.assertEqual(root_response.status_code, 200)
            root_payload = root_response.json()
            self.assertEqual(root_payload["frontend"], "/public-knowledge")
            self.assertEqual(root_payload["workspace_flow"], "/api/public-knowledge/workspace-flow")

            page_response = client.get("/public-knowledge")
            self.assertEqual(page_response.status_code, 200)
            self.assertIn("Public Knowledge Base", page_response.text)
            self.assertNotIn('data-status="draft"', page_response.text)

            create_response = client.post(
                "/api/public-knowledge/articles",
                json={
                    "title": "Project constrained publish flow",
                    "summary": "Show how a published-only project defaults write status without draft support.",
                    "body": "A project instance should be able to remove draft support while keeping the same framework template and route structure.",
                    "tags": ["project", "publish"],
                },
            )
            self.assertEqual(create_response.status_code, 201)
            created = create_response.json()
            self.assertEqual(created["status"], "published")

            update_response = client.put(
                "/api/public-knowledge/articles/public-guidance",
                json={
                    "title": "Public guidance",
                    "summary": "This project instance should not expose update routes.",
                    "body": "The edit route is disabled when supports_edit is false.",
                    "tags": ["public"],
                    "status": "published",
                },
            )
            self.assertEqual(update_response.status_code, 405)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from datetime import date
import unittest

from fastapi.testclient import TestClient

from knowledge_base_demo.app import build_knowledge_base_demo_app


class KnowledgeBaseDemoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(build_knowledge_base_demo_app())

    def test_frontend_page_contains_workbench_regions(self) -> None:
        response = self.client.get("/knowledge-base")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Knowledge Base Workbench", response.text)
        self.assertIn("Search", response.text)
        self.assertIn("Read", response.text)
        self.assertIn("Compose", response.text)

    def test_root_exposes_project_summary(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project"]["project"]["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["frontend"], "/knowledge-base")

    def test_list_articles_supports_filtering(self) -> None:
        response = self.client.get("/api/knowledge/articles", params={"tag": "framework"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload["total"], 1)
        self.assertTrue(all("framework" in item["tags"] for item in payload["items"]))

    def test_get_article_detail(self) -> None:
        response = self.client.get("/api/knowledge/articles/framework-language-for-ai-coding")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "framework-language-for-ai-coding")
        self.assertIn("stable workbench contract", payload["body"])

    def test_create_article_round_trip(self) -> None:
        create_response = self.client.post(
            "/api/knowledge/articles",
            json={
                "title": "Natural language code review checklist",
                "summary": "Capture how framework clauses become review checkpoints before shipping.",
                "body": (
                    "A stable review checklist starts from capability, boundary, base, combination, and "
                    "verification clauses. Each generated file should map back to one or more of them."
                ),
                "tags": ["review", "framework"],
                "status": "draft",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created = create_response.json()
        self.assertEqual(created["status"], "draft")
        self.assertEqual(created["updated_at"], date.today().isoformat())

        list_response = self.client.get("/api/knowledge/articles", params={"keyword": "review checklist"})
        self.assertEqual(list_response.status_code, 200)
        payload = list_response.json()
        self.assertGreaterEqual(payload["total"], 1)
        self.assertTrue(any(item["slug"] == created["slug"] for item in payload["items"]))

    def test_update_article_round_trip(self) -> None:
        update_response = self.client.put(
            "/api/knowledge/articles/framework-language-for-ai-coding",
            json={
                "title": "Framework language for AI coding",
                "summary": "Update the contract notes after validating the generated workbench.",
                "body": (
                    "A stable workbench contract needs create and update paths. The edit flow should reuse "
                    "the same list, detail, and write result surface without introducing a second protocol."
                ),
                "tags": ["framework", "ai", "editing"],
                "status": "published",
            },
        )
        self.assertEqual(update_response.status_code, 200)
        updated = update_response.json()
        self.assertEqual(updated["slug"], "framework-language-for-ai-coding")
        self.assertIn("editing", updated["tags"])
        self.assertEqual(updated["updated_at"], date.today().isoformat())

        detail_response = self.client.get("/api/knowledge/articles/framework-language-for-ai-coding")
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json()
        self.assertEqual(
            detail["summary"],
            "Update the contract notes after validating the generated workbench.",
        )

    def test_workspace_flow_exposes_verification_evidence(self) -> None:
        response = self.client.get("/api/knowledge/workspace-flow")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project"]["project"]["project_id"], "knowledge_base_basic")
        self.assertEqual(len(payload["scenes"]), 4)
        self.assertTrue(payload["frontend_verification"]["passed"])
        self.assertTrue(payload["workspace_verification"]["passed"])
        self.assertTrue(payload["backend_verification"]["passed"])


if __name__ == "__main__":
    unittest.main()

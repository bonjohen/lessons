"""Tests for GitHub discovery with mocked responses."""

import json
import logging
import subprocess
import time
from unittest.mock import MagicMock, patch

import httpx

from app.discovery.candidate_scorer import score_candidate
from app.discovery.lesson_extractor import (
    detect_extractable_content,
    generate_candidate_lesson,
)
from app.discovery.repo_intake import build_candidate_record, save_candidate_repo
from app.discovery.todo_writer import create_todo, list_todos

MOCK_REPO = {
    "github_url": "https://github.com/example/project",
    "full_name": "example/project",
    "owner": "example",
    "repo_name": "project",
    "description": "A terraform deployment pipeline with Azure Container Apps",
    "primary_language": "Python",
    "stars": 42,
    "last_updated": "2026-04-01T00:00:00Z",
    "license": "MIT",
    "clone_url": "https://github.com/example/project.git",
    "topics": ["terraform", "deployment", "azure"],
    "has_wiki": True,
}

MOCK_GAP = {
    "gap_id": "gap_test123",
    "status": "open",
    "trigger_query": "Azure deployment lessons",
    "normalized_topic": "azure deployment",
    "missing_concepts": ["azure", "deployment", "container"],
}


class TestCandidateScorer:
    def test_scores_relevant_repo(self):
        score, reasons = score_candidate(MOCK_REPO, MOCK_GAP)
        assert score > 0
        assert len(reasons) > 0

    def test_higher_score_for_matching_topics(self):
        relevant = {**MOCK_REPO, "topics": ["azure", "deployment", "lessons-learned"]}
        irrelevant = {**MOCK_REPO, "description": "unrelated", "topics": [], "stars": 0, "license": ""}
        score1, _ = score_candidate(relevant, MOCK_GAP)
        score2, _ = score_candidate(irrelevant, MOCK_GAP)
        assert score1 > score2

    def test_license_adds_score(self):
        with_license = {**MOCK_REPO, "license": "MIT"}
        without_license = {**MOCK_REPO, "license": ""}
        s1, _ = score_candidate(with_license, MOCK_GAP)
        s2, _ = score_candidate(without_license, MOCK_GAP)
        assert s1 > s2

    def test_score_capped_at_one(self):
        super_repo = {
            **MOCK_REPO,
            "stars": 10000,
            "topics": ["azure", "deployment", "terraform", "lessons-learned", "github-actions", "documentation"],
            "has_wiki": True,
        }
        score, _ = score_candidate(super_repo, MOCK_GAP)
        assert score <= 1.0

    def test_empty_repo_scores_zero(self):
        score, reasons = score_candidate({}, {"missing_concepts": []})
        assert score == 0.0
        assert reasons == []

    def test_stars_boundary_100(self):
        repo_100 = {
            **MOCK_REPO,
            "stars": 100,
            "topics": [],
            "description": "",
            "license": "",
            "has_wiki": False,
            "last_updated": "",
        }
        repo_99 = {
            **MOCK_REPO,
            "stars": 99,
            "topics": [],
            "description": "",
            "license": "",
            "has_wiki": False,
            "last_updated": "",
        }
        s100, r100 = score_candidate(repo_100, {"missing_concepts": []})
        s99, r99 = score_candidate(repo_99, {"missing_concepts": []})
        assert s100 > s99
        assert any("100 stars" in r for r in r100)

    def test_recent_activity_bonus(self):
        recent = {
            **MOCK_REPO,
            "last_updated": "2026-01-01",
            "topics": [],
            "description": "",
            "license": "",
            "has_wiki": False,
            "stars": 0,
        }
        old = {
            **MOCK_REPO,
            "last_updated": "2020-01-01",
            "topics": [],
            "description": "",
            "license": "",
            "has_wiki": False,
            "stars": 0,
        }
        s1, _ = score_candidate(recent, {"missing_concepts": []})
        s2, _ = score_candidate(old, {"missing_concepts": []})
        assert s1 > s2


class TestLessonExtractor:
    def test_detect_extractable_content(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project\nSome content", encoding="utf-8")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide", encoding="utf-8")
        (tmp_path / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")

        content = detect_extractable_content(tmp_path)
        assert len(content["docs"]) >= 2  # README + guide
        assert len(content["deploy"]) == 1

    def test_generate_candidate_lesson(self, tmp_path):
        # Setup mock repo dir
        (tmp_path / "README.md").write_text("# Test Project\nA test project for testing.", encoding="utf-8")

        candidate = {**MOCK_REPO, "license": "MIT"}
        content_files = {"docs": [tmp_path / "README.md"], "ci": [], "deploy": [], "architecture": []}

        with patch("app.discovery.lesson_extractor.CANDIDATE_LESSONS_DIR", tmp_path / "candidates"):
            lesson_path = generate_candidate_lesson(tmp_path, candidate, MOCK_GAP, content_files)

        assert lesson_path is not None
        assert lesson_path.exists()

        content = lesson_path.read_text(encoding="utf-8")
        # Check required sections per PDR 8.5
        assert "status: candidate_external" in content
        assert "review_status: needs_review" in content
        assert "coordination_status: owner_not_contacted" in content
        assert "## Attribution and Thanks" in content
        assert "## Coordination TODO" in content
        assert "## Evidence From Project" in content

    def test_attribution_block_present(self, tmp_path):
        (tmp_path / "README.md").write_text("# Repo", encoding="utf-8")
        candidate = {**MOCK_REPO}
        content_files = {"docs": [], "ci": [], "deploy": [], "architecture": []}

        with patch("app.discovery.lesson_extractor.CANDIDATE_LESSONS_DIR", tmp_path / "candidates"):
            lesson_path = generate_candidate_lesson(tmp_path, candidate, MOCK_GAP, content_files)

        content = lesson_path.read_text(encoding="utf-8")
        assert "Thank you to the maintainers" in content
        assert "example/project" in content
        assert "should not be proposed back" in content


class TestTodoWriter:
    def test_create_todo(self, tmp_path):
        with patch("app.discovery.todo_writer.TODOS_PATH", tmp_path / "todos.json"):
            todo = create_todo(MOCK_REPO, "/path/to/lesson.md", gap_id="gap_123")

        assert todo["todo_id"].startswith("todo_")
        assert todo["status"] == "open"
        assert "example/project" in todo["title"]
        assert todo["source_gap_id"] == "gap_123"

    def test_create_todo_deduplicates(self, tmp_path):
        todos_file = tmp_path / "todos.json"
        with patch("app.discovery.todo_writer.TODOS_PATH", todos_file):
            todo1 = create_todo(MOCK_REPO, "/path/to/lesson1.md", gap_id="gap_1")
            todo2 = create_todo(MOCK_REPO, "/path/to/lesson2.md", gap_id="gap_2")

        assert todo1["todo_id"] == todo2["todo_id"]
        with open(todos_file, encoding="utf-8") as f:
            todos = json.load(f)
        assert len(todos) == 1
        assert todos[0]["source_gap_id"] == "gap_2"  # updated, not duplicated

    def test_list_todos(self, tmp_path):
        todos_file = tmp_path / "todos.json"
        todos_file.write_text(json.dumps([{"todo_id": "t1", "title": "Test"}]), encoding="utf-8")
        with patch("app.discovery.todo_writer.TODOS_PATH", todos_file):
            todos = list_todos()
        assert len(todos) == 1

    def test_list_todos_no_file(self, tmp_path):
        with patch("app.discovery.todo_writer.TODOS_PATH", tmp_path / "nonexistent.json"):
            todos = list_todos()
        assert todos == []

    def test_no_git_push_in_discovery_source(self):
        """Verify discovery modules don't shell out to git push or create PRs."""
        import inspect

        from app.discovery import candidate_scorer, lesson_extractor, repo_intake, todo_writer

        for mod in [candidate_scorer, lesson_extractor, repo_intake, todo_writer]:
            source = inspect.getsource(mod)
            assert "git push" not in source, f"{mod.__name__} contains 'git push'"
            assert "git pr" not in source, f"{mod.__name__} contains 'git pr'"


class TestGitHubSearcher:
    def test_http_error_logged_and_returned(self, caplog):
        from app.discovery.github_search import GitHubSearcher

        def mock_get(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "rate limited",
                request=httpx.Request("GET", "https://api.github.com/search/repositories"),
                response=httpx.Response(403),
            )

        searcher = GitHubSearcher(token="fake")
        with patch("app.discovery.github_search.httpx.get", side_effect=mock_get):
            with caplog.at_level(logging.ERROR, logger="app.discovery.github_search"):
                result = searcher.search_repos(["test query"])

        assert "test query" in result["failed_queries"]
        assert len(result["repos"]) == 0
        assert any("GitHub search failed" in r.message for r in caplog.records)

    def test_rate_limit_triggers_sleep(self, caplog):
        from app.discovery.github_search import GitHubSearcher

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {
            "X-RateLimit-Remaining": "1",
            "X-RateLimit-Reset": str(int(time.time()) + 5),
        }
        mock_resp.json.return_value = {"items": []}

        searcher = GitHubSearcher(token="fake")
        with (
            patch("app.discovery.github_search.httpx.get", return_value=mock_resp),
            patch("app.discovery.github_search.time.sleep") as mock_sleep,
            caplog.at_level(logging.WARNING, logger="app.discovery.github_search"),
        ):
            searcher.search_repos(["test query"])

        mock_sleep.assert_called_once()
        assert any("rate limit low" in r.message for r in caplog.records)


class TestCloneTimeout:
    def test_clone_timeout_returns_none(self):
        from app.discovery.repo_intake import clone_or_pull

        with patch("app.discovery.repo_intake.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 60)):
            result = clone_or_pull("owner", "repo", "https://github.com/owner/repo.git")

        assert result is None


class TestRepoIntake:
    def test_build_candidate_record(self):
        record = build_candidate_record(MOCK_REPO, MOCK_GAP, score=0.75, reasons=["topic match"])
        assert record["candidate_repo_id"].startswith("candidate_")
        assert record["gap_id"] == "gap_test123"
        assert record["score"] == 0.75
        assert record["harvest_status"] == "pending"

    def test_save_candidate_repo_creates_file(self, tmp_path):
        repos_file = tmp_path / "candidate-repos.json"
        record = build_candidate_record(MOCK_REPO, MOCK_GAP, score=0.5, reasons=["test"])
        with patch("app.discovery.repo_intake.CANDIDATE_REPOS_PATH", repos_file):
            save_candidate_repo(record)
        with open(repos_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["candidate_repo_id"] == record["candidate_repo_id"]

    def test_save_candidate_repo_deduplicates(self, tmp_path):
        repos_file = tmp_path / "candidate-repos.json"
        record = build_candidate_record(MOCK_REPO, MOCK_GAP, score=0.5, reasons=["first"])
        with patch("app.discovery.repo_intake.CANDIDATE_REPOS_PATH", repos_file):
            save_candidate_repo(record)
            record["score"] = 0.9
            save_candidate_repo(record)
        with open(repos_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["score"] == 0.9

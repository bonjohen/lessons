"""Integration tests for the harvest pipeline."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import production modules
from lesson_core import normalize_tags, make_slug, extract_title


def _write_lesson(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_repo_entry(rid: str = "test-repo") -> dict:
    return {
        "id": rid,
        "name": "Test Repo",
        "owner": "testowner",
        "repo": "testrepo",
        "branch": "main",
        "lessons_path": "docs/lessons",
    }


def _setup_repo_dir(tmp_path: Path, rid: str = "test-repo") -> Path:
    """Create the directory structure that TMP_DIR / rid would have."""
    repo_root = tmp_path / rid
    repo_root.mkdir(parents=True, exist_ok=True)
    return repo_root


class TestParseLesson:
    """Test parse_lesson by importing it from harvest_lessons."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        # Import harvest_lessons and reset its module-level state
        import harvest_lessons
        import lesson_core
        lesson_core.reset_log_stats()
        self.harvest = harvest_lessons
        self.tmp_path = tmp_path

    def test_full_frontmatter(self):
        repo = _make_repo_entry()
        repo_root = _setup_repo_dir(self.tmp_path)
        lessons_dir = repo_root / "docs" / "lessons"
        md = lessons_dir / "my-lesson.md"
        _write_lesson(md, (
            "---\n"
            "title: Full Lesson\n"
            "summary: A complete lesson\n"
            "date: 2025-06-01\n"
            "phase: implementation\n"
            "lesson_type: architecture\n"
            "status: active\n"
            "tags: [python, testing]\n"
            "---\n\n"
            "This is the body of the lesson with enough words to avoid the short content warning easily.\n"
        ))

        with patch.object(self.harvest, 'TMP_DIR', self.tmp_path):
            result = self.harvest.parse_lesson(md, repo)

        assert result is not None
        assert result["id"] == "test-repo-my-lesson"
        assert result["title"] == "Full Lesson"
        assert result["summary"] == "A complete lesson"
        assert result["date"] == "2025-06-01"
        assert result["tags"] == ["python", "testing"]
        assert result["repo_id"] == "test-repo"
        assert "github.com/testowner/testrepo" in result["source_url"]

    def test_minimal_lesson_title_from_h1(self):
        repo = _make_repo_entry()
        repo_root = _setup_repo_dir(self.tmp_path)
        lessons_dir = repo_root / "docs" / "lessons"
        md = lessons_dir / "bare.md"
        _write_lesson(md, "# Heading Title\n\nBody content here with some words.\n")

        with patch.object(self.harvest, 'TMP_DIR', self.tmp_path):
            result = self.harvest.parse_lesson(md, repo)

        assert result is not None
        assert result["title"] == "Heading Title"
        assert result["tags"] == []
        assert result["date"] is None

    def test_empty_content_returns_none(self):
        repo = _make_repo_entry()
        repo_root = _setup_repo_dir(self.tmp_path)
        lessons_dir = repo_root / "docs" / "lessons"
        md = lessons_dir / "empty.md"
        _write_lesson(md, "---\ntitle: Empty\n---\n")

        with patch.object(self.harvest, 'TMP_DIR', self.tmp_path):
            result = self.harvest.parse_lesson(md, repo)

        assert result is None

    def test_subdirectory_slug_includes_path(self):
        repo = _make_repo_entry()
        repo_root = _setup_repo_dir(self.tmp_path)
        lessons_dir = repo_root / "docs" / "lessons"
        md = lessons_dir / "block1" / "index.md"
        _write_lesson(md, "# Block 1 Intro\n\nContent for block one.\n")

        with patch.object(self.harvest, 'TMP_DIR', self.tmp_path):
            result = self.harvest.parse_lesson(md, repo)

        assert result is not None
        assert result["id"] == "test-repo-block1-index"


class TestScanLessons:
    """Test scan_lessons with real filesystem."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        import harvest_lessons
        import lesson_core
        lesson_core.reset_log_stats()
        self.harvest = harvest_lessons
        self.tmp_path = tmp_path

    def test_scans_md_files_recursively(self):
        repo = _make_repo_entry()
        repo_root = _setup_repo_dir(self.tmp_path)
        lessons_dir = repo_root / "docs" / "lessons"
        _write_lesson(lessons_dir / "lesson-a.md", "# A\n\nContent A.\n")
        _write_lesson(lessons_dir / "sub" / "lesson-b.md", "# B\n\nContent B.\n")
        _write_lesson(lessons_dir / "README.md", "# README\n\nShould be excluded.\n")

        with patch.object(self.harvest, 'TMP_DIR', self.tmp_path):
            lessons = self.harvest.scan_lessons(repo, repo_root)

        assert len(lessons) == 2
        ids = {l["id"] for l in lessons}
        assert "test-repo-lesson-a" in ids
        assert "test-repo-sub-lesson-b" in ids

    def test_missing_lessons_dir_produces_error(self):
        repo = _make_repo_entry()
        repo_root = _setup_repo_dir(self.tmp_path)
        # Don't create docs/lessons

        lessons = self.harvest.scan_lessons(repo, repo_root)
        assert lessons == []
        import lesson_core
        assert lesson_core.get_log_stats().errors > 0


class TestGenerateIndexes:
    """Test JSON index generation."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        import harvest_lessons
        import lesson_core
        lesson_core.reset_log_stats()
        self.harvest = harvest_lessons
        self.tmp_path = tmp_path

    def _make_lesson_record(self, lid="test-repo-a", tags=None, phase="impl", lesson_type="arch"):
        return {
            "id": lid, "title": "T", "summary": "S", "repo_id": "test-repo",
            "repo_name": "Test", "repo_owner": "o", "repo_slug": "r",
            "source_path": "a.md", "source_url": "http://x", "project_url": "http://y",
            "date": "2025-01-01", "updated": None, "phase": phase,
            "lesson_type": lesson_type, "status": "active",
            "tags": tags or ["python"], "source_files": [], "related_prs": [],
            "related_issues": [], "related_commits": [], "audience": [],
            "content": "Body.", "word_count": 1, "reading_minutes": 1,
        }

    def test_generates_all_index_files(self):
        gen_dir = self.tmp_path / "generated"
        repos = [{"id": "test-repo", "name": "Test", "owner": "o", "repo": "r",
                  "branch": "main", "lessons_path": "docs/lessons"}]
        lessons = [self._make_lesson_record()]

        with patch.object(self.harvest, 'GENERATED_DIR', gen_dir):
            self.harvest.generate_indexes(lessons, repos)

        for name in ["lessons.json", "repos.json", "tags.json", "phases.json", "lesson_types.json"]:
            path = gen_dir / name
            assert path.exists(), f"Missing {name}"
            data = json.loads(path.read_text(encoding="utf-8"))
            assert isinstance(data, list)

    def test_repos_json_has_lesson_count(self):
        gen_dir = self.tmp_path / "generated"
        repos = [{"id": "test-repo", "name": "Test", "owner": "o", "repo": "r",
                  "branch": "main", "lessons_path": "docs/lessons"}]
        lessons = [self._make_lesson_record("a"), self._make_lesson_record("b")]

        with patch.object(self.harvest, 'GENERATED_DIR', gen_dir):
            self.harvest.generate_indexes(lessons, repos)

        repos_data = json.loads((gen_dir / "repos.json").read_text(encoding="utf-8"))
        assert repos_data[0]["lesson_count"] == 2

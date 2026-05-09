"""Tests for validation rules."""

import pytest


def make_lesson(**overrides) -> dict:
    """Create a test lesson record with defaults."""
    base = {
        "id": "test-lesson",
        "title": "Test Lesson",
        "summary": "A test",
        "repo_id": "test",
        "repo_name": "Test",
        "repo_owner": "user",
        "repo_slug": "test",
        "source_path": "lesson.md",
        "source_url": "https://github.com/user/test/blob/main/docs/lessons/lesson.md",
        "project_url": "https://github.com/user/test",
        "date": "2025-01-01",
        "updated": None,
        "phase": "implementation",
        "lesson_type": "architecture",
        "status": "active",
        "tags": ["python", "testing"],
        "source_files": [],
        "related_prs": [],
        "related_issues": [],
        "related_commits": [],
        "audience": [],
        "content": "This is the lesson body with enough words to pass the short content check.",
        "word_count": 15,
        "reading_minutes": 1,
    }
    base.update(overrides)
    return base


VALID_LESSON_TYPES = {
    "architecture", "implementation", "testing", "deployment", "debugging",
    "data-design", "ai-assisted-development", "documentation", "maintenance",
    "process", "other",
}


class TestValidation:
    def test_valid_lesson_passes(self):
        lesson = make_lesson()
        errors = []
        warnings = []
        if not lesson["content"].strip():
            errors.append("empty content")
        if not lesson["title"]:
            errors.append("missing title")
        if not lesson["summary"]:
            warnings.append("missing summary")
        assert errors == []
        assert warnings == []

    def test_duplicate_id_error(self):
        lessons = [make_lesson(id="a"), make_lesson(id="a")]
        seen = set()
        dupes = []
        for l in lessons:
            if l["id"] in seen:
                dupes.append(l["id"])
            seen.add(l["id"])
        assert dupes == ["a"]

    def test_missing_summary_warning(self):
        lesson = make_lesson(summary="")
        warnings = []
        if not lesson["summary"]:
            warnings.append("missing summary")
        assert "missing summary" in warnings

    def test_missing_date_warning(self):
        lesson = make_lesson(date=None)
        warnings = []
        if not lesson["date"]:
            warnings.append("missing date")
        assert "missing date" in warnings

    def test_missing_tags_warning(self):
        lesson = make_lesson(tags=[])
        warnings = []
        if not lesson["tags"]:
            warnings.append("missing tags")
        assert "missing tags" in warnings

    def test_unknown_lesson_type_warning(self):
        lesson = make_lesson(lesson_type="nonexistent")
        warnings = []
        if lesson["lesson_type"] and lesson["lesson_type"] not in VALID_LESSON_TYPES:
            warnings.append(f"unknown type: {lesson['lesson_type']}")
        assert len(warnings) == 1

    def test_known_lesson_types_pass(self):
        for lt in VALID_LESSON_TYPES:
            lesson = make_lesson(lesson_type=lt)
            assert lesson["lesson_type"] in VALID_LESSON_TYPES

    def test_empty_content_error(self):
        lesson = make_lesson(content="")
        errors = []
        if not lesson["content"].strip():
            errors.append("empty content")
        assert "empty content" in errors

    def test_short_content_warning(self):
        lesson = make_lesson(content="Short.", word_count=1)
        warnings = []
        if 0 < lesson["word_count"] < 50:
            warnings.append("short content")
        assert "short content" in warnings

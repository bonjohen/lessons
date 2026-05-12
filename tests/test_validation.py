"""Tests for validation rules using production code from lesson_core."""

from lesson_core import (
    validate_lesson_record,
    find_duplicate_ids,
    normalize_tags,
    VALID_LESSON_TYPES,
)


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


class TestValidation:
    def test_valid_lesson_passes(self):
        errors, warnings = validate_lesson_record(make_lesson())
        assert errors == []

    def test_empty_content_error(self):
        errors, warnings = validate_lesson_record(make_lesson(content=""))
        assert any("Empty lesson content" in e for e in errors)

    def test_missing_title_error(self):
        errors, warnings = validate_lesson_record(make_lesson(title=""))
        assert any("Missing title" in e for e in errors)

    def test_missing_summary_warning(self):
        errors, warnings = validate_lesson_record(make_lesson(summary=""))
        assert any("Missing summary" in w for w in warnings)

    def test_missing_date_warning(self):
        errors, warnings = validate_lesson_record(make_lesson(date=None))
        assert any("Missing date" in w for w in warnings)

    def test_missing_tags_warning(self):
        errors, warnings = validate_lesson_record(make_lesson(tags=[]))
        assert any("Missing tags" in w for w in warnings)

    def test_unknown_lesson_type_warning(self):
        errors, warnings = validate_lesson_record(
            make_lesson(lesson_type="nonexistent")
        )
        assert any("Unknown lesson_type" in w for w in warnings)

    def test_known_lesson_types_pass(self):
        for lt in VALID_LESSON_TYPES:
            errors, warnings = validate_lesson_record(make_lesson(lesson_type=lt))
            assert not any("lesson_type" in w for w in warnings)

    def test_unknown_status_warning(self):
        errors, warnings = validate_lesson_record(make_lesson(status="bogus"))
        assert any("Unknown status" in w for w in warnings)

    def test_short_content_warning(self):
        errors, warnings = validate_lesson_record(
            make_lesson(content="Short.", word_count=1)
        )
        assert any("Short content" in w for w in warnings)

    def test_duplicate_id_detection(self):
        lessons = [make_lesson(id="a"), make_lesson(id="a")]
        assert find_duplicate_ids(lessons) == ["a"]


class TestNormalizeTags:
    def test_basic(self):
        assert normalize_tags(["Python", "Testing"]) == ["python", "testing"]

    def test_string_input(self):
        assert normalize_tags("python, testing") == ["python", "testing"]

    def test_dedup(self):
        assert normalize_tags(["python", "Python"]) == ["python"]

    def test_none(self):
        assert normalize_tags(None) == []

    def test_empty_list(self):
        assert normalize_tags([]) == []

    def test_spaces_to_hyphens(self):
        result = normalize_tags(["my tag"])
        assert result == ["my-tag"]

    def test_non_string_coercion(self):
        result = normalize_tags([123])
        assert len(result) == 1
        assert result[0] == "123"

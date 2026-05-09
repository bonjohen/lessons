"""Integration tests for the validation script."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


def _make_lesson_record(**overrides):
    base = {
        "id": "test-lesson", "title": "Test", "summary": "S",
        "repo_id": "test", "repo_name": "Test", "repo_owner": "o",
        "repo_slug": "r", "source_path": "a.md", "source_url": "http://x",
        "project_url": "http://y", "date": "2025-01-01", "updated": None,
        "phase": "implementation", "lesson_type": "architecture",
        "status": "active", "tags": ["python"], "source_files": [],
        "related_prs": [], "related_issues": [], "related_commits": [],
        "audience": [], "content": "Body text.", "word_count": 2,
        "reading_minutes": 1,
    }
    base.update(overrides)
    return base


class TestValidateReposYml:
    @pytest.fixture(autouse=True)
    def _setup(self):
        import validate_lessons
        validate_lessons.error_count = 0
        validate_lessons.warning_count = 0
        validate_lessons.info_count = 0
        self.validator = validate_lessons

    def test_valid_repos_yml(self, tmp_path):
        yml = tmp_path / "repos.yml"
        yml.write_text(yaml.dump({"repos": [
            {"id": "test", "name": "T", "owner": "o", "repo": "r",
             "branch": "main", "lessons_path": "docs/lessons"},
        ]}), encoding="utf-8")

        with patch.object(self.validator, 'REPOS_YML', yml):
            result = self.validator.validate_repos_yml()

        assert result is True
        assert self.validator.error_count == 0

    def test_missing_repos_yml(self, tmp_path):
        yml = tmp_path / "nonexistent.yml"

        with patch.object(self.validator, 'REPOS_YML', yml):
            result = self.validator.validate_repos_yml()

        assert result is False
        assert self.validator.error_count > 0

    def test_invalid_repo_id_format(self, tmp_path):
        yml = tmp_path / "repos.yml"
        yml.write_text(yaml.dump({"repos": [
            {"id": "BAD_ID", "name": "T", "owner": "o", "repo": "r",
             "branch": "main", "lessons_path": "docs/lessons"},
        ]}), encoding="utf-8")

        with patch.object(self.validator, 'REPOS_YML', yml):
            self.validator.validate_repos_yml()

        assert self.validator.error_count > 0

    def test_duplicate_repo_ids(self, tmp_path):
        yml = tmp_path / "repos.yml"
        yml.write_text(yaml.dump({"repos": [
            {"id": "dup", "name": "A", "owner": "o", "repo": "r1",
             "branch": "main", "lessons_path": "docs/lessons"},
            {"id": "dup", "name": "B", "owner": "o", "repo": "r2",
             "branch": "main", "lessons_path": "docs/lessons"},
        ]}), encoding="utf-8")

        with patch.object(self.validator, 'REPOS_YML', yml):
            self.validator.validate_repos_yml()

        assert self.validator.error_count > 0


class TestValidateLessons:
    @pytest.fixture(autouse=True)
    def _setup(self):
        import validate_lessons
        validate_lessons.error_count = 0
        validate_lessons.warning_count = 0
        validate_lessons.info_count = 0
        self.validator = validate_lessons

    def test_valid_lessons_no_errors(self):
        lessons = [_make_lesson_record(id="a"), _make_lesson_record(id="b")]
        self.validator.validate_lessons(lessons)
        assert self.validator.error_count == 0

    def test_duplicate_ids_produce_error(self):
        lessons = [_make_lesson_record(id="dup"), _make_lesson_record(id="dup")]
        self.validator.validate_lessons(lessons)
        assert self.validator.error_count > 0

    def test_empty_content_produces_error(self):
        lessons = [_make_lesson_record(content="")]
        self.validator.validate_lessons(lessons)
        assert self.validator.error_count > 0

    def test_missing_summary_produces_warning(self):
        lessons = [_make_lesson_record(summary="")]
        self.validator.validate_lessons(lessons)
        assert self.validator.warning_count > 0

    def test_unknown_lesson_type_produces_warning(self):
        lessons = [_make_lesson_record(lesson_type="bogus")]
        self.validator.validate_lessons(lessons)
        assert self.validator.warning_count > 0


class TestLoadJson:
    @pytest.fixture(autouse=True)
    def _setup(self):
        import validate_lessons
        validate_lessons.error_count = 0
        validate_lessons.warning_count = 0
        validate_lessons.info_count = 0
        self.validator = validate_lessons

    def test_valid_json_array(self, tmp_path):
        gen = tmp_path / "generated"
        gen.mkdir()
        (gen / "test.json").write_text('[{"id": "a"}]', encoding="utf-8")

        with patch.object(self.validator, 'GENERATED_DIR', gen):
            result = self.validator.load_json("test.json")

        assert result == [{"id": "a"}]
        assert self.validator.error_count == 0

    def test_missing_file_produces_error(self, tmp_path):
        gen = tmp_path / "generated"
        gen.mkdir()

        with patch.object(self.validator, 'GENERATED_DIR', gen):
            result = self.validator.load_json("missing.json")

        assert result is None
        assert self.validator.error_count > 0

    def test_invalid_json_produces_error(self, tmp_path):
        gen = tmp_path / "generated"
        gen.mkdir()
        (gen / "bad.json").write_text("{not valid json", encoding="utf-8")

        with patch.object(self.validator, 'GENERATED_DIR', gen):
            result = self.validator.load_json("bad.json")

        assert result is None
        assert self.validator.error_count > 0

"""Tests for lesson frontmatter parsing and title inference."""

import frontmatter

from lesson_core import (
    extract_title,
    coerce_date,
    build_source_url,
    compute_reading_time,
)


class TestTitleExtraction:
    def test_title_from_frontmatter(self, tmp_path):
        md = tmp_path / "lesson.md"
        md.write_text("---\ntitle: My Lesson\n---\n\nBody text.", encoding="utf-8")
        post = frontmatter.load(str(md))
        title, inferred = extract_title(post, md)
        assert title == "My Lesson"
        assert not inferred

    def test_title_from_h1(self, tmp_path):
        md = tmp_path / "lesson.md"
        md.write_text("# Title From Heading\n\nBody text.", encoding="utf-8")
        post = frontmatter.load(str(md))
        title, inferred = extract_title(post, md)
        assert title == "Title From Heading"
        assert not inferred

    def test_title_from_filename(self, tmp_path):
        md = tmp_path / "my-lesson-name.md"
        md.write_text("No heading here, just body text.", encoding="utf-8")
        post = frontmatter.load(str(md))
        title, inferred = extract_title(post, md)
        assert title == "My Lesson Name"
        assert inferred

    def test_frontmatter_title_preferred_over_h1(self, tmp_path):
        md = tmp_path / "lesson.md"
        md.write_text(
            "---\ntitle: FM Title\n---\n\n# H1 Title\n\nBody.", encoding="utf-8"
        )
        post = frontmatter.load(str(md))
        title, inferred = extract_title(post, md)
        assert title == "FM Title"
        assert not inferred


class TestCoerceDate:
    def test_none(self):
        assert coerce_date(None) is None

    def test_string(self):
        assert coerce_date("2025-01-15") == "2025-01-15"

    def test_datetime(self):
        from datetime import datetime

        dt = datetime(2025, 3, 15, 10, 30)
        assert coerce_date(dt) == "2025-03-15"


class TestBuildSourceUrl:
    def test_basic(self):
        repo = {
            "owner": "user",
            "repo": "proj",
            "branch": "main",
            "lessons_path": "docs/lessons",
        }
        url = build_source_url(repo, "my-lesson.md")
        assert url == "https://github.com/user/proj/blob/main/docs/lessons/my-lesson.md"


class TestComputeReadingTime:
    def test_minimum_one_minute(self):
        assert compute_reading_time(10) == 1

    def test_200_words(self):
        assert compute_reading_time(200) == 1

    def test_400_words(self):
        assert compute_reading_time(400) == 2

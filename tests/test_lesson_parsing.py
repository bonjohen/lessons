"""Tests for lesson frontmatter parsing and title inference."""

import tempfile
from pathlib import Path

import frontmatter
import pytest


def extract_title(post, filepath: Path) -> tuple[str, bool]:
    """Extract title — mirrors harvester logic."""
    import re
    if post.get("title"):
        return post["title"], False
    for line in post.content.split("\n"):
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip(), False
    title = filepath.stem.replace("-", " ").replace("_", " ").title()
    return title, True


class TestLessonParsing:
    def test_valid_frontmatter(self, tmp_path):
        md = tmp_path / "lesson.md"
        md.write_text("---\ntitle: My Lesson\nsummary: A test\n---\n\nBody text here.", encoding="utf-8")
        post = frontmatter.load(str(md))
        assert post["title"] == "My Lesson"
        assert post["summary"] == "A test"
        assert post.content.strip() == "Body text here."

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

    def test_empty_content_detected(self, tmp_path):
        md = tmp_path / "empty.md"
        md.write_text("---\ntitle: Empty\n---\n", encoding="utf-8")
        post = frontmatter.load(str(md))
        assert post.content.strip() == ""

    def test_frontmatter_with_tags(self, tmp_path):
        md = tmp_path / "tagged.md"
        md.write_text("---\ntitle: Tagged\ntags: [python, testing]\n---\n\nContent.", encoding="utf-8")
        post = frontmatter.load(str(md))
        assert post["tags"] == ["python", "testing"]

    def test_no_frontmatter(self, tmp_path):
        md = tmp_path / "plain.md"
        md.write_text("# Just a Heading\n\nPlain markdown without frontmatter.", encoding="utf-8")
        post = frontmatter.load(str(md))
        title, inferred = extract_title(post, md)
        assert title == "Just a Heading"
        assert not inferred

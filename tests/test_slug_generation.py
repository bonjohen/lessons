"""Tests for slug generation and ID creation."""

from pathlib import Path, PurePosixPath

import frontmatter
import pytest
from slugify import slugify


def make_slug(post, filepath: Path, lessons_root: Path) -> str:
    """Mirrors harvester slug logic."""
    if post.get("slug"):
        return slugify(post["slug"])
    try:
        rel = filepath.relative_to(lessons_root).with_suffix("")
        parts = rel.parts
        return slugify("-".join(parts))
    except ValueError:
        return slugify(filepath.stem)


class TestSlugGeneration:
    def test_explicit_slug(self, tmp_path):
        md = tmp_path / "anything.md"
        md.write_text("---\nslug: custom-slug\ntitle: T\n---\nBody.", encoding="utf-8")
        post = frontmatter.load(str(md))
        assert make_slug(post, md, tmp_path) == "custom-slug"

    def test_filename_based_slug(self, tmp_path):
        lessons = tmp_path / "lessons"
        lessons.mkdir()
        md = lessons / "my-lesson-name.md"
        md.write_text("---\ntitle: T\n---\nBody.", encoding="utf-8")
        post = frontmatter.load(str(md))
        assert make_slug(post, md, lessons) == "my-lesson-name"

    def test_title_based_slug(self):
        assert slugify("Schema Drift Validation") == "schema-drift-validation"

    def test_kebab_case(self):
        assert slugify("My Great Lesson") == "my-great-lesson"
        assert slugify("under_score_name") == "under-score-name"

    def test_subdirectory_slug(self, tmp_path):
        """Lessons in subdirs include the subdir in the slug."""
        lessons = tmp_path / "lessons"
        sub = lessons / "block1"
        sub.mkdir(parents=True)
        md = sub / "index.md"
        md.write_text("---\ntitle: T\n---\nBody.", encoding="utf-8")
        post = frontmatter.load(str(md))
        slug = make_slug(post, md, lessons)
        assert slug == "block1-index"

    def test_duplicate_id_detection(self):
        ids = ["repo-lesson-a", "repo-lesson-b", "repo-lesson-a"]
        seen = set()
        dupes = []
        for lid in ids:
            if lid in seen:
                dupes.append(lid)
            seen.add(lid)
        assert dupes == ["repo-lesson-a"]

    def test_id_format(self, tmp_path):
        lessons = tmp_path / "lessons"
        lessons.mkdir()
        md = lessons / "my-lesson.md"
        md.write_text("---\ntitle: T\n---\nBody.", encoding="utf-8")
        post = frontmatter.load(str(md))
        slug = make_slug(post, md, lessons)
        lesson_id = f"myrepo-{slug}"
        assert lesson_id == "myrepo-my-lesson"

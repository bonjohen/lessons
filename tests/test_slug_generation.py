"""Tests for slug generation and ID creation."""

import frontmatter

from lesson_core import make_slug, find_duplicate_ids


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

    def test_slug_outside_lessons_root(self, tmp_path):
        """File outside lessons_root falls back to stem."""
        md = tmp_path / "outside.md"
        md.write_text("---\ntitle: T\n---\nBody.", encoding="utf-8")
        post = frontmatter.load(str(md))
        lessons_root = tmp_path / "other"
        lessons_root.mkdir()
        assert make_slug(post, md, lessons_root) == "outside"

    def test_duplicate_id_detection(self):
        items = [{"id": "a"}, {"id": "b"}, {"id": "a"}]
        assert find_duplicate_ids(items) == ["a"]

    def test_id_format(self, tmp_path):
        lessons = tmp_path / "lessons"
        lessons.mkdir()
        md = lessons / "my-lesson.md"
        md.write_text("---\ntitle: T\n---\nBody.", encoding="utf-8")
        post = frontmatter.load(str(md))
        slug = make_slug(post, md, lessons)
        lesson_id = f"myrepo-{slug}"
        assert lesson_id == "myrepo-my-lesson"

"""Tests for the RAG corpus builder."""

import json
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_rag_corpus import build_corpus, chunk_by_heading, content_hash, estimate_tokens


class TestChunkByHeading:
    """Test markdown chunking by H2 headings."""

    def test_single_section_no_h2(self):
        content = "# Title\n\nSome intro text.\n\nMore text here."
        meta = {"title": "Test Lesson", "repo_id": "test", "tags": [], "summary": ""}
        chunks = chunk_by_heading(content, "test-lesson", meta)
        assert len(chunks) == 1
        assert chunks[0]["heading_path"] == "Test Lesson"
        assert chunks[0]["chunk_index"] == 0

    def test_splits_on_h2(self):
        content = "Intro paragraph.\n\n## Section One\n\nContent one.\n\n## Section Two\n\nContent two."
        meta = {"title": "Test", "repo_id": "r", "tags": [], "summary": ""}
        chunks = chunk_by_heading(content, "test-id", meta)
        assert len(chunks) == 3  # intro + 2 sections
        assert chunks[0]["heading_path"] == "Test"
        assert "Section One" in chunks[1]["heading_path"]
        assert "Section Two" in chunks[2]["heading_path"]

    def test_does_not_split_on_h3(self):
        content = "## Main Section\n\nText.\n\n### Subsection\n\nMore text."
        meta = {"title": "T", "repo_id": "r", "tags": [], "summary": ""}
        chunks = chunk_by_heading(content, "id", meta)
        assert len(chunks) == 1
        assert "Subsection" in chunks[0]["chunk_text"]

    def test_stable_chunk_ids(self):
        content = "## A\n\nText A.\n\n## B\n\nText B."
        meta = {"title": "T", "repo_id": "r", "tags": [], "summary": ""}
        chunks1 = chunk_by_heading(content, "lesson-1", meta)
        chunks2 = chunk_by_heading(content, "lesson-1", meta)
        assert [c["chunk_id"] for c in chunks1] == [c["chunk_id"] for c in chunks2]

    def test_preserves_metadata(self):
        content = "## Section\n\nBody text."
        meta = {"title": "My Title", "repo_id": "my-repo", "tags": ["python", "testing"], "summary": "A summary"}
        chunks = chunk_by_heading(content, "my-lesson", meta)
        chunk = chunks[0]
        assert chunk["title"] == "My Title"
        assert chunk["repo_id"] == "my-repo"
        assert chunk["tags"] == ["python", "testing"]
        assert chunk["lesson_id"] == "my-lesson"

    def test_empty_content_returns_no_chunks(self):
        chunks = chunk_by_heading("", "id", {"title": "T", "repo_id": "r", "tags": [], "summary": ""})
        assert chunks == []

    def test_chunk_text_includes_heading_line(self):
        content = "## My Heading\n\nParagraph under heading."
        meta = {"title": "T", "repo_id": "r", "tags": [], "summary": ""}
        chunks = chunk_by_heading(content, "id", meta)
        assert "## My Heading" in chunks[0]["chunk_text"]

    def test_content_hash_is_stable(self):
        text = "Same content"
        assert content_hash(text) == content_hash(text)

    def test_content_hash_changes_with_content(self):
        assert content_hash("aaa") != content_hash("bbb")


class TestEstimateTokens:
    def test_short_text(self):
        assert estimate_tokens("hello world") >= 1

    def test_longer_text(self):
        text = " ".join(["word"] * 100)
        tokens = estimate_tokens(text)
        assert 100 < tokens < 200  # ~1.33x words


class TestBuildCorpus:
    def test_build_from_fixture(self, tmp_path):
        lessons = [
            {
                "id": "repo-lesson-one",
                "title": "Lesson One",
                "summary": "First lesson",
                "repo_id": "repo",
                "content": "## Section A\n\nContent A.\n\n## Section B\n\nContent B.",
                "tags": ["testing"],
            },
            {
                "id": "repo-lesson-two",
                "title": "Lesson Two",
                "summary": "",
                "repo_id": "repo",
                "content": "Just a paragraph with no headings.",
                "tags": [],
            },
        ]

        lessons_file = tmp_path / "lessons.json"
        lessons_file.write_text(json.dumps(lessons), encoding="utf-8")

        chunks, manifest = build_corpus(lessons_file)

        assert manifest["total_lessons"] == 2
        assert manifest["lessons_chunked"] == 2
        assert manifest["lessons_skipped"] == 0
        assert manifest["total_chunks"] == len(chunks)
        assert len(chunks) == 3  # 2 sections from lesson 1 + 1 from lesson 2

        # All chunk IDs unique
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))

    def test_skips_empty_content(self, tmp_path):
        lessons = [{"id": "empty", "title": "Empty", "summary": "", "repo_id": "r", "content": "", "tags": []}]
        lessons_file = tmp_path / "lessons.json"
        lessons_file.write_text(json.dumps(lessons), encoding="utf-8")

        chunks, manifest = build_corpus(lessons_file)
        assert manifest["lessons_skipped"] == 1
        assert len(chunks) == 0

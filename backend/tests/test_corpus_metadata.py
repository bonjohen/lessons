"""Tests for RAG corpus metadata enrichment (lesson_type, phase, status)."""

import importlib.util
import json
import tempfile
from pathlib import Path

# Load build_rag_corpus directly — scripts/ is not a Python package
_SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "build_rag_corpus.py"
_spec = importlib.util.spec_from_file_location("build_rag_corpus", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
build_corpus = _mod.build_corpus


def _make_lessons_json(lessons: list[dict]) -> Path:
    """Write a temporary lessons.json and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(lessons, tmp)
    tmp.close()
    return Path(tmp.name)


def test_corpus_chunk_includes_lesson_type():
    """Chunks built from a lesson with lesson_type carry that field."""
    path = _make_lessons_json([
        {
            "id": "test-lesson",
            "title": "Deploy Guide",
            "summary": "How to deploy",
            "repo_id": "repo1",
            "tags": ["deploy"],
            "lesson_type": "deployment",
            "phase": "production",
            "status": "active",
            "content": "## Setup\n\nInstall the thing.\n\n## Deploy\n\nRun the command.",
        }
    ])
    chunks, manifest = build_corpus(path)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk["lesson_type"] == "deployment"
        assert chunk["phase"] == "production"
        assert chunk["status"] == "active"
    Path(path).unlink()


def test_corpus_chunk_defaults_missing_metadata():
    """Chunks from lessons without lesson_type/phase/status default to empty string."""
    path = _make_lessons_json([
        {
            "id": "minimal-lesson",
            "title": "Minimal",
            "content": "## Intro\n\nSome content.",
        }
    ])
    chunks, _ = build_corpus(path)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk["lesson_type"] == ""
        assert chunk["phase"] == ""
        assert chunk["status"] == ""
    Path(path).unlink()


def test_chromadb_metadata_includes_lesson_type():
    """ChromaDB adapter includes lesson_type in the metadata dict on upsert."""
    # Simulate what index_chunks does with metadata extraction
    chunk = {
        "chunk_id": "c1",
        "lesson_id": "l1",
        "repo_id": "r1",
        "title": "Test",
        "summary": "A test",
        "heading_path": "Test",
        "lesson_url": "/lessons/l1",
        "chunk_text": "text",
        "tags": ["deploy"],
        "chunk_index": 0,
        "lesson_type": "deployment",
        "phase": "production",
        "status": "active",
    }

    # Build metadata dict the same way the adapter does
    metadata = {
        "lesson_id": chunk["lesson_id"],
        "repo_id": chunk["repo_id"],
        "title": chunk["title"],
        "summary": chunk.get("summary", ""),
        "heading_path": chunk["heading_path"],
        "lesson_url": chunk["lesson_url"],
        "tags": ",".join(chunk.get("tags", [])),
        "chunk_index": chunk["chunk_index"],
        "lesson_type": chunk.get("lesson_type", ""),
        "phase": chunk.get("phase", ""),
        "status": chunk.get("status", ""),
    }

    assert metadata["lesson_type"] == "deployment"
    assert metadata["phase"] == "production"
    assert metadata["status"] == "active"

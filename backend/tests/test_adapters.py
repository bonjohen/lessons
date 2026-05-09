"""Tests for vector and LLM adapters."""

import pytest

from app.adapters.vector.chromadb_adapter import ChromaDBAdapter


class TestChromaDBAdapter:
    """Test ChromaDB vector adapter with a temp directory."""

    @pytest.fixture
    def adapter(self, tmp_path):
        return ChromaDBAdapter(persist_dir=tmp_path / "chromadb")

    def test_empty_collection(self, adapter):
        assert adapter.count() == 0

    def test_index_and_count(self, adapter):
        chunks = [
            {
                "chunk_id": "c1",
                "chunk_text": "hello world",
                "lesson_id": "l1",
                "repo_id": "r1",
                "title": "T1",
                "summary": "S1",
                "heading_path": "H1",
                "lesson_url": "/l/1",
                "tags": ["a"],
                "chunk_index": 0,
            },
            {
                "chunk_id": "c2",
                "chunk_text": "goodbye world",
                "lesson_id": "l1",
                "repo_id": "r1",
                "title": "T1",
                "summary": "S1",
                "heading_path": "H2",
                "lesson_url": "/l/1",
                "tags": [],
                "chunk_index": 1,
            },
        ]
        embeddings = [[0.1] * 10, [0.2] * 10]
        count = adapter.index_chunks(chunks, embeddings)
        assert count == 2
        assert adapter.count() == 2

    def test_query_returns_results(self, adapter):
        chunks = [
            {
                "chunk_id": "c1",
                "chunk_text": "python testing",
                "lesson_id": "l1",
                "repo_id": "r1",
                "title": "Testing",
                "summary": "",
                "heading_path": "Testing",
                "lesson_url": "/l/1",
                "tags": ["testing"],
                "chunk_index": 0,
            },
        ]
        embeddings = [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
        adapter.index_chunks(chunks, embeddings)

        results = adapter.query([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], top_k=5)
        assert len(results) == 1
        assert results[0]["chunk_id"] == "c1"
        assert results[0]["similarity_score"] > 0

    def test_query_empty_collection(self, adapter):
        results = adapter.query([0.1] * 10, top_k=5)
        assert results == []

    def test_delete_collection(self, adapter):
        chunks = [
            {
                "chunk_id": "c1",
                "chunk_text": "text",
                "lesson_id": "l1",
                "repo_id": "r1",
                "title": "T",
                "summary": "",
                "heading_path": "H",
                "lesson_url": "/l/1",
                "tags": [],
                "chunk_index": 0,
            },
        ]
        adapter.index_chunks(chunks, [[0.5] * 10])
        assert adapter.count() == 1

        adapter.delete_collection()
        assert adapter.count() == 0

    def test_index_empty_list(self, adapter):
        assert adapter.index_chunks([], []) == 0

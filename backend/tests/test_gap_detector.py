"""Tests for gap detection and gap store."""

import pytest

from app.rag.gap_detector import _extract_concepts, _normalize_topic, _suggest_github_queries, detect_gap
from app.rag.gap_store import GapStore


class TestDetectGap:
    """Test the 7 gap detection rules."""

    def _chunks(self, scores, lesson_ids=None):
        """Create mock chunks with given similarity scores."""
        return [
            {
                "chunk_id": f"c{i}",
                "lesson_id": lesson_ids[i] if lesson_ids else f"lesson-{i}",
                "similarity_score": score,
                "chunk_text": f"some text about topic {i}",
            }
            for i, score in enumerate(scores)
        ]

    def test_no_gap_when_strong_retrieval(self):
        chunks = self._chunks([0.85, 0.72, 0.65], ["l1", "l2", "l3"])
        result = detect_gap(
            "How do I test?", chunks, "Here is how to test using pytest...", [{"lesson_id": "l1"}, {"lesson_id": "l2"}]
        )
        assert result is None

    def test_gap_when_no_relevant_chunks(self):
        chunks = self._chunks([0.1, 0.05])
        result = detect_gap("container apps deployment", chunks, "I could not find relevant lessons.", [])
        assert result is not None
        assert result["gap_type"] == "missing_topic"

    def test_gap_when_few_distinct_lessons(self):
        chunks = self._chunks([0.5, 0.45, 0.4], ["l1", "l1", "l1"])
        result = detect_gap("How to deploy?", chunks, "Based on one lesson...", [{"lesson_id": "l1"}])
        assert result is not None

    def test_gap_when_weak_answer_language(self):
        chunks = self._chunks([0.6, 0.5], ["l1", "l2"])
        result = detect_gap(
            "What about Kubernetes?", chunks, "The corpus does not appear to contain material about Kubernetes.", []
        )
        assert result is not None
        assert "weak_answer_language" in result["detection_reasons"]

    def test_gap_for_missing_platform(self):
        chunks = self._chunks([0.4, 0.3], ["l1", "l2"])
        # Chunks don't mention "azure"
        result = detect_gap("Azure deployment lessons", chunks, "Limited coverage.", [])
        assert result is not None
        assert result["gap_type"] == "missing_platform"

    def test_gap_includes_suggested_queries(self):
        chunks = self._chunks([0.1])
        result = detect_gap("Terraform infrastructure as code", chunks, "No lessons found.", [])
        assert result is not None
        assert len(result["suggested_github_queries"]) > 0

    def test_no_gap_on_empty_chunks_but_good_answer(self):
        # Edge case: no chunks but somehow a good answer shouldn't happen,
        # but if chunks are empty, gap should be detected
        result = detect_gap("Something", [], "I could not find anything.", [])
        assert result is not None


class TestGapHelpers:
    def test_normalize_topic(self):
        topic = _normalize_topic("What lessons do I have about testing?")
        assert "testing" in topic

    def test_extract_concepts(self):
        concepts = _extract_concepts("Azure Container Apps deployment best practices")
        assert "azure" in concepts
        assert "container" in concepts
        assert "deployment" in concepts

    def test_suggest_github_queries(self):
        queries = _suggest_github_queries("Terraform deployment patterns", "terraform deployment patterns")
        assert len(queries) > 0
        assert any("terraform" in q for q in queries)


class TestGapStore:
    @pytest.fixture
    def store(self, tmp_path):
        return GapStore(path=tmp_path / "gaps.json")

    def test_empty_store(self, store):
        assert store.list_gaps() == []
        assert store.count() == 0

    def test_create_and_get(self, store):
        gap = {"gap_id": "gap_123", "status": "open", "trigger_query": "test", "normalized_topic": "test"}
        stored = store.create_or_update(gap)
        assert stored["gap_id"] == "gap_123"
        assert store.count() == 1
        assert store.get_gap("gap_123") is not None

    def test_update_existing(self, store):
        gap = {"gap_id": "gap_123", "status": "open", "trigger_query": "first query", "normalized_topic": "test"}
        store.create_or_update(gap)
        gap2 = {
            "gap_id": "gap_123",
            "status": "open",
            "trigger_query": "second query",
            "normalized_topic": "test",
            "retrieval_summary": "updated",
            "confidence_score": 0.5,
        }
        stored = store.create_or_update(gap2)
        assert store.count() == 1
        assert "second query" in str(stored.get("additional_queries", []))

    def test_update_status(self, store):
        gap = {"gap_id": "gap_123", "status": "open", "trigger_query": "test", "normalized_topic": "test"}
        store.create_or_update(gap)
        result = store.update_status("gap_123", "searching")
        assert result["status"] == "searching"

    def test_invalid_status(self, store):
        gap = {"gap_id": "gap_123", "status": "open", "trigger_query": "test", "normalized_topic": "test"}
        store.create_or_update(gap)
        result = store.update_status("gap_123", "invalid_status")
        assert result is None

    def test_filter_by_status(self, store):
        store.create_or_update({"gap_id": "g1", "status": "open", "trigger_query": "a", "normalized_topic": "a"})
        store.create_or_update({"gap_id": "g2", "status": "resolved", "trigger_query": "b", "normalized_topic": "b"})
        open_gaps = store.list_gaps(status="open")
        assert len(open_gaps) == 1
        assert open_gaps[0]["gap_id"] == "g1"

    def test_get_nonexistent(self, store):
        assert store.get_gap("nonexistent") is None

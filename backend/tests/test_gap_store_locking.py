"""Tests for concurrent GapStore writes with file locking."""

import json
import threading

from app.rag.gap_store import GapStore


def _make_gap(n: int) -> dict:
    return {
        "gap_id": f"gap_thread_{n}",
        "created_date": "2026-01-01T00:00:00Z",
        "updated_date": "2026-01-01T00:00:00Z",
        "status": "open",
        "trigger_query": f"query {n}",
        "normalized_topic": f"topic {n}",
        "missing_concepts": [],
        "retrieval_summary": "",
        "best_matching_lessons": [],
        "confidence_score": 0.0,
        "suggested_github_queries": [],
        "candidate_repo_ids": [],
        "todo_ids": [],
        "resolution_notes": "",
        "gap_type": "missing_topic",
        "detection_reasons": ["no_relevant_chunks"],
    }


class TestConcurrentGapStoreWrites:
    def test_ten_threads_all_records_persisted(self, tmp_path):
        store = GapStore(path=tmp_path / "gaps.json")
        barrier = threading.Barrier(10)
        errors = []

        def write_gap(n):
            try:
                barrier.wait(timeout=5)
                store.create_or_update(_make_gap(n))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_gap, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"

        # Verify final file is valid JSON with all 10 records
        with open(tmp_path / "gaps.json", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 10
        ids = {g["gap_id"] for g in data}
        assert ids == {f"gap_thread_{i}" for i in range(10)}

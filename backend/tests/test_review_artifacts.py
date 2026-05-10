"""Tests for dual-write of runtime JSON + review markdown artifacts."""

import json

from backend.app.rag.gap_store import GapStore


def test_gap_store_writes_review_markdown(tmp_path):
    """GapStore.create_or_update writes both JSON and review markdown."""
    gaps_json = tmp_path / "gaps" / "corpus-gaps.json"
    review_dir = tmp_path / "review" / "gaps"

    store = GapStore(path=gaps_json, review_dir=review_dir)

    gap = {
        "gap_id": "gap_test_topic",
        "created_date": "2026-05-10",
        "updated_date": "",
        "status": "open",
        "trigger_query": "How do I deploy to Azure?",
        "normalized_topic": "azure deployment",
        "missing_concepts": ["Azure Container Apps", "ACA"],
        "retrieval_summary": "No relevant chunks found",
        "best_matching_lessons": [],
        "confidence_score": 0.1,
        "suggested_github_queries": ["Azure Container Apps deployment"],
        "candidate_repo_ids": [],
        "todo_ids": [],
        "resolution_notes": "",
        "gap_type": "missing_platform",
    }

    store.create_or_update(gap)

    # JSON file should exist
    assert gaps_json.exists()
    data = json.loads(gaps_json.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["gap_id"] == "gap_test_topic"

    # Review markdown should exist
    review_file = review_dir / "gap_test_topic.md"
    assert review_file.exists()
    content = review_file.read_text(encoding="utf-8")
    assert "gap_id: gap_test_topic" in content
    assert "azure deployment" in content
    assert "Azure Container Apps" in content


def test_gap_store_update_status_writes_review(tmp_path):
    """GapStore.update_status also updates the review markdown."""
    gaps_json = tmp_path / "gaps" / "corpus-gaps.json"
    review_dir = tmp_path / "review" / "gaps"

    store = GapStore(path=gaps_json, review_dir=review_dir)

    gap = {
        "gap_id": "gap_status_test",
        "created_date": "2026-05-10",
        "updated_date": "",
        "status": "open",
        "trigger_query": "test query",
        "normalized_topic": "test topic",
        "missing_concepts": [],
        "retrieval_summary": "",
        "best_matching_lessons": [],
        "confidence_score": 0.0,
        "suggested_github_queries": [],
        "candidate_repo_ids": [],
        "todo_ids": [],
        "resolution_notes": "",
        "gap_type": "missing_topic",
    }

    store.create_or_update(gap)
    store.update_status("gap_status_test", "searching")

    review_file = review_dir / "gap_status_test.md"
    content = review_file.read_text(encoding="utf-8")
    assert "status: searching" in content

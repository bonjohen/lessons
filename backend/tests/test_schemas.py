"""Tests for Pydantic schema model ordering and validation."""

from backend.app.models.schemas import (
    ChatFilters,
    ChatRequest,
    ChatResponse,
    ChunkRecord,
    ChunkResult,
    RelevantLesson,
    RetrieveRequest,
    RetrieveResponse,
)


def test_chat_request_with_filters():
    """ChatRequest with ChatFilters — no forward-reference errors."""
    filters = ChatFilters(repo="test-repo", lesson_type="deployment")
    req = ChatRequest(message="hello", filters=filters)
    assert req.filters.repo == "test-repo"
    assert req.filters.lesson_type == "deployment"


def test_chat_request_without_filters():
    """ChatRequest without filters works."""
    req = ChatRequest(message="hello")
    assert req.filters is None


def test_retrieve_response_with_chunk_results():
    """RetrieveResponse with ChunkResult list — no forward-reference errors."""
    chunk = ChunkResult(
        chunk_id="c1",
        lesson_id="l1",
        title="Test",
        heading_path="Test > Intro",
        chunk_text="some text",
        similarity_score=0.9,
        lesson_type="deployment",
    )
    resp = RetrieveResponse(query="test query", chunks=[chunk])
    assert len(resp.chunks) == 1
    assert resp.chunks[0].lesson_type == "deployment"


def test_retrieve_request_uses_chat_filters():
    """RetrieveRequest also uses ChatFilters."""
    filters = ChatFilters(tags=["docker"])
    req = RetrieveRequest(query="test", filters=filters)
    assert req.filters.tags == ["docker"]


def test_chunk_record_has_metadata_fields():
    """ChunkRecord includes lesson_type, phase, status."""
    rec = ChunkRecord(
        chunk_id="c1",
        lesson_id="l1",
        repo_id="r1",
        title="Test",
        summary="A test",
        lesson_url="/lessons/l1",
        chunk_index=0,
        heading_path="Test",
        chunk_text="text",
        token_count=5,
        content_hash="abc123",
        lesson_type="deployment",
        phase="production",
        status="active",
    )
    assert rec.lesson_type == "deployment"
    assert rec.phase == "production"
    assert rec.status == "active"


def test_chat_response_structure():
    """ChatResponse includes gap detection fields."""
    lesson = RelevantLesson(
        lesson_id="l1",
        title="Test",
        repo_name="repo",
        similarity_score=0.8,
        lesson_url="/lessons/l1",
    )
    resp = ChatResponse(answer="answer", relevant_lessons=[lesson], gap_detected=True)
    assert resp.gap_detected is True
    assert len(resp.relevant_lessons) == 1

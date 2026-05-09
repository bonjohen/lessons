"""Chat endpoint — RAG-grounded Q&A over the lessons corpus."""

from fastapi import APIRouter

from app.api._deps import get_gap_store, get_generator
from app.models.schemas import ChatRequest, ChatResponse, RelevantLesson
from app.rag.gap_detector import detect_gap

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Answer a question using the lessons corpus."""
    generator = get_generator()
    if generator is None:
        return ChatResponse(
            answer="The RAG backend is not initialized. Please run the embedding pipeline first.",
            relevant_lessons=[],
        )

    filters = None
    if req.filters:
        filters = req.filters.model_dump(exclude_none=True)
        if not any(filters.values()):
            filters = None

    result = generator.generate(req.message, top_k=req.top_k, filters=filters)

    relevant_lessons = [
        RelevantLesson(
            lesson_id=rl["lesson_id"],
            title=rl["title"],
            repo_name=rl["repo_name"],
            similarity_score=rl["similarity_score"],
            lesson_url=rl["lesson_url"],
        )
        for rl in result["relevant_lessons"]
    ]

    # Gap detection
    gap_detected = False
    gap_id = None
    suggested_actions = []

    gap = detect_gap(
        query=req.message,
        chunks=result.get("chunks", []),
        answer=result["answer"],
        relevant_lessons=result["relevant_lessons"],
    )

    if gap:
        gap_detected = True
        gap_store = get_gap_store()
        stored_gap = gap_store.create_or_update(gap)
        gap_id = stored_gap["gap_id"]
        suggested_actions = [
            "Search GitHub for relevant projects",
            "Create candidate lessons from relevant repos",
        ]

    return ChatResponse(
        answer=result["answer"],
        relevant_lessons=relevant_lessons,
        gap_detected=gap_detected,
        gap_id=gap_id,
        suggested_actions=suggested_actions,
    )

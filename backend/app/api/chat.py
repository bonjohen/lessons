"""Chat endpoint — RAG-grounded Q&A over the lessons corpus."""

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse, RelevantLesson
from app.api._deps import get_generator

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

    return ChatResponse(
        answer=result["answer"],
        relevant_lessons=relevant_lessons,
    )

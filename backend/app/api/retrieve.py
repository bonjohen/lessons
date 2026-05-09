"""Retrieve endpoint — return relevant chunks without generation."""

from fastapi import APIRouter

from app.api._deps import get_retriever
from app.models.schemas import ChunkResult, RetrieveRequest, RetrieveResponse

router = APIRouter()


@router.post("/api/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    """Retrieve relevant lesson chunks for a query."""
    retriever = get_retriever()
    if retriever is None:
        return RetrieveResponse(query=req.query, chunks=[])

    filters = None
    if req.filters:
        filters = req.filters.model_dump(exclude_none=True)
        if not any(filters.values()):
            filters = None

    results = retriever.retrieve(req.query, top_k=req.top_k, filters=filters)

    chunks = [
        ChunkResult(
            chunk_id=r["chunk_id"],
            lesson_id=r["lesson_id"],
            title=r["title"],
            heading_path=r["heading_path"],
            chunk_text=r["chunk_text"],
            similarity_score=r["similarity_score"],
            tags=r.get("tags", []),
        )
        for r in results
    ]

    return RetrieveResponse(query=req.query, chunks=chunks)

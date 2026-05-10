"""RAG retriever — query vector store and return relevant chunks."""

from __future__ import annotations

from app.adapters.llm.base import LLMAdapter
from app.adapters.vector.base import VectorAdapter

DEFAULT_TOP_K = 8


class Retriever:
    """Retrieves relevant lesson chunks for a query."""

    def __init__(self, vector: VectorAdapter, llm: LLMAdapter):
        self._vector = vector
        self._llm = llm

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K, filters: dict | None = None) -> list[dict]:
        """Embed the query and retrieve similar chunks.

        Returns list of chunk results with similarity scores.
        """
        query_embedding = self._llm.embed([query])[0]
        results = self._vector.query(query_embedding, top_k=top_k, filters=filters)
        return results

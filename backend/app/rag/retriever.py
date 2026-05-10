"""RAG retriever — query vector store and return relevant chunks."""

from __future__ import annotations

from app.adapters.llm.base import LLMAdapter
from app.adapters.vector.base import VectorAdapter
from app.rag.cache import TTLCache

DEFAULT_TOP_K = 8


class Retriever:
    """Retrieves relevant lesson chunks for a query."""

    def __init__(self, vector: VectorAdapter, llm: LLMAdapter):
        self._vector = vector
        self._llm = llm
        self._cache = TTLCache()

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K, filters: dict | None = None) -> list[dict]:
        """Embed the query and retrieve similar chunks.

        Returns list of chunk results with similarity scores.
        Caches results by query string with TTL.
        """
        cache_key = TTLCache.make_key(query, filters)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        query_embedding = self._llm.embed([query])[0]
        results = self._vector.query(query_embedding, top_k=top_k, filters=filters)

        self._cache.put(cache_key, results)
        return results

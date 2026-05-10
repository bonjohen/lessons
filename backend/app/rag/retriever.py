"""RAG retriever — query vector store and return relevant chunks."""

from __future__ import annotations

import os
import time

from app.adapters.llm.base import LLMAdapter
from app.adapters.vector.base import VectorAdapter

DEFAULT_TOP_K = 8
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "128"))


class Retriever:
    """Retrieves relevant lesson chunks for a query."""

    def __init__(self, vector: VectorAdapter, llm: LLMAdapter):
        self._vector = vector
        self._llm = llm
        self._cache: dict[str, tuple[float, list[dict]]] = {}

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K, filters: dict | None = None) -> list[dict]:
        """Embed the query and retrieve similar chunks.

        Returns list of chunk results with similarity scores.
        Caches results by query string with TTL.
        """
        cache_key = query if filters is None else f"{query}|{sorted(filters.items())}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            ts, results = cached
            if time.monotonic() - ts < CACHE_TTL_SECONDS:
                return results
            del self._cache[cache_key]

        query_embedding = self._llm.embed([query])[0]
        results = self._vector.query(query_embedding, top_k=top_k, filters=filters)

        # Evict oldest if at capacity
        if len(self._cache) >= CACHE_MAX_SIZE:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]

        self._cache[cache_key] = (time.monotonic(), results)
        return results

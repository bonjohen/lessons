"""RAG generator — produce grounded answers from retrieved context."""

from __future__ import annotations

import os
import time

from app.adapters.llm.base import LLMAdapter
from app.rag.prompt_builder import build_chat_messages
from app.rag.retriever import Retriever

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "128"))


class Generator:
    """Generates answers grounded in lesson context."""

    def __init__(self, retriever: Retriever, llm: LLMAdapter):
        self._retriever = retriever
        self._llm = llm
        self._cache: dict[str, tuple[float, dict]] = {}

    def generate(self, query: str, top_k: int = 8, filters: dict | None = None) -> dict:
        """Retrieve context and generate an answer.

        Returns dict with answer, relevant_lessons, and retrieval metadata.
        Caches full results by query string with TTL.
        """
        cache_key = query if filters is None else f"{query}|{sorted(filters.items())}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            ts, result = cached
            if time.monotonic() - ts < CACHE_TTL_SECONDS:
                return result
            del self._cache[cache_key]

        chunks = self._retriever.retrieve(query, top_k=top_k, filters=filters)

        if not chunks:
            result = {
                "answer": "I could not find any relevant lessons in the corpus for this question.",
                "relevant_lessons": [],
                "chunks": [],
            }
        else:
            messages = build_chat_messages(query, chunks)
            answer = self._llm.chat(messages)

            # Deduplicate lessons from chunks
            seen = set()
            relevant_lessons = []
            for chunk in chunks:
                lid = chunk.get("lesson_id", "")
                if lid and lid not in seen:
                    seen.add(lid)
                    relevant_lessons.append(
                        {
                            "lesson_id": lid,
                            "title": chunk.get("title", ""),
                            "repo_name": chunk.get("repo_id", ""),
                            "similarity_score": chunk.get("similarity_score", 0.0),
                            "lesson_url": chunk.get("lesson_url", ""),
                        }
                    )

            result = {
                "answer": answer,
                "relevant_lessons": relevant_lessons,
                "chunks": chunks,
            }

        # Evict oldest if at capacity
        if len(self._cache) >= CACHE_MAX_SIZE:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]

        self._cache[cache_key] = (time.monotonic(), result)
        return result

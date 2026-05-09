"""RAG generator — produce grounded answers from retrieved context."""

from __future__ import annotations

from app.adapters.llm.base import LLMAdapter
from app.rag.prompt_builder import build_chat_messages
from app.rag.retriever import Retriever


class Generator:
    """Generates answers grounded in lesson context."""

    def __init__(self, retriever: Retriever, llm: LLMAdapter):
        self._retriever = retriever
        self._llm = llm

    def generate(self, query: str, top_k: int = 8, filters: dict | None = None) -> dict:
        """Retrieve context and generate an answer.

        Returns dict with answer, relevant_lessons, and retrieval metadata.
        """
        chunks = self._retriever.retrieve(query, top_k=top_k, filters=filters)

        if not chunks:
            return {
                "answer": "I could not find any relevant lessons in the corpus for this question.",
                "relevant_lessons": [],
                "chunks": [],
            }

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

        return {
            "answer": answer,
            "relevant_lessons": relevant_lessons,
            "chunks": chunks,
        }

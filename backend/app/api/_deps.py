"""Shared dependency singletons for API endpoints."""

from __future__ import annotations

from app.adapters.llm.ollama_adapter import OllamaAdapter
from app.adapters.vector.chromadb_adapter import ChromaDBAdapter
from app.rag.gap_store import GapStore
from app.rag.generator import Generator
from app.rag.retriever import Retriever

_retriever: Retriever | None = None
_generator: Generator | None = None
_gap_store: GapStore | None = None


def _init():
    """Lazy-initialize the RAG pipeline components."""
    global _retriever, _generator

    try:
        vector = ChromaDBAdapter()
        if vector.count() == 0:
            return  # No embeddings indexed yet
    except Exception:
        return  # ChromaDB not available

    try:
        llm = OllamaAdapter()
    except Exception:
        return  # Ollama not available

    _retriever = Retriever(vector=vector, llm=llm)
    _generator = Generator(retriever=_retriever, llm=llm)


def get_retriever() -> Retriever | None:
    """Get the retriever singleton, initializing if needed."""
    if _retriever is None:
        _init()
    return _retriever


def get_generator() -> Generator | None:
    """Get the generator singleton, initializing if needed."""
    if _generator is None:
        _init()
    return _generator


def get_gap_store() -> GapStore:
    """Get the gap store singleton."""
    global _gap_store
    if _gap_store is None:
        _gap_store = GapStore()
    return _gap_store

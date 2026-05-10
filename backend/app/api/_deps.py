"""Shared dependency singletons for API endpoints."""

from __future__ import annotations

import os
import threading

from app.rag.gap_store import GapStore
from app.rag.generator import Generator
from app.rag.retriever import Retriever

_retriever: Retriever | None = None
_generator: Generator | None = None
_gap_store: GapStore | None = None
_INIT_LOCK = threading.Lock()


def _create_adapters(profile: str):
    """Return (llm, vector) adapter pair for the given deployment profile."""
    if profile == "aws":
        from app.adapters.llm.bedrock_adapter import BedrockAdapter
        from app.adapters.vector.opensearch_adapter import OpenSearchAdapter

        return BedrockAdapter(), OpenSearchAdapter()

    if profile == "azure":
        from app.adapters.llm.azure_openai_adapter import AzureOpenAIAdapter
        from app.adapters.vector.azure_search_adapter import AzureSearchAdapter

        return AzureOpenAIAdapter(), AzureSearchAdapter()

    if profile == "gcp":
        from app.adapters.llm.vertex_adapter import VertexAIAdapter
        from app.adapters.vector.vertex_adapter import VertexVectorSearchAdapter

        return VertexAIAdapter(), VertexVectorSearchAdapter()

    # Default: local (Ollama + ChromaDB)
    from app.adapters.llm.ollama_adapter import OllamaAdapter
    from app.adapters.vector.chromadb_adapter import ChromaDBAdapter

    return OllamaAdapter(), ChromaDBAdapter()


def _init():
    """Lazy-initialize the RAG pipeline components (thread-safe)."""
    global _retriever, _generator

    if _retriever is not None:
        return

    with _INIT_LOCK:
        if _retriever is not None:
            return  # another thread initialized while we waited

        profile = os.environ.get("DEPLOYMENT_PROFILE", "local")

        try:
            llm, vector = _create_adapters(profile)
        except Exception:
            return  # adapter not available

        # For local profile, skip if no embeddings indexed yet
        if profile == "local":
            try:
                if vector.count() == 0:
                    return
            except Exception:
                return

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
    if _gap_store is not None:
        return _gap_store

    with _INIT_LOCK:
        if _gap_store is None:
            _gap_store = GapStore()
        return _gap_store

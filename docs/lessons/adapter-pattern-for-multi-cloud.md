---
title: Adapter Pattern for Multi-Cloud Portability
summary: Abstract base classes with minimal interfaces let the same RAG pipeline run on four different cloud providers without conditional logic in business code.
date: 2026-05-09
phase: implementation
lesson_type: architecture
status: active
tags: [python, adapter-pattern, cloud, dependency-injection, architecture]
---

# Adapter Pattern for Multi-Cloud Portability

## The Lesson

When building an application that must run on multiple cloud providers, define the narrowest possible abstract interface for each external dependency, then inject the concrete implementation at startup. The business logic should never import, reference, or branch on any specific provider. The adapter boundary is the only place cloud-specific code lives.

## Context

A RAG chatbot needed two external capabilities: embedding/chat (LLM) and similarity search (vector store). The system had to run locally during development (Ollama + ChromaDB, free, no credentials) and on three cloud providers in production (AWS Bedrock + OpenSearch, Azure OpenAI + AI Search, GCP Vertex AI + Vector Search). Four LLM implementations and four vector store implementations — 16 possible combinations, though only 4 are used in practice.

## What Happened

1. Defined `LLMAdapter` as an abstract base class with two methods: `embed(texts) -> list[list[float]]` and `chat(messages) -> str`. No other methods. This was the smallest interface that covered all usage in the RAG pipeline.
2. Defined `VectorAdapter` with four methods: `index_chunks(chunks, embeddings) -> int`, `query(embedding, top_k, filters) -> list[dict]`, `delete_collection()`, and `count() -> int`.
3. Built the `Retriever` and `Generator` classes to accept these abstract types via constructor injection. Neither class imports any concrete adapter — only `from app.adapters.llm.base import LLMAdapter`.
4. Each cloud adapter handles provider-specific quirks internally. Bedrock separates system messages from chat messages (its API requires it). Vertex AI concatenates messages into a single prompt string for Gemini's `generate_content()`. Azure OpenAI uses the standard OpenAI client with an Azure endpoint. None of this leaks into the RAG pipeline.
5. ChromaDB returns distances (lower = more similar); the adapter converts to similarity scores (1.0 - distance). OpenSearch returns scores directly. The `query()` return format is identical regardless.
6. The dependency injection point (`_deps.py`) reads a `DEPLOYMENT_PROFILE` environment variable and instantiates the correct adapter pair. This is the only file that knows which concrete adapters exist.

## Key Insights

- **Two methods is enough for an LLM interface.** The temptation is to add methods for streaming, token counting, model listing, fine-tuning. Resist. The RAG pipeline needs `embed` and `chat`. Everything else is adapter-internal or a separate concern. Narrow interfaces are easier to implement and harder to break.

- **Uniform output formats matter more than uniform input formats.** Each cloud API has different request shapes (Bedrock's message format vs. OpenAI's vs. Gemini's). The adapter absorbs those differences. But the return values — embedding vectors as `list[list[float]]`, chat responses as `str`, query results as `list[dict]` with fixed keys — must be identical. The consumer code can't adapt to adapter-specific output shapes.

- **Constructor injection beats configuration files for adapter selection.** A factory function that reads one env var and returns the right pair is simpler than a plugin registry, configuration schema, or service locator. There are only four options. A dict lookup is the right complexity level.

- **Local development is a first-class deployment target.** Ollama + ChromaDB cost nothing, require no credentials, and start in seconds. If the adapter pattern makes local development harder, the abstraction is wrong. In practice, most debugging and feature development happens locally — the cloud adapters are used only for deployment validation.

- **Don't normalize what doesn't need normalizing.** Bedrock and Azure OpenAI both accept `messages: list[dict]` but with different structures. Rather than defining a universal message schema, each adapter translates from the simple `{role, content}` format the RAG pipeline produces. The translation is 5-10 lines per adapter, not worth abstracting further.

## Examples

**Business logic sees only the interface:**
```python
class Retriever:
    def __init__(self, vector: VectorAdapter, llm: LLMAdapter):
        self._vector = vector
        self._llm = llm

    def retrieve(self, query: str, top_k: int = 8) -> list[dict]:
        embedding = self._llm.embed([query])[0]
        return self._vector.query(embedding, top_k=top_k)
```

**Adapter selection is one place, one lookup:**
```python
ADAPTERS = {
    "local": (OllamaAdapter, ChromaDBAdapter),
    "aws":   (BedrockAdapter, OpenSearchAdapter),
    "azure": (AzureOpenAIAdapter, AzureSearchAdapter),
    "gcp":   (VertexAIAdapter, VertexVectorSearchAdapter),
}
profile = os.getenv("DEPLOYMENT_PROFILE", "local")
LLMClass, VectorClass = ADAPTERS[profile]
```

## Applicability

This pattern works when:
- The number of implementations is small (2-6) and known at design time
- The interface can be kept to a handful of methods
- Implementations differ in protocol details but serve the same purpose

It does **not** work well when:
- Implementations have fundamentally different capabilities (one supports streaming, another doesn't) — you end up with lowest-common-denominator interfaces
- The number of implementations grows unbounded (plugin systems need a different approach)
- Performance characteristics differ enough to change the calling code's behavior (batch sizes, rate limits)

## Related Lessons

- [Lazy Imports for Optional Cloud Dependencies](lazy-imports-for-optional-dependencies.md) — the import strategy that makes optional adapters possible
- [Phased Multi-Cloud Infrastructure](phased-multi-cloud-infrastructure.md) — the infrastructure side of the same multi-cloud story

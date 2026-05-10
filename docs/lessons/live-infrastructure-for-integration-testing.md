---
title: Live Infrastructure for Integration Testing
summary: When local services are already running, skip mocks and test the real pipeline end-to-end
date: 2026-05-10
phase: execution
lesson_type: process
status: active
tags: [testing, integration, ollama, chromadb, rag, mocks]
---

# Live Infrastructure for Integration Testing

## The Lesson

When local infrastructure happens to be running — an LLM server, a vector database, a message broker — use it for integration testing instead of defaulting to mocks. Mocks prove that your code calls the right functions; live tests prove that your system actually works.

## Context

Lessons Hub V2 has a RAG backend: a FastAPI server that retrieves lesson chunks from ChromaDB (vector store), sends them to Ollama (local LLM), and returns grounded answers with source citations. The pipeline has five stages: corpus build, embedding, retrieval, generation, and gap detection. Each stage was developed with unit tests using mocks — mocked vector adapters, mocked LLM responses, mocked gap stores. After 134 unit tests passed, the question was whether the real pipeline worked end-to-end.

## What Happened

1. After completing five phases of code improvements (schema fixes, security hardening, adapter factories, structured logging, caching), all 134 backend unit tests passed and lint was clean.
2. Before writing integration tests with mocks, a quick check revealed Ollama was already running locally with `nomic-embed-text` (embeddings) and `llama3.1:8b` (chat), and ChromaDB's persistent directory existed but was empty.
3. Instead of building a mock integration test, the real corpus was built from 116 harvested lessons (793 chunks), then embedded through Ollama into ChromaDB — a process that took about 30 seconds across 16 batches.
4. The backend was started on an alternate port and tested with curl against real HTTP endpoints: `/health`, `/api/retrieve`, `/api/chat`, `/api/gaps`, `/api/v1/retrieve`, `/metrics`.
5. The retrieve test returned ranked chunks with real similarity scores. The chat test produced a multi-paragraph LLM response citing specific lesson titles. The gap detection test correctly identified "Kubernetes pod autoscaling with KEDA" as a `missing_platform` gap and generated four GitHub search queries.
6. The gap was persisted to both the runtime JSON store and the new review markdown artifact — verifying a feature that had only been tested with unit tests minutes earlier.
7. The entire smoke test took less time than writing equivalent mock-based integration tests would have, and caught zero bugs — which was itself valuable confirmation that the unit tests were testing the right things.

## Key Insights

- **Accidental readiness is a signal, not a coincidence.** If your local environment already has the infrastructure running, that means your development workflow naturally maintains it. This is a feature of local-first architecture — the same services you use during development are available for testing without extra setup.
- **Mock tests and live tests answer different questions.** The 134 mock-based unit tests proved that each component calls the right interfaces with the right arguments. The live test proved that Ollama actually returns embeddings in the right shape, ChromaDB actually persists and queries them, and the LLM actually generates coherent answers from real context. These are not redundant — they're complementary.
- **Live tests catch integration seams that mocks hide.** A mock ChromaDB adapter doesn't test whether your metadata dict keys match what the real ChromaDB stores. A mock LLM doesn't test whether your prompt template produces coherent answers. The live test found that the `lesson_type` filter had never been tested against real indexed data — it worked, but only because the fix was minutes old.
- **The cost asymmetry favors trying live first.** Writing a mock integration test for the full RAG pipeline would require faking embeddings (768-dimensional vectors), faking ChromaDB query results with realistic similarity scores, and faking LLM responses that look grounded. Each fake adds maintenance burden and test brittleness. The live test was six curl commands.
- **"Zero bugs found" is a valid and valuable result.** The smoke test confirmed that 53 tasks across 9 hardening phases and 5 suggestion phases produced a coherent system. This confidence is worth more than any specific bug it might have caught.

## Applicability

This pattern works when:
- The infrastructure is lightweight and local (Ollama, SQLite, Redis, ChromaDB, local Kafka)
- The data volume is small enough for a full run (793 chunks embedded in ~30 seconds)
- The test is exploratory, not part of CI (CI needs deterministic, fast, repeatable tests)

This pattern does NOT replace:
- Unit tests (which run in CI without infrastructure)
- Contract tests (which verify API schemas between services)
- Load tests (which need controlled, repeatable conditions)

## Related Lessons

- [Adapter Pattern for Multi-Cloud Portability](adapter-pattern-for-multi-cloud.md) — The adapter pattern made it trivial to swap between "test with mocks" and "test with real Ollama+ChromaDB" since the same interface is used
- [RAG Corpus Chunking Strategy](rag-corpus-chunking-strategy.md) — The chunking strategy produced the 793 chunks that were embedded and queried in the live test
- [Rule-Based Gap Detection Without ML](rule-based-gap-detection.md) — Gap detection was one of the pipeline stages verified end-to-end

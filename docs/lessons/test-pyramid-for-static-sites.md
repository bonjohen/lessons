---
title: Test Pyramid for Static Sites
summary: Layer unit, integration, and acceptance tests so each catches what the others cannot in a static site with a backend API
date: 2026-05-10
phase: execution
lesson_type: architecture
status: active
tags: [testing, test-pyramid, pytest, playwright, integration, architecture]
---

# Test Pyramid for Static Sites

## The Lesson

A static site with a backend API needs three distinct testing layers — fast unit tests for logic correctness, live integration tests for service interactions, and browser-based acceptance tests for the rendered result. Each layer catches a different failure class, and skipping any one of them creates a blind spot that the others cannot cover.

## Context

Lessons Hub is a static Astro site backed by a FastAPI RAG API. The build pipeline harvests markdown from multiple repositories, validates schemas, builds a vector corpus, renders HTML, and indexes for search. The backend serves chat queries using Ollama (LLM) and ChromaDB (vector store). The system spans Python harvesting scripts, TypeScript rendering, and browser-visible output — a single testing approach cannot cover all three.

## What Happened

1. The project started with 76 pytest unit tests covering the Python harvesting pipeline: slug generation, frontmatter parsing, YAML schema validation, JSON output structure, and edge cases like duplicate IDs and missing fields.
2. The backend grew to 138 pytest tests covering health endpoints, chat flow, retrieval, adapter factories, gap detection, discovery scoring, and cloud adapter initialization — all using mocked infrastructure.
3. When Ollama and ChromaDB were running locally, live integration tests validated that the real RAG pipeline produced grounded responses with proper citations — something mocks fundamentally cannot verify.
4. After both test layers passed, 105 broken links were discovered in production by a Playwright crawler. The bug was in the Astro rendering layer (link rewriting), invisible to Python tests because they never touch the final HTML.
5. The three layers were formalized: unit (pytest, fast, no infrastructure), integration (pytest, requires live services), acceptance (Playwright, requires a running site).

## Key Insights

- **Unit tests are fast feedback, not correctness proof.** 214 passing unit tests gave confidence in individual functions but said nothing about whether the system worked end-to-end. The 105 broken links existed for weeks alongside a green test suite.

- **Each layer has a different "failure class" it catches:**
  - **Unit:** Logic errors, edge cases, regressions in individual functions (slug collision, frontmatter coercion, validation rules)
  - **Integration:** Service interaction failures (embedding dimensions mismatch, vector search returning wrong format, LLM prompt producing unusable output)
  - **Acceptance:** Rendering and routing failures (broken links, missing UI elements, dark mode CSS issues, search widget not initializing)

- **The pyramid shape still applies, but the ratios shift.** Traditional web apps have many unit tests, fewer integration tests, fewer E2E tests. A static site inverts some of this: the rendering layer is the product, so acceptance tests carry disproportionate value compared to a backend-heavy service.

- **Integration tests need a "live services available" gate.** Don't fail CI when Ollama isn't running — skip with a clear message. In local dev, run them opportunistically when services happen to be up.

- **Separate test commands prevent confusion.**
  ```bash
  python -m pytest tests/           # Unit: always runs, no deps
  python -m pytest backend/tests/   # Unit: always runs, mocked deps
  python -m pytest tests/integration/ --live  # Integration: needs services
  npx playwright test               # Acceptance: needs running site
  ```

## Examples

### Layer Comparison

| Layer | Tool | Speed | Infrastructure | What it catches |
|-------|------|-------|----------------|-----------------|
| Unit | pytest | ~5s for 214 tests | None | Logic bugs, regressions, edge cases |
| Integration | pytest + live services | ~30s | Ollama, ChromaDB | Service interaction, data format, pipeline correctness |
| Acceptance | Playwright | ~60s for 80 pages | Deployed/preview site | Broken links, UI regressions, routing errors |

### What Each Layer Missed

| Bug | Unit | Integration | Acceptance |
|-----|------|-------------|------------|
| Relative .md links broken after rendering | Cannot detect (doesn't render HTML) | Cannot detect (doesn't test the site) | **Caught** (crawled all pages) |
| LLM returning malformed citations | Mocked away | **Caught** (real LLM response) | Cannot detect (doesn't test API) |
| Duplicate slug from new repo | **Caught** (slug collision test) | Irrelevant | Would show as duplicate page |
| Pagefind search white in dark mode | Cannot detect | Cannot detect | **Caught** (smoke test) |

## Applicability

This three-layer model applies to any system where:
- The build pipeline transforms source data (content pipelines, documentation sites, generated APIs)
- External services are part of the runtime (LLMs, databases, search engines)
- The final output is browser-rendered and has inter-page navigation

It is less necessary for:
- Pure API services (unit + integration usually suffice)
- Simple single-page apps with no content transformation
- Systems where the build output is consumed programmatically, not by humans in browsers

## Related Lessons

- [Acceptance Testing with Playwright](acceptance-testing-with-playwright.md) — the acceptance layer in detail
- [Live Infrastructure for Integration Testing](live-infrastructure-for-integration-testing.md) — the integration layer in detail
- [Mock vs Live Testing Trade-offs](mock-vs-live-testing-trade-offs.md) — when to mock and when to test real services

# V2 Hardening — Physical Design Requirements

**Source documents:** `docs/prd_v2_suggestions.md`, `docs/review-2026-05-08.md`
**Project root:** `C:\Projects\lessons`
**Date:** 2026-05-09

---

## 1. System Context

### 1.1 Current State

V2 is feature-complete across 8 phases with 147 passing tests. The RAG chatbot, gap detection, GitHub discovery, multi-cloud adapters, CI/CD pipelines, and cloud infrastructure templates are all implemented. The static site deploys to GitHub Pages. The backend runs locally with Ollama + ChromaDB.

### 1.2 Scope of This Work

Harden V2 for production readiness: fix configuration and concurrency issues that block deployment, improve reliability and maintainability, and resolve remaining code review findings. No new features.

---

## 2. Requirements by Priority

### 2.1 Must-Fix — Production Blockers

| ID | Title | Source | Affected Files |
|----|-------|--------|----------------|
| R-01 | Environment-based API URL | v2_summary §11.1 | `src/components/ChatPanel.astro` |
| R-02 | Adapter factory with DEPLOYMENT_PROFILE | v2_summary §11.2, §6 reviewer note | `backend/app/api/_deps.py` |
| R-03 | Environment-based CORS origins | v2_summary §11.3 | `backend/app/main.py` |
| R-04 | File locking on JSON stores | v2_summary §11.4 | `backend/app/rag/gap_store.py`, `backend/app/discovery/lesson_extractor.py` (TODO store) |

### 2.2 Should-Fix — Reliability and Maintainability

| ID | Title | Source | Affected Files |
|----|-------|--------|----------------|
| R-05 | Structured logging | v2_summary §11.5, reviewer notes | `backend/app/api/_deps.py`, `backend/app/discovery/github_search.py`, `backend/app/rag/gap_detector.py` |
| R-06 | Async GitHub clone | v2_summary §11.6 | `backend/app/discovery/lesson_extractor.py` |
| R-07 | GitHub API rate limiting | v2_summary §11.7 | `backend/app/discovery/github_search.py` |
| R-08 | Named constants for magic numbers | v2_summary §11.8, review F-10 | `backend/app/rag/gap_detector.py`, `backend/app/rag/prompt_builder.py`, `backend/app/rag/retriever.py` |
| R-09 | Thread-safe singleton initialization | v2_summary §4 reviewer note | `backend/app/api/_deps.py` |
| R-10 | Consistent error handling between scripts | review F-06 | `scripts/harvest_lessons.py`, `scripts/validate_lessons.py`, `scripts/lesson_core.py` |
| R-11 | Deduplicate tag CSS | review F-07 | `src/components/LessonCard.astro`, `src/components/RepoCard.astro`, `src/components/TagList.astro` |
| R-12 | GitHub search error propagation | v2_summary §5 reviewer note | `backend/app/discovery/github_search.py` |

### 2.3 Nice-to-Have — Future Enhancements

| ID | Title | Source | Affected Files |
|----|-------|--------|----------------|
| R-13 | Query result caching | v2_summary §11.9 | `backend/app/rag/retriever.py`, `backend/app/rag/generator.py` |
| R-14 | Incremental re-indexing | v2_summary §11.10 | `scripts/embed_rag_corpus.py` |
| R-15 | Metrics and observability | v2_summary §11.11 | `backend/app/main.py`, new `backend/app/metrics.py` |
| R-16 | API versioning | v2_summary §11.12 | `backend/app/main.py`, router files |
| R-17 | Concept extraction stemming | v2_summary §4 reviewer note | `backend/app/rag/gap_detector.py` |
| R-18 | Data-driven platform keyword list | v2_summary §4 reviewer note | `backend/app/rag/gap_detector.py` |

---

## 3. Technical Specifications

### R-01: Environment-Based API URL

**Current behavior:** `ChatPanel.astro:15` hardcodes `const API_BASE = 'http://localhost:8000'`. Works locally, silently fails in any deployed environment.

**Required behavior:** Read the API base URL from an Astro environment variable (`PUBLIC_API_BASE` or `import.meta.env.PUBLIC_API_BASE`). Fall back to `http://localhost:8000` for local development.

**Files:** `src/components/ChatPanel.astro`
**Verification:** Set `PUBLIC_API_BASE` in `.env`, run `npm run build`, confirm the built JS references the configured URL.

### R-02: Adapter Factory with DEPLOYMENT_PROFILE

**Current behavior:** `_deps.py` always tries `OllamaAdapter` + `ChromaDBAdapter`. Cloud adapters (Bedrock, Azure OpenAI, Vertex AI, OpenSearch, Azure Search, Vertex Vector Search) exist but are never selected.

**Required behavior:** Read `DEPLOYMENT_PROFILE` env var (values: `local`, `aws`, `azure`, `gcp`). Dispatch to the correct LLM + Vector adapter pair. Default to `local` (Ollama + ChromaDB) when unset.

| Profile | LLM Adapter | Vector Adapter |
|---------|-------------|----------------|
| `local` | `OllamaAdapter` | `ChromaDBAdapter` |
| `aws` | `BedrockAdapter` | `OpenSearchAdapter` |
| `azure` | `AzureOpenAIAdapter` | `AzureSearchAdapter` |
| `gcp` | `VertexAIAdapter` | `VertexVectorSearchAdapter` |

**Files:** `backend/app/api/_deps.py`
**Verification:** Set `DEPLOYMENT_PROFILE=aws`, start the backend, confirm it initializes Bedrock + OpenSearch adapters (will fail without AWS credentials, but the adapter selection path should be testable). Add a unit test for each profile.

### R-03: Environment-Based CORS Origins

**Current behavior:** `main.py:30-35` hardcodes four localhost origins.

**Required behavior:** Read `CORS_ORIGINS` env var as a comma-separated list. Fall back to the current localhost list when unset.

**Files:** `backend/app/main.py`
**Verification:** Set `CORS_ORIGINS=https://example.com,https://staging.example.com`, start backend, confirm CORS headers use the configured origins.

### R-04: File Locking on JSON Stores

**Current behavior:** `GapStore._save()` writes JSON without locking. Concurrent API requests could corrupt `data/gaps/corpus-gaps.json`. Same issue for TODO store if it uses the same pattern.

**Required behavior:** Use `filelock` (or `fcntl`/`msvcrt` platform-native locks) to acquire an exclusive lock before read-modify-write operations. For the scope of this work, `filelock` (cross-platform, pip-installable) is the simplest option.

**Files:** `backend/app/rag/gap_store.py`, TODO store (find via grep for similar JSON read-write pattern)
**New dependency:** `filelock>=3.15`
**Verification:** Unit test that simulates concurrent writes (threading) and confirms no data corruption.

### R-05: Structured Logging

**Current behavior:** `_deps.py` silently swallows initialization errors (`except Exception: return`). `github_search.py:77` catches `httpx.HTTPError` and continues silently. Gap detection reasoning is not logged.

**Required behavior:** Add Python `logging` with a module-level logger in each affected file. Log at `WARNING` for initialization failures, `ERROR` for HTTP failures, `DEBUG` for gap detection rule evaluations. Configure a structured formatter (JSON) when `DEPLOYMENT_PROFILE` is set to a cloud value.

**Files:** `backend/app/api/_deps.py`, `backend/app/discovery/github_search.py`, `backend/app/rag/gap_detector.py`
**Verification:** Start backend, trigger a chat query, confirm log output appears with appropriate levels.

### R-06: Async GitHub Clone

**Current behavior:** `lesson_extractor.py` clones repos synchronously in the request handler. Large repos block the event loop and cause HTTP timeouts.

**Required behavior:** Run the `git clone` subprocess via `asyncio.create_subprocess_exec` with a configurable timeout (default 60s). Return a 202 Accepted with a task ID for long-running clones, or keep synchronous with a shallow clone (`--depth 1`) to reduce clone time.

**Files:** `backend/app/discovery/lesson_extractor.py`, `backend/app/api/github_discovery.py`
**Verification:** Clone a large repo (e.g., 100MB+); confirm the request doesn't block and either completes within timeout or returns 202.

### R-07: GitHub API Rate Limiting

**Current behavior:** `GitHubSearcher.search_repos()` makes unbounded requests. GitHub rate limit is 10 req/min unauthenticated, 30 req/min authenticated for search.

**Required behavior:** Track remaining rate limit from `X-RateLimit-Remaining` response header. When approaching the limit, delay or return an error with retry-after guidance. Log rate limit status.

**Files:** `backend/app/discovery/github_search.py`
**Verification:** Unit test that mocks rate-limit headers and confirms the searcher backs off appropriately.

### R-08: Named Constants for Magic Numbers

**Current behavior:** Hardcoded values scattered across backend code:
- `gap_detector.py:10` — `MIN_RELEVANCE_THRESHOLD = 0.3` (already a constant, good)
- `gap_detector.py:83` — `0.5` (related-but-unanswered threshold, inline)
- `gap_detector.py:119` — `200` (answer length threshold, inline)
- `retriever.py` — `top_k` defaults
- `prompt_builder.py` — token/context limits

**Required behavior:** Extract all inline threshold values to named constants at the top of their respective modules. Group backend configuration constants in a `backend/app/config.py` if the count exceeds 5.

**Files:** `backend/app/rag/gap_detector.py`, `backend/app/rag/retriever.py`, `backend/app/rag/prompt_builder.py`
**Verification:** Grep for bare numeric literals in backend code; confirm only trivial values (0, 1, array indices) remain.

### R-09: Thread-Safe Singleton Initialization

**Current behavior:** `_deps.py` uses module-level globals (`_retriever`, `_generator`, `_gap_store`) with no synchronization. With multiple uvicorn workers, concurrent initialization could create duplicate instances or race conditions.

**Required behavior:** Use `threading.Lock` to protect the lazy initialization in `_init()` and `get_gap_store()`. The lock should be held for the duration of the check-and-initialize sequence.

**Files:** `backend/app/api/_deps.py`
**Verification:** Unit test with concurrent threads calling `get_generator()` simultaneously; confirm only one initialization occurs.

### R-10: Consistent Error Handling Between Scripts

**Current behavior:**
- `harvest_lessons.py` uses `warn()` / `error()`, appends to lists, prints to stderr
- `validate_lessons.py` uses `log_error()` / `log_warning()` / `log_info()`, uses global counters, prints to stdout

Different naming, different output streams, different tracking mechanisms.

**Required behavior:** Both scripts use the same error/warning API. Options:
1. Extract shared logging helpers to `lesson_core.py` (`log_error()`, `log_warning()`, `log_info()`) that write to stderr and return structured results
2. Use Python's `logging` module with a shared configuration

Option 1 is simpler and aligns with the existing `lesson_core.py` shared module.

**Files:** `scripts/harvest_lessons.py`, `scripts/validate_lessons.py`, `scripts/lesson_core.py`
**Verification:** Run both scripts; confirm errors/warnings use the same format and go to the same output stream.

### R-11: Deduplicate Tag CSS

**Current behavior:** `.tags` / `.tag` CSS rules are duplicated across `LessonCard.astro`, `RepoCard.astro`, and `TagList.astro` with identical `display: flex; gap: 0.4rem; flex-wrap: wrap` and `font-size: 0.75rem`.

**Required behavior:** Extract shared tag styles to a global stylesheet (either in `BaseLayout.astro` global styles or a new `src/styles/tags.css`). Remove duplicated rules from individual components.

**Files:** `src/components/LessonCard.astro`, `src/components/RepoCard.astro`, `src/components/TagList.astro`, `src/layouts/BaseLayout.astro` (or new `src/styles/tags.css`)
**Verification:** Visual inspection — tag appearance unchanged across all pages (lessons, repos, tags).

### R-12: GitHub Search Error Propagation

**Current behavior:** `github_search.py:77` catches `httpx.HTTPError` and `continue`s, silently swallowing errors. The caller has no visibility into failed queries.

**Required behavior:** Log the error (ties into R-05). Optionally collect failed queries and include them in the response so the caller knows which queries succeeded and which failed.

**Files:** `backend/app/discovery/github_search.py`
**Verification:** Mock an HTTP error for one query; confirm it is logged and the remaining queries still execute.

### R-13: Query Result Caching

**Current behavior:** Every identical query re-embeds, re-searches, and re-generates. No caching at any layer.

**Required behavior:** Add an LRU cache (or TTL cache) for embedding results and retrieval results. Cache key: normalized query text. Cache size and TTL configurable via env vars.

**Files:** `backend/app/rag/retriever.py`, `backend/app/rag/generator.py`
**Verification:** Send the same query twice; confirm the second response returns faster (measure latency) and the LLM is not called again.

### R-14: Incremental Re-Indexing

**Current behavior:** `embed_rag_corpus.py` re-embeds all chunks on every run. Content hashes exist in `rag-chunks.json` but are not used to skip unchanged chunks.

**Required behavior:** Compare content hashes against the vector store's existing chunk metadata. Only embed and index new or changed chunks. Delete removed chunks.

**Files:** `scripts/embed_rag_corpus.py`
**Verification:** Run embed twice with no changes; confirm zero embeddings generated on the second run. Change one lesson; confirm only its chunks are re-embedded.

### R-15: Metrics and Observability

**Current behavior:** No metrics collection. No visibility into embedding latency, vector search performance, gap detection rate, or error rates.

**Required behavior:** Add lightweight metrics (counters and histograms) for key operations. Use `prometheus_client` for local/Prometheus-compatible scraping, or structured log metrics for cloud deployments.

**Files:** `backend/app/main.py` (middleware), new `backend/app/metrics.py`
**New dependency:** `prometheus_client>=0.20` (optional)
**Verification:** Hit `/metrics` endpoint; confirm counters increment with requests.

### R-16: API Versioning

**Current behavior:** All endpoints are unversioned (`/api/chat`, `/api/gaps`, etc.).

**Required behavior:** Add version prefix (`/api/v1/chat`, etc.). Keep unversioned routes as aliases for the current version to avoid breaking existing clients.

**Files:** `backend/app/main.py`, all router files in `backend/app/api/`
**Verification:** Both `/api/chat` and `/api/v1/chat` return the same response.

### R-17: Concept Extraction Stemming

**Current behavior:** `gap_detector.py:186-230` uses a stopword list for concept extraction without stemming. "deploying" and "deployment" are treated as different concepts, reducing gap-merging accuracy.

**Required behavior:** Add lightweight stemming (e.g., Porter stemmer via `nltk.stem` or the simpler `stemming` package) to `_extract_concepts()` and `_normalize_topic()`.

**Files:** `backend/app/rag/gap_detector.py`
**New dependency:** `nltk>=3.8` or `stemming>=1.0`
**Verification:** Queries about "deploying" and "deployment" produce the same gap ID.

### R-18: Data-Driven Platform Keyword List

**Current behavior:** `gap_detector.py:42-54` has a hardcoded `PLATFORM_KEYWORDS` list of 11 platforms.

**Required behavior:** Move the keyword list to a configuration file (`data/platform-keywords.json` or env var) so it can be updated without code changes.

**Files:** `backend/app/rag/gap_detector.py`, new `data/platform-keywords.json`
**Verification:** Add a new platform to the config file; confirm gap detection recognizes it without code changes.

---

## 4. Dependencies and Constraints

| Dependency | Requirements | Notes |
|------------|-------------|-------|
| `filelock>=3.15` | R-04 | Cross-platform file locking |
| `nltk>=3.8` or `stemming>=1.0` | R-17 | Optional, only if stemming is pursued |
| `prometheus_client>=0.20` | R-15 | Optional, only if metrics endpoint is pursued |

R-02 (adapter factory) is a prerequisite for cloud deployments to work end-to-end. R-01 and R-03 are also required for any non-local deployment.

R-05 (logging) should be done early as it benefits debugging of all subsequent work.

---

## 5. Out of Scope

- New features (additional gap detection rules, new adapters, new UI pages)
- Database migration (SQLite or PostgreSQL for gap/todo storage) — R-04 uses file locking as a stopgap; a full DB migration is a separate effort
- Frontend framework changes (React/Svelte migration)
- Authentication/authorization for the API
- Chunk size optimization (token estimate accuracy) — noted in v2_summary but low impact

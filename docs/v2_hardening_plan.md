# V2 Hardening — Implementation Plan

**Source document:** `docs/v2_suggestions_pdr.md`
**Project root:** `C:\Projects\lessons`
**Date:** 2026-05-09

## Work Queue Instructions

### State Transitions

Open  -->  Started  -->  Completed
              |
              └-->  Blocked  -->  Started  -->  Completed

- **Open**: Not yet begun.
- **Started**: Actively in progress. Record the start datetime (PST).
- **Completed**: Done and verified. Record the completion datetime (PST).
- **Blocked**: Cannot proceed; note the blocker in the description.

### Commit Protocol

1. Work through all tasks in a phase.
2. When every task reaches Completed, write the Phase Summary.
3. Stage and commit all changes for the phase. Do not push.
4. Proceed immediately to the next phase.

## Technology Stack (Additive)

| Concern | Choice |
|---|---|
| File locking | `filelock>=3.15` |
| Stemming | `nltk>=3.8` (punkt_tab + snowball stemmer) |
| Metrics (optional) | `prometheus_client>=0.20` |

---

## Phase 1: Configuration Externalization (R-01, R-03)

**Goal:** API URL and CORS origins read from environment variables with safe localhost defaults. No hardcoded deployment-specific values remain in source.
**Depends on:** Nothing (first phase).
**Exit condition:** `ChatPanel.astro` uses `import.meta.env.PUBLIC_API_BASE`; CORS origins configurable via `CORS_ORIGINS` env var; `npm run build` succeeds; backend starts cleanly.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 1.1 | Completed | 2026-05-09 11:58 PM (PST) | 2026-05-09 11:58 PM (PST) | In `src/components/ChatPanel.astro`, replace hardcoded `API_BASE = 'http://localhost:8000'` with `import.meta.env.PUBLIC_API_BASE \|\| 'http://localhost:8000'`. Pass via `define:vars`. |
| 1.2 | Completed | 2026-05-09 11:58 PM (PST) | 2026-05-09 11:58 PM (PST) | In `backend/app/main.py`, read `CORS_ORIGINS` env var (comma-separated), fall back to current localhost list. Replace hardcoded `allow_origins` list. |
| 1.3 | Completed | 2026-05-09 11:58 PM (PST) | 2026-05-09 11:59 PM (PST) | Add `.env.example` at project root documenting `PUBLIC_API_BASE` and `CORS_ORIGINS` with example values and comments. |
| 1.4 | Completed | 2026-05-09 11:59 PM (PST) | 2026-05-10 12:00 AM (PST) | Verify: `npm run build` succeeds with no `.env`; backend starts with default CORS; set `CORS_ORIGINS=https://example.com` and confirm CORS header changes. Run `pytest backend/tests/` green. |
| 1.5 | Completed | 2026-05-10 12:00 AM (PST) | 2026-05-10 12:01 AM (PST) | Stage and commit all Phase 1 changes. |

### Phase 1 Summary

- **Changes:** `src/components/ChatPanel.astro` reads `PUBLIC_API_BASE` from env via `define:vars`; `backend/app/main.py` reads `CORS_ORIGINS` env var (comma-separated) with localhost fallback; added `.env.example` documenting both variables.
- **Changes hosted at:** TBD
- **Commit:** `fix: externalize API URL and CORS origins (R-01, R-03)`

---

## Phase 2: Adapter Factory + Thread Safety (R-02, R-09)

**Goal:** Backend selects LLM + vector adapter pair based on `DEPLOYMENT_PROFILE` env var. Singleton initialization is thread-safe.
**Depends on:** Phase 1.
**Exit condition:** `DEPLOYMENT_PROFILE=local` uses Ollama+ChromaDB (default); `aws`/`azure`/`gcp` select the correct adapter pair; concurrent init calls don't race; new unit tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 2.1 | Completed | 2026-05-10 12:02 AM (PST) | 2026-05-10 12:02 AM (PST) | Rewrite `backend/app/api/_deps.py`: add `_INIT_LOCK = threading.Lock()`, read `DEPLOYMENT_PROFILE` env var in `_init()`, dispatch to adapter pair via dict lookup. Keep `local` as default with try/except fallback. |
| 2.2 | Completed | 2026-05-10 12:02 AM (PST) | 2026-05-10 12:02 AM (PST) | Wrap `_init()` body and `get_gap_store()` initialization in `with _INIT_LOCK:` blocks. Use double-checked locking pattern (check None outside lock, re-check inside). |
| 2.3 | Completed | 2026-05-10 12:02 AM (PST) | 2026-05-10 12:04 AM (PST) | Add `backend/tests/test_deps.py`: test each `DEPLOYMENT_PROFILE` value selects the correct adapter classes (mock cloud adapter constructors). Test thread-safety: spawn 10 threads calling `get_generator()` concurrently, assert `_init()` runs exactly once. |
| 2.4 | Completed | 2026-05-10 12:04 AM (PST) | 2026-05-10 12:04 AM (PST) | Verify: `pytest backend/tests/` all green. Backend starts with no `DEPLOYMENT_PROFILE` set (local default). |
| 2.5 | Completed | 2026-05-10 12:04 AM (PST) | 2026-05-10 12:05 AM (PST) | Stage and commit all Phase 2 changes. |

### Phase 2 Summary

- **Changes:** Rewrote `backend/app/api/_deps.py` with `_create_adapters()` factory dispatching on `DEPLOYMENT_PROFILE` env var (local/aws/azure/gcp), `threading.Lock` double-checked locking on `_init()` and `get_gap_store()`. Added `backend/tests/test_deps.py` (7 tests: profile dispatch + thread safety).
- **Changes hosted at:** TBD
- **Commit:** `feat: adapter factory with DEPLOYMENT_PROFILE dispatch and thread-safe init (R-02, R-09)`

---

## Phase 3: Structured Logging (R-05, R-12)

**Goal:** Backend emits structured log messages for initialization, errors, and gap detection. GitHub search errors are logged and propagated.
**Depends on:** Phase 2 (adapter factory changes `_deps.py`).
**Exit condition:** Startup logs show adapter initialization result; GitHub search HTTP errors appear in logs; gap detection rules log at DEBUG; all tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 3.1 | Completed | 2026-05-10 12:05 AM (PST) | 2026-05-10 12:08 AM (PST) | Add `backend/app/logging_config.py`: configure root logger with `logging.basicConfig()`, JSON formatter when `DEPLOYMENT_PROFILE` is a cloud value, human-readable otherwise. Import and call from `main.py` lifespan startup. |
| 3.2 | Completed | 2026-05-10 12:05 AM (PST) | 2026-05-10 12:08 AM (PST) | In `backend/app/api/_deps.py`: add `logger = logging.getLogger(__name__)`. Log WARNING on ChromaDB/Ollama/cloud adapter init failure (include exception message). Log INFO on successful initialization with adapter class names. |
| 3.3 | Completed | 2026-05-10 12:05 AM (PST) | 2026-05-10 12:08 AM (PST) | In `backend/app/discovery/github_search.py`: add logger. Replace bare `except httpx.HTTPError: continue` with `logger.error("GitHub search failed for query %r: %s", query, exc)` then `continue`. Add `failed_queries` list to return value so callers see which queries failed. |
| 3.4 | Completed | 2026-05-10 12:05 AM (PST) | 2026-05-10 12:08 AM (PST) | In `backend/app/rag/gap_detector.py`: add logger. Log each rule evaluation at DEBUG level with the rule name and whether it fired. Log the final gap decision (detected vs. not) at INFO. |
| 3.5 | Completed | 2026-05-10 12:08 AM (PST) | 2026-05-10 12:08 AM (PST) | Update existing tests if any assert on silent behavior. Add a test in `test_discovery.py` that mocks an HTTP error and asserts the error is logged (use `caplog` fixture). |
| 3.6 | Completed | 2026-05-10 12:08 AM (PST) | 2026-05-10 12:08 AM (PST) | Verify: `pytest backend/tests/` green. Start backend, send a chat query, confirm log output at INFO level shows adapter init and gap detection result. |
| 3.7 | Started | 2026-05-10 12:08 AM (PST) |  | Stage and commit all Phase 3 changes. |

### Phase 3 Summary

- **Changes:** Added `backend/app/logging_config.py` (JSON formatter for cloud, human-readable for local). Added loggers to `_deps.py` (init success/failure), `github_search.py` (HTTP errors + `failed_queries` return field), `gap_detector.py` (DEBUG per-rule, INFO final decision). Updated `github_discovery.py` for new `search_repos` return type. Added `TestGitHubSearcher` to `test_discovery.py`.
- **Changes hosted at:** TBD
- **Commit:** `feat: structured logging for init, discovery, and gap detection (R-05, R-12)`

---

## Phase 4: File Locking + Named Constants (R-04, R-08)

**Goal:** JSON stores use file locking for concurrent safety. Magic numbers extracted to named constants.
**Depends on:** Phase 3.
**Exit condition:** `filelock` protects gap/todo store writes; all inline thresholds are named constants; tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 4.1 | Open |  |  | Add `filelock>=3.15` to `backend/pyproject.toml` core dependencies. Run `pip install -e backend[dev]`. |
| 4.2 | Open |  |  | In `backend/app/rag/gap_store.py`: add `FileLock` import. Create lock path as `self._path.with_suffix('.lock')`. Wrap `_load()` + `_save()` sequences in `create_or_update()` and `update_status()` with `with FileLock(self._lock_path):`. |
| 4.3 | Open |  |  | Find TODO store (grep for similar JSON read-write pattern in `backend/app/discovery/`). Apply same `FileLock` pattern. |
| 4.4 | Open |  |  | Add concurrent write test in `backend/tests/test_gap_store_locking.py`: 10 threads each calling `create_or_update()` with unique gaps, assert final file has all 10 records and valid JSON. |
| 4.5 | Open |  |  | In `backend/app/rag/gap_detector.py`: extract `0.5` → `RELATED_BUT_UNANSWERED_THRESHOLD = 0.5`, `200` → `MIN_ANSWER_LENGTH_FOR_WEAK_EVIDENCE = 200`, `3` → `MIN_CHUNKS_FOR_RELATED = 3`. Replace inline usages. |
| 4.6 | Open |  |  | In `backend/app/rag/retriever.py` and `backend/app/rag/prompt_builder.py`: extract any inline numeric defaults (top_k, token limits) to named constants at module top. |
| 4.7 | Open |  |  | Verify: `pytest backend/tests/` green. `ruff check backend/` clean. |
| 4.8 | Open |  |  | Stage and commit all Phase 4 changes. |

### Phase 4 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `fix: file locking on JSON stores and named constants for thresholds (R-04, R-08)`

---

## Phase 5: GitHub Discovery Hardening (R-06, R-07)

**Goal:** GitHub clone is non-blocking with timeout. API rate limits are respected.
**Depends on:** Phase 3 (logging in github_search.py).
**Exit condition:** Clone uses `--depth 1` with configurable timeout; rate-limit headers tracked; tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 5.1 | Open |  |  | In `backend/app/discovery/lesson_extractor.py`: change `git clone` to `git clone --depth 1`. Add configurable timeout (env var `CLONE_TIMEOUT_SECONDS`, default 60). Use `asyncio.create_subprocess_exec` if the function is async, or `subprocess.run(timeout=...)` if sync. |
| 5.2 | Open |  |  | In `backend/app/discovery/github_search.py`: after each `httpx.get()`, read `X-RateLimit-Remaining` and `X-RateLimit-Reset` from response headers. If remaining < 3, log a warning and `time.sleep()` until reset time. |
| 5.3 | Open |  |  | Add test in `backend/tests/test_discovery.py`: mock `httpx.get` returning rate-limit headers with remaining=1, assert the searcher pauses (mock `time.sleep` and verify it's called). |
| 5.4 | Open |  |  | Add test for clone timeout: mock `subprocess.run` raising `subprocess.TimeoutExpired`, assert the extractor returns an error result instead of crashing. |
| 5.5 | Open |  |  | Verify: `pytest backend/tests/` green. `ruff check backend/` clean. |
| 5.6 | Open |  |  | Stage and commit all Phase 5 changes. |

### Phase 5 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `fix: shallow clone with timeout and GitHub API rate limiting (R-06, R-07)`

---

## Phase 6: Script and Frontend Cleanup (R-10, R-11)

**Goal:** Harvest and validate scripts use consistent error handling. Tag CSS deduplicated.
**Depends on:** Nothing (independent of backend phases, but sequenced here to avoid merge conflicts).
**Exit condition:** Both scripts log to stderr with same format; tag styles live in one place; visual appearance unchanged; `pytest tests/` green.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 6.1 | Open |  |  | In `scripts/lesson_core.py`: add shared `log_error(msg)`, `log_warning(msg)`, `log_info(msg)` functions that write to stderr with `[ERROR]`/`[WARNING]`/`[INFO]` prefixes and track counts in a module-level `LogStats` dataclass. |
| 6.2 | Open |  |  | In `scripts/harvest_lessons.py`: replace `warn()`/`error()` with `lesson_core.log_warning()`/`lesson_core.log_error()`. Remove old helper functions and list-based tracking. |
| 6.3 | Open |  |  | In `scripts/validate_lessons.py`: replace `log_error()`/`log_warning()`/`log_info()` with `lesson_core.log_error()`/`lesson_core.log_warning()`/`lesson_core.log_info()`. Remove old helper functions and global counter variables. Change print calls from stdout to use the shared helpers. |
| 6.4 | Open |  |  | Extract shared tag CSS: create `src/styles/tags.css` with `.tags { display: flex; gap: 0.4rem; flex-wrap: wrap; }` and `.tag { font-size: 0.75rem; }`. Import in `BaseLayout.astro` via `import '../styles/tags.css'`. |
| 6.5 | Open |  |  | Remove duplicated `.tags` and `.tag` style blocks from `src/components/LessonCard.astro`, `src/components/RepoCard.astro`, `src/components/TagList.astro` (remove the `.tag-list` equivalent rule too). |
| 6.6 | Open |  |  | Verify: `pytest tests/` green. `npm run build` succeeds. Visual spot-check of tag styling on lessons, repos, and tags pages. |
| 6.7 | Open |  |  | Stage and commit all Phase 6 changes. |

### Phase 6 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `fix: consistent error handling and deduplicated tag CSS (R-10, R-11)`

---

## Phase 7: Caching and Incremental Indexing (R-13, R-14)

**Goal:** Repeated queries return cached results. Embedding runs skip unchanged chunks.
**Depends on:** Phase 4 (named constants in retriever/prompt_builder).
**Exit condition:** Second identical query skips LLM call; incremental embed only processes changed chunks; tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 7.1 | Open |  |  | In `backend/app/rag/retriever.py`: add `functools.lru_cache` on a `_cached_retrieve(query_text)` method (or use `cachetools.TTLCache` with configurable TTL via `CACHE_TTL_SECONDS` env var, default 300). Cache key is the query string. |
| 7.2 | Open |  |  | In `backend/app/rag/generator.py`: cache the full generate result keyed on query text. Set max cache size via `CACHE_MAX_SIZE` env var (default 128). |
| 7.3 | Open |  |  | In `scripts/embed_rag_corpus.py`: on startup, load existing chunk metadata from vector store (chunk_id → content_hash). Compare against `rag-chunks.json`. Embed only chunks where hash differs or chunk is new. Delete chunks no longer in the corpus. Log counts: added, updated, unchanged, deleted. |
| 7.4 | Open |  |  | Add test: mock retriever, call generator twice with same query, assert LLM `chat()` called only once. |
| 7.5 | Open |  |  | Add test: embed script with pre-existing chunks (mock vector adapter), change one chunk's content hash, verify only that chunk is re-embedded. |
| 7.6 | Open |  |  | Verify: `pytest backend/tests/` and `pytest tests/` green. |
| 7.7 | Open |  |  | Stage and commit all Phase 7 changes. |

### Phase 7 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `feat: query result caching and incremental re-indexing (R-13, R-14)`

---

## Phase 8: Gap Detection Improvements (R-17, R-18)

**Goal:** Concept extraction uses stemming for better gap merging. Platform keyword list is data-driven.
**Depends on:** Phase 4 (named constants in gap_detector.py).
**Exit condition:** "deploying" and "deployment" produce the same gap ID; platform keywords loaded from config file; tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 8.1 | Open |  |  | Add `nltk>=3.8` to `backend/pyproject.toml`. In `backend/app/rag/gap_detector.py`: import `nltk.stem.SnowballStemmer`, create stemmer instance. Apply stemming in `_extract_concepts()` and `_normalize_topic()`. |
| 8.2 | Open |  |  | Create `data/platform-keywords.json` with the current 11 keywords. In `gap_detector.py`: load the list from the JSON file at module init (with fallback to hardcoded list if file missing). Remove the hardcoded `PLATFORM_KEYWORDS` list. |
| 8.3 | Open |  |  | Update `backend/tests/test_gap_detector.py`: add test that "deploying containers" and "container deployment" produce the same normalized topic and gap ID. Add test that a keyword added to `data/platform-keywords.json` is recognized by the detector. |
| 8.4 | Open |  |  | Verify: `pytest backend/tests/` green. `ruff check backend/` clean. |
| 8.5 | Open |  |  | Stage and commit all Phase 8 changes. |

### Phase 8 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `feat: stemmed concept extraction and data-driven platform keywords (R-17, R-18)`

---

## Phase 9: Metrics, Observability, and API Versioning (R-15, R-16)

**Goal:** Backend exposes a `/metrics` endpoint with request counters and latency histograms. API routes available under `/api/v1/` prefix.
**Depends on:** Phase 3 (logging infrastructure).
**Exit condition:** `/metrics` returns Prometheus-format metrics; `/api/v1/chat` works identically to `/api/chat`; unversioned routes still work; tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 9.1 | Open |  |  | Add `prometheus_client>=0.20` to `backend/pyproject.toml` optional deps group `[metrics]`. |
| 9.2 | Open |  |  | Create `backend/app/metrics.py`: define Counter (`requests_total` with labels method+path+status), Histogram (`request_duration_seconds`), Counter (`gap_detections_total`), Counter (`cache_hits_total`). |
| 9.3 | Open |  |  | In `backend/app/main.py`: add Starlette middleware that increments counters and records duration for every request. Add `GET /metrics` endpoint using `prometheus_client.generate_latest()`. Guard with try/except ImportError so the backend runs without prometheus_client installed. |
| 9.4 | Open |  |  | In `backend/app/main.py`: mount all existing routers under both `/api/` (current) and `/api/v1/` (versioned). Use `app.include_router(router, prefix="/api/v1")` for the versioned mount. |
| 9.5 | Open |  |  | Add tests: `GET /metrics` returns 200 with `requests_total` in body (or 404 if prometheus not installed). `POST /api/v1/chat` returns same schema as `POST /api/chat`. |
| 9.6 | Open |  |  | Verify: `pytest backend/tests/` green. `ruff check backend/` clean. |
| 9.7 | Open |  |  | Stage and commit all Phase 9 changes. |

### Phase 9 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `feat: Prometheus metrics endpoint and API v1 versioned routes (R-15, R-16)`

---

## Requirement → Phase Cross-Reference

| Req | Title | Phase |
|-----|-------|-------|
| R-01 | Environment-based API URL | 1 |
| R-02 | Adapter factory with DEPLOYMENT_PROFILE | 2 |
| R-03 | Environment-based CORS origins | 1 |
| R-04 | File locking on JSON stores | 4 |
| R-05 | Structured logging | 3 |
| R-06 | Async GitHub clone | 5 |
| R-07 | GitHub API rate limiting | 5 |
| R-08 | Named constants for magic numbers | 4 |
| R-09 | Thread-safe singleton init | 2 |
| R-10 | Consistent error handling | 6 |
| R-11 | Deduplicate tag CSS | 6 |
| R-12 | GitHub search error propagation | 3 |
| R-13 | Query result caching | 7 |
| R-14 | Incremental re-indexing | 7 |
| R-15 | Metrics and observability | 9 |
| R-16 | API versioning | 9 |
| R-17 | Concept extraction stemming | 8 |
| R-18 | Data-driven platform keywords | 8 |

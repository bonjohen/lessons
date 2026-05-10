# Lessons Hub V2 — Implementation Summary

**Source plan:** `docs/lessons_hub_v2_plan.md` | **PDR:** `docs/PDR_V2.md`
**Phases completed:** 8 of 8 | **Total tests:** 178 (102 backend + 76 project)

This document summarizes the V2 implementation across all eight phases and explains the architecture, key design decisions, and areas that warrant attention during code review.

---

## 1. What V2 Adds

V1 was a static Astro site that harvests markdown lessons from GitHub repos and renders them as browsable pages with Pagefind search.

V2 adds:
- **RAG chatbot** — ask questions, get grounded answers citing specific lessons
- **Gap detection** — queries the corpus can't answer create trackable gap records
- **GitHub discovery** — gaps produce candidate external repos, scored and ranked
- **Candidate lesson extraction** — generates draft lessons from discovered repos with attribution
- **Multi-cloud deployment** — AWS, Azure, and GCP infrastructure alongside the existing GitHub Pages pipeline
- **CI/CD hardening** — pytest, ruff, corpus validation in CI; staging/production split with approval gates

---

## 2. Architecture Overview

```
                          +------------------+
                          |   Astro Static   |
                          |   Site (Pages)   |
                          +--------+---------+
                                   |
                          +--------v---------+
                          |  ChatPanel.astro |
                          |  (client-side JS)|
                          +--------+---------+
                                   |
                          POST /api/chat
                                   |
                 +-----------------v-----------------+
                 |        FastAPI Backend            |
                 |                                   |
                 |  +-------+  +----------+  +-----+ |
                 |  |  RAG  |  |   Gap    |  | Disc| |
                 |  |Pipeline|  |Detection |  |overy| |
                 |  +---+---+  +----+-----+  +--+--+ |
                 |      |           |            |    |
                 |  +---v-----------v------------v--+ |
                 |  |     Adapter Layer             | |
                 |  |  LLM: Ollama|Bedrock|Azure|GCP| |
                 |  | Vector: Chroma|OS|AzSearch|Vtx| |
                 |  +-------------------------------+ |
                 +-----------------------------------+
```

### Key boundaries

| Concern | Owner | Notes |
|---------|-------|-------|
| Lesson harvesting, validation, static pages | Existing V1 pipeline | Unchanged |
| RAG corpus building | `scripts/build_rag_corpus.py` | Chunks `lessons.json` by H2 headings |
| Embedding + indexing | `scripts/embed_rag_corpus.py` | Ollama locally; Bedrock/Azure/Vertex in cloud |
| Chat, retrieval, gap detection | `backend/app/` | FastAPI, runs separately from Astro |
| GitHub discovery + lesson extraction | `backend/app/discovery/` | Triggered from gap records |
| Infrastructure | `infra/{aws,azure,gcp}/` | CloudFormation, Bicep, shell scripts |
| CI/CD | `.github/workflows/` | 5 workflow files |

---

## 3. RAG Pipeline (Phases 1-2)

### Corpus building (`scripts/build_rag_corpus.py`)

Reads `src/content/generated/lessons.json` (produced by V1 harvest) and splits each lesson's markdown into chunks at H2 boundaries. Each chunk carries:

- **Stable ID:** `{lesson_id}-{chunk_index}` — deterministic across rebuilds
- **Heading path:** breadcrumb trail (e.g. "Git Basics > Branching") for citation context
- **Content hash:** SHA-256 of chunk text, enabling future incremental re-indexing
- **Token estimate:** `word_count * 0.75`, capped at minimum 1

The intro content (before the first H2) becomes chunk 0. Output: `data/rag-chunks.json` (793 chunks from 116 lessons) + `data/rag-manifest.json` with statistics.

**Reviewer note:** The token estimate is approximate. Chunks can exceed 5000 tokens; the validator warns but doesn't fail. If context window limits become an issue, tighten this.

### Retrieval and generation

```
Query → LLMAdapter.embed(query) → VectorAdapter.query(embedding, top_k=8)
     → deduplicate lessons → PromptBuilder.build_chat_messages(query, chunks)
     → LLMAdapter.chat(messages) → answer + cited lessons
```

The **Retriever** (`backend/app/rag/retriever.py`) embeds the query and searches the vector store. The **Generator** (`backend/app/rag/generator.py`) wraps the retriever, builds a grounded prompt with the retrieved chunks, calls the LLM, and extracts lesson citations from the response.

The **PromptBuilder** (`backend/app/rag/prompt_builder.py`) constructs a system prompt that instructs the LLM to only use provided excerpts, cite by title, and list sources with URLs.

### Dependency injection (`backend/app/api/_deps.py`)

Core components (Retriever, Generator, GapStore) are lazy-loaded singletons. If ChromaDB or Ollama are unavailable at startup, the singletons remain `None` and the API returns graceful fallback responses. This allows the static site to work independently of the backend.

**Reviewer note:** No logging on initialization failure — silent `None` makes debugging harder. No thread-safety on the global singletons (acceptable for single-worker dev, but needs attention for production with multiple workers).

---

## 4. Gap Detection (Phase 3)

### Detection rules (`backend/app/rag/gap_detector.py`)

Seven rules evaluate whether a query exposed a corpus gap:

| # | Rule | Signal |
|---|------|--------|
| 1 | No chunks above relevance threshold (0.3) | `max(similarity_scores) < 0.3` |
| 2 | Fewer than 2 distinct lessons above threshold | Thin coverage |
| 3 | Chunks exist but scores are 0.0-0.5 with 3+ results | Related but unanswered |
| 4 | Answer contains weak-answer language | 9 phrase patterns ("does not appear", "no relevant", etc.) |
| 5 | User asks about missing material | Pattern match + weak answer |
| 6 | Platform-specific query with no matches | 14 platform keywords (AWS, Docker, K8s, etc.) |
| 7 | Long answer from limited evidence | >200 chars answer with <2 above-threshold chunks |

Multiple rules can fire simultaneously. The gap record captures which rules triggered (`detection_reasons`), the classified gap type (one of 8: `missing_topic`, `thin_coverage`, `missing_platform`, `missing_example`, etc.), and up to 5 suggested GitHub search queries generated from extracted concepts.

**Reviewer note:** Thresholds (0.3, 0.5, 200) are hardcoded constants. The concept extraction uses a stopword list without stemming/lemmatization — "deploying" won't match "deployment". The platform keyword list is static; consider making it data-driven.

### Gap storage (`backend/app/rag/gap_store.py`)

JSON-backed CRUD at `data/gaps/corpus-gaps.json`. Gaps merge by ID (MD5 hash of normalized topic, first 12 chars) — repeated queries about the same topic append to `additional_queries` rather than creating duplicates.

Status transitions: `open` -> `searching` -> `candidates_found` -> `lessons_staged` -> `owner_coordination_needed` -> `resolved` | `closed_no_action`.

**Reviewer note:** No file locking — concurrent writes could corrupt JSON. Acceptable for single-user local dev; needs migration to SQLite or a real DB for multi-user deployment.

---

## 5. GitHub Discovery (Phase 4)

### Three-stage pipeline

**Stage 1 — Search** (`backend/app/discovery/github_search.py`): Takes the gap's `suggested_github_queries`, runs them against the GitHub Repos API with optional auth token, deduplicates by `full_name`, sorts by stars.

**Stage 2 — Score** (`backend/app/discovery/candidate_scorer.py`): 10 additive criteria (topic relevance, docs presence, CI/CD topics, stars, license, recency, etc.) produce a 0-1 score with human-readable reason strings. The scoring is transparent — you can see exactly why a repo scored 0.72.

**Stage 3 — Extract** (`backend/app/discovery/lesson_extractor.py`): Detects extractable content (docs, CI configs, Dockerfiles, ADRs), generates a candidate lesson markdown with full frontmatter, a summary from the README, an evidence list, and an attribution block. Always creates a coordination TODO.

The **attribution block** thanks the source project, includes a no-endorsement disclaimer, and links to the source. The **TODO** tracks the coordination step — reaching out to the source project owner before incorporating.

**Reviewer note:** Clone happens synchronously in the request handler. Large repos will cause request timeouts. The GitHub API has rate limits (60 req/min authenticated); no rate limiting logic is implemented. Error handling in the search stage swallows `httpx.HTTPError` silently.

### API surface

| Endpoint | Purpose |
|----------|---------|
| `POST /api/chat` | Q&A with automatic gap detection |
| `POST /api/retrieve` | Raw chunk retrieval without generation |
| `GET /api/gaps` | List gaps with status/candidate filters |
| `GET /api/gaps/{id}` | Get single gap |
| `POST /api/gaps` | Create/update gap |
| `PATCH /api/gaps/{id}/status` | Transition gap status |
| `POST /api/github/search` | Search GitHub for a gap's suggested queries |
| `POST /api/github/harvest-candidate` | Clone repo, extract lesson, create TODO |
| `GET /api/todos` | List coordination TODOs |
| `PATCH /api/todos/{id}` | Update TODO status |
| `GET /health` | Health check with version and corpus status |

---

## 6. Adapter Layer (Phases 1-2, 6-8)

All cloud-specific dependencies use **lazy imports** — `import boto3` happens inside `__init__`, not at module level. This means:
- The base backend runs without any cloud SDK installed
- CI tests mock at the `sys.modules` level before importing adapters
- Adding a new provider doesn't affect existing ones

### LLM adapters (`backend/app/adapters/llm/`)

| Adapter | Embed Model | Chat Model | Import |
|---------|------------|------------|--------|
| `OllamaAdapter` | nomic-embed-text | llama3.1:8b | `ollama` |
| `BedrockAdapter` | Titan Embed Text v2 | Claude 3 Haiku | `boto3` (lazy) |
| `AzureOpenAIAdapter` | text-embedding-3-small | gpt-4o-mini | `openai` (lazy) |
| `VertexAIAdapter` | text-embedding-004 | Gemini 1.5 Flash | `vertexai` (lazy) |

All implement `LLMAdapter` (abstract base): `embed(texts) -> list[list[float]]` and `chat(messages) -> str`.

### Vector adapters (`backend/app/adapters/vector/`)

| Adapter | Backend | Import |
|---------|---------|--------|
| `ChromaDBAdapter` | ChromaDB (local, cosine HNSW) | `chromadb` |
| `OpenSearchAdapter` | OpenSearch Serverless (AWS) | `opensearchpy`, `boto3` (lazy) |
| `AzureSearchAdapter` | Azure AI Search | `azure.search.documents` (lazy) |
| `VertexVectorSearchAdapter` | Vertex AI Vector Search | `google.cloud.aiplatform` (lazy) |

All implement `VectorAdapter` (abstract base): `index_chunks`, `query`, `delete_collection`, `count`.

**Reviewer note:** Adapter selection is currently done in `_deps.py` by trying to connect to Ollama/ChromaDB. There is no `DEPLOYMENT_PROFILE` env var dispatch yet — the adapters exist but aren't wired into a factory. This is the main gap before cloud deployment actually works end-to-end.

---

## 7. Frontend Chat UI (Phase 2)

`src/components/ChatPanel.astro` is a client-side component with vanilla JS. It:
- Checks backend health on load (shows corpus chunk count)
- Sends queries to `POST /api/chat` with `top_k=8`
- Renders answers with cited lessons (linked, with similarity % badges)
- Shows a gap-detected notice via `src/components/CorpusGapNotice.astro`
- Falls back gracefully if the backend is unreachable

**Reviewer note:** The API base URL is hardcoded to `http://localhost:8000`. This needs to be environment-injected for any non-local deployment. The component works fine for local development but will silently fail in production without this fix.

---

## 8. CI/CD (Phase 5)

### Workflow structure

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-deploy.yml` | push/PR to main, daily, manual | Full pipeline: lint + test + harvest + build + deploy to GitHub Pages |
| `deploy-staging.yml` | push to main | Build + deploy to staging environment + smoke tests |
| `deploy-production.yml` | after staging succeeds, or manual | Deploy to production with environment approval gate |
| `deploy-aws.yml` | manual (staging/production) | ECR + ECS + S3 + CloudFront |
| `deploy-azure.yml` | manual (staging/production) | ACR + Container Apps + Static Web Apps |
| `deploy-gcp.yml` | manual (staging/production) | Artifact Registry + Cloud Run + Cloud Storage |

### CI checks added in V2

- `ruff check backend/` and `ruff format --check backend/` (import sorting, line length, unused imports)
- `pytest tests/` (76 project tests: harvesting, validation, slugs, frontmatter)
- `pytest backend/tests/` (102 backend tests: health, chat, adapters, gaps, discovery, AWS/Azure/GCP)
- `npm run corpus && npm run validate:corpus` (RAG corpus build + validation)
- PR trigger added (build-only, no deploy)
- Deploy job gated with `if: github.event_name != 'pull_request'`

---

## 9. Infrastructure (Phases 6-8)

### AWS (`infra/aws/cloudformation.yml`)

Full VPC (10.0.0.0/16, 4 subnets across 2 AZs), ALB, ECS Fargate cluster, ECR with lifecycle policy, CloudFront distribution with S3 origin + ALB backend origin (cache bypass for `/api/*`), IAM roles with Bedrock + OpenSearch policies, CloudWatch Logs, and GitHub OIDC provider for keyless CI/CD auth.

Production: 2 ECS replicas, 30-day log retention, Container Insights enabled.
Staging: 1 replica, 7-day retention.

### Azure (`infra/azure/main.bicep`)

Container Apps with Log Analytics, ACR, Static Web Apps (Free tier), Azure AI Search (Free tier), Azure OpenAI with two model deployments (embedding + chat), Key Vault. Container Apps scale to zero in staging.

### GCP (`infra/gcp/deploy.sh`)

Shell script that enables APIs, creates Artifact Registry, Cloud Storage bucket with static web hosting, Workload Identity Pool/Provider for GitHub OIDC, and a service account with roles for Cloud Run, Artifact Registry, Storage, and Vertex AI.

**Reviewer note:** All three cloud stacks use OIDC/Workload Identity Federation — no long-lived credentials in GitHub secrets. The infra templates create the resources but the actual adapter wiring (which adapter to use based on `DEPLOYMENT_PROFILE`) is not yet implemented in `_deps.py`. This is the remaining integration work.

---

## 10. Test Coverage

| Test File | Count | What it covers |
|-----------|-------|----------------|
| `tests/test_repo_config.py` | 10 | repos.yml parsing |
| `tests/test_lesson_parsing.py` | 12 | Frontmatter normalization |
| `tests/test_slug_generation.py` | 6 | Lesson ID generation |
| `tests/test_validation.py` | 18 | Validation rules (error/warning) |
| `tests/test_corpus_builder.py` | 12 | H2 chunking, stable IDs, metadata |
| `tests/test_harvest_integration.py` | 6 | End-to-end harvest |
| `tests/test_validate_integration.py` | 12 | Validation integration |
| `backend/tests/test_health.py` | 5 | Health endpoint |
| `backend/tests/test_chat.py` | 5 | Chat endpoint with mocked generator |
| `backend/tests/test_adapters.py` | 6 | ChromaDB adapter CRUD |
| `backend/tests/test_gap_detector.py` | 17 | All 7 detection rules, topic normalization |
| `backend/tests/test_discovery.py` | 11 | Scoring, extraction, attribution, TODOs |
| `backend/tests/test_aws_adapters.py` | 11 | Bedrock + OpenSearch with mocked boto3 |
| `backend/tests/test_azure_adapters.py` | 8 | Azure OpenAI + AI Search with mocked SDK |
| `backend/tests/test_gcp_adapters.py` | 8 | Vertex AI + Vector Search with mocked SDK |

All cloud adapter tests use `sys.modules.setdefault()` to inject mock modules before importing the adapters, avoiding any dependency on cloud SDKs in the test environment.

---

## 11. Known Limitations and Future Work

### Must-fix before production

1. **API URL hardcoded** in `ChatPanel.astro` to `localhost:8000` — needs environment-based injection
2. **No adapter factory** — `_deps.py` always tries Ollama/ChromaDB; needs `DEPLOYMENT_PROFILE` dispatch to select cloud adapters
3. **CORS origins hardcoded** in `main.py` to localhost — needs env-based configuration
4. **No file locking** on JSON gap/todo stores — will corrupt under concurrent writes

### Should-fix

5. **No logging** in `_deps.py` initialization, GitHub search errors, or gap detection reasoning
6. **Synchronous GitHub clone** in request handler — large repos will timeout
7. **No rate limiting** for GitHub API calls (60/min authenticated limit)
8. **Magic numbers** (similarity thresholds, token limits) should be named constants or config

### Nice-to-have

9. **Caching** for repeated identical queries
10. **Incremental re-indexing** using content hashes (infrastructure exists, not wired)
11. **Metrics/observability** (embedding latency, vector search p99, gap detection rate)
12. **API versioning** strategy

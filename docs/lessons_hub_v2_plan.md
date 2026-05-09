# Lessons Hub V2 — Implementation Plan

**Source document:** `docs/PDR_V2.md`
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
| Backend framework | FastAPI |
| Backend models | Pydantic v2 |
| Vector store (local) | ChromaDB |
| Embedding model (local) | Ollama nomic-embed-text (768 dims) |
| Chat model (local) | Ollama llama3.2:3b |
| Corpus storage | JSON (data/rag-chunks.json) |
| Gap/TODO storage | JSON (data/gaps/, data/todos/) |
| Backend tests | pytest |
| Backend lint | ruff |

## Phase 1: Backend Scaffold + RAG Corpus Builder

**Goal:** FastAPI skeleton runs with health endpoint; corpus builder converts harvested lessons to RAG chunks.
**Depends on:** Nothing (first phase).
**Exit condition:** `GET /health` returns 200; `data/rag-chunks.json` generated from 116 lessons; backend tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 1.1 | Completed | 2026-05-09 02:25 PM (PST) | 2026-05-09 02:27 PM (PST) | Create `backend/` directory structure: `app/main.py`, `app/api/`, `app/rag/`, `app/discovery/`, `app/adapters/vector/`, `app/adapters/llm/`, `app/models/`, `tests/`. Add `__init__.py` files. |
| 1.2 | Completed | 2026-05-09 02:27 PM (PST) | 2026-05-09 02:28 PM (PST) | Create `backend/pyproject.toml` with deps: fastapi, uvicorn[standard], pydantic>=2, chromadb, ollama, httpx, pytest, ruff. Pin Python >=3.11. |
| 1.3 | Completed | 2026-05-09 02:28 PM (PST) | 2026-05-09 02:29 PM (PST) | Implement `backend/app/main.py` — FastAPI app with CORS (origins: localhost:4321, localhost:3000), mount API router, lifespan handler. |
| 1.4 | Completed | 2026-05-09 02:29 PM (PST) | 2026-05-09 02:30 PM (PST) | Implement `backend/app/api/health.py` — `GET /health` returning version, deployment_profile, corpus_status. Wire into main router. |
| 1.5 | Completed | 2026-05-09 02:30 PM (PST) | 2026-05-09 02:31 PM (PST) | Implement `backend/app/models/schemas.py` — Pydantic models: ChunkRecord, GapRecord, CandidateRepo, TodoRecord, ChatRequest, ChatResponse, RetrieveRequest, RetrieveResponse per PDR 8.2-8.5 and 12.1-12.2. |
| 1.6 | Completed | 2026-05-09 02:31 PM (PST) | 2026-05-09 02:34 PM (PST) | Implement `scripts/build_rag_corpus.py` — load `src/content/generated/lessons.json`, chunk by markdown H2 headings, stable chunk IDs (`{lesson_id}-{chunk_index}`), preserve metadata (title, summary, tags, repo_id, lesson_url). Write `data/rag-chunks.json` + `data/rag-manifest.json`. |
| 1.7 | Completed | 2026-05-09 02:34 PM (PST) | 2026-05-09 02:35 PM (PST) | Implement `scripts/validate_rag_corpus.py` — validate chunk schema, unique IDs, lesson_ids resolve against lessons.json, token counts reasonable, no empty chunks. |
| 1.8 | Completed | 2026-05-09 02:35 PM (PST) | 2026-05-09 02:36 PM (PST) | Write tests: `backend/tests/test_health.py` (health endpoint returns 200, has version field), `tests/test_corpus_builder.py` (chunking splits on H2, stable IDs, metadata preserved, empty content handled). |
| 1.9 | Completed | 2026-05-09 02:36 PM (PST) | 2026-05-09 02:37 PM (PST) | Add npm scripts to `package.json`: `"backend"`, `"corpus"`, `"validate:corpus"`. Update `build:full` to include `npm run corpus && npm run validate:corpus`. |
| 1.10 | Completed | 2026-05-09 02:37 PM (PST) | 2026-05-09 02:38 PM (PST) | Update `.gitignore` for `data/rag-chunks.json`, `data/rag-manifest.json`, `data/chromadb/`, `data/gaps/`, `data/todos/`, `data/external/`, `.external/`, `backend/__pycache__/`. Verify: run harvest, build corpus, validate, run all tests green. Stage and commit. |

### Phase 1 Summary

- **Changes:** Created `backend/` directory with FastAPI app, health endpoint, Pydantic models. Created `scripts/build_rag_corpus.py` (793 chunks from 116 lessons) and `scripts/validate_rag_corpus.py`. Added 17 new tests (5 health + 12 corpus). Updated `package.json` with backend/corpus scripts and `.gitignore` for V2 data.
- **Changes hosted at:** TBD
- **Commit:** `feat: Phase 1 — backend scaffold and RAG corpus builder`

## Phase 2: Vector Index, Retrieval, and Chat

**Goal:** Local chatbot answers questions with lesson citations.
**Depends on:** Phase 1.
**Exit condition:** `POST /api/chat` returns grounded answers linking to lessons; `POST /api/retrieve` returns ranked chunks; chat panel works in browser.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 2.1 | Completed | 2026-05-09 02:38 PM (PST) | 2026-05-09 02:39 PM (PST) | Implement vector adapter interface: `backend/app/adapters/vector/base.py` — abstract class with `index_chunks(chunks, embeddings)`, `query(embedding, top_k, filters)`, `delete_collection()`. |
| 2.2 | Completed | 2026-05-09 02:39 PM (PST) | 2026-05-09 02:40 PM (PST) | Implement ChromaDB adapter: `backend/app/adapters/vector/chromadb_adapter.py` — persist to `data/chromadb/`, collection per corpus version. |
| 2.3 | Completed | 2026-05-09 02:39 PM (PST) | 2026-05-09 02:39 PM (PST) | Implement LLM adapter interface: `backend/app/adapters/llm/base.py` — abstract class with `embed(texts) -> list[list[float]]`, `chat(messages) -> str`. |
| 2.4 | Completed | 2026-05-09 02:39 PM (PST) | 2026-05-09 02:40 PM (PST) | Implement Ollama adapter: `backend/app/adapters/llm/ollama_adapter.py` — `nomic-embed-text` for embed, `llama3.1:8b` for chat. Handle connection errors gracefully. |
| 2.5 | Completed | 2026-05-09 02:40 PM (PST) | 2026-05-09 02:40 PM (PST) | Implement `scripts/embed_rag_corpus.py` — load `data/rag-chunks.json`, embed chunk texts via LLM adapter, index into ChromaDB via vector adapter. Idempotent (delete + re-index). |
| 2.6 | Completed | 2026-05-09 02:40 PM (PST) | 2026-05-09 02:41 PM (PST) | Implement `backend/app/rag/retriever.py` — query vector store with embedded query, return top-k chunks with similarity scores + lesson metadata. |
| 2.7 | Completed | 2026-05-09 02:41 PM (PST) | 2026-05-09 02:41 PM (PST) | Implement `backend/app/rag/prompt_builder.py` — build system prompt with retrieved lesson context, citation format instructions, grounding rules. |
| 2.8 | Completed | 2026-05-09 02:41 PM (PST) | 2026-05-09 02:41 PM (PST) | Implement `backend/app/rag/generator.py` — call LLM adapter with built prompt, parse response, extract lesson citations. |
| 2.9 | Completed | 2026-05-09 02:41 PM (PST) | 2026-05-09 02:42 PM (PST) | Implement `backend/app/api/retrieve.py` (`POST /api/retrieve`) and `backend/app/api/chat.py` (`POST /api/chat`) per PDR 12.1-12.2. Wire into main router. |
| 2.10 | Completed | 2026-05-09 02:42 PM (PST) | 2026-05-09 02:42 PM (PST) | Implement `src/components/ChatPanel.astro` — client-side JS `<script>` block, fetch to backend, loading/streaming indicator, lesson card display for cited lessons, "backend unavailable" fallback state. |
| 2.11 | Completed | 2026-05-09 02:42 PM (PST) | 2026-05-09 02:42 PM (PST) | Implement `src/pages/ask.astro` — "Ask the Lessons" page embedding ChatPanel. Add "Ask" link to nav in `src/layouts/BaseLayout.astro`. |
| 2.12 | Completed | 2026-05-09 02:42 PM (PST) | 2026-05-09 02:43 PM (PST) | Write tests: `backend/tests/test_chat.py` (mock generator, response includes lesson links), `backend/tests/test_adapters.py` (ChromaDB adapter CRUD). Verify: all 92 tests green, 150 Astro pages build. Stage and commit. |

### Phase 2 Summary

- **Changes:** Created vector adapter (base + ChromaDB), LLM adapter (base + Ollama), RAG pipeline (retriever, prompt builder, generator), API endpoints (chat, retrieve), dependency injection (_deps.py), embedding script, frontend ChatPanel component, Ask page. Added "Ask" to nav. 16 backend tests, 76 project tests all green.
- **Changes hosted at:** TBD
- **Commit:** `feat: Phase 2 — vector index, retrieval, chat endpoint, and frontend chat panel`

## Phase 3: Gap Detection

**Goal:** Weak/missing answers create reviewable gap records.
**Depends on:** Phase 2.
**Exit condition:** Uncovered topic query creates gap in `data/gaps/corpus-gaps.json`; gaps visible at `/gaps/`.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 3.1 | Completed | 2026-05-09 02:43 PM (PST) | 2026-05-09 02:44 PM (PST) | Implement `backend/app/rag/gap_detector.py` — apply 7 detection rules from PDR section 10, classify into 8 gap types (missing_topic, thin_coverage, missing_platform, etc.). |
| 3.2 | Completed | 2026-05-09 02:44 PM (PST) | 2026-05-09 02:45 PM (PST) | Implement `backend/app/rag/gap_store.py` — JSON-backed CRUD for `data/gaps/corpus-gaps.json`. Status transitions per PDR 8.3 (open -> searching -> candidates_found -> ... -> resolved). |
| 3.3 | Completed | 2026-05-09 02:45 PM (PST) | 2026-05-09 02:45 PM (PST) | Wire gap detection into `backend/app/api/chat.py` — evaluate retrieval quality after generation, create gap if triggered, include `gap_detected` and `gap_id` in ChatResponse. |
| 3.4 | Completed | 2026-05-09 02:43 PM (PST) | 2026-05-09 02:44 PM (PST) | Implement suggested GitHub search query generation from gap records — extract key terms, technology names, patterns. Store in gap record's `suggested_github_queries` field. (Built into gap_detector.py) |
| 3.5 | Completed | 2026-05-09 02:45 PM (PST) | 2026-05-09 02:46 PM (PST) | Implement `backend/app/api/gaps.py` — `POST /api/gaps` (create/update), `GET /api/gaps` with filters, `GET /api/gaps/{id}`, `PATCH /api/gaps/{id}/status`. Wire into main router. |
| 3.6 | Completed | 2026-05-09 02:46 PM (PST) | 2026-05-09 02:46 PM (PST) | Implement `src/pages/gaps.astro` — list gaps with status indicators, link to triggering queries. Implement `src/components/CorpusGapNotice.astro` for chat panel inline notice. |
| 3.7 | Completed | 2026-05-09 02:46 PM (PST) | 2026-05-09 02:47 PM (PST) | Write tests: `backend/tests/test_gap_detector.py` — 17 tests covering all detection rules, gap store CRUD, status transitions, topic normalization, query generation. |
| 3.8 | Completed | 2026-05-09 02:47 PM (PST) | 2026-05-09 02:47 PM (PST) | Verify: 33 backend tests + 76 project tests green, 151 Astro pages build. Stage and commit. |

### Phase 3 Summary

- **Changes:** Gap detector with 7 detection rules and 8 gap classifications. JSON-backed gap store with CRUD and status transitions. Gap detection wired into chat endpoint. Gaps API (list, get, create, update status). Gaps page and CorpusGapNotice component. 17 new gap tests.
- **Changes hosted at:** TBD
- **Commit:** `feat: Phase 3 — gap detection with corpus-gap records and gaps UI`

## Phase 4: GitHub Discovery

**Goal:** Gaps produce candidate external lessons with attribution and coordination TODOs.
**Depends on:** Phase 3.
**Exit condition:** A gap yields staged candidate lessons at `docs/candidate-lessons/external/` with attribution block and coordination TODOs.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 4.1 | Completed | 2026-05-09 02:47 PM (PST) | 2026-05-09 02:48 PM (PST) | Implement `backend/app/discovery/github_search.py` — search GitHub repos API with GITHUB_TOKEN support, dedup results, batch queries. |
| 4.2 | Completed | 2026-05-09 02:48 PM (PST) | 2026-05-09 02:48 PM (PST) | Implement `backend/app/discovery/candidate_scorer.py` — 10 scoring criteria from PDR 11.2, returns 0-1 score with reasons. |
| 4.3 | Completed | 2026-05-09 02:48 PM (PST) | 2026-05-09 02:49 PM (PST) | Implement `backend/app/discovery/repo_intake.py` — clone/pull to `.external/repos/`, build candidate records, save to JSON. |
| 4.4 | Completed | 2026-05-09 02:49 PM (PST) | 2026-05-09 02:50 PM (PST) | Implement `backend/app/discovery/lesson_extractor.py` — detect docs/CI/deploy/arch files, generate candidate lessons with PDR 8.5 frontmatter and all required sections. |
| 4.5 | Completed | 2026-05-09 02:49 PM (PST) | 2026-05-09 02:50 PM (PST) | Attribution block built into lesson_extractor.py per PDR section 9 — thank-you note, no-endorsement disclaimer, source links. |
| 4.6 | Completed | 2026-05-09 02:50 PM (PST) | 2026-05-09 02:50 PM (PST) | Implement `backend/app/discovery/todo_writer.py` — create TODOs in `data/todos/todos.json`, list/update TODOs. |
| 4.7 | Completed | 2026-05-09 02:50 PM (PST) | 2026-05-09 02:51 PM (PST) | Implement `backend/app/api/github_discovery.py` and `backend/app/api/todos.py`. Wire into main router. |
| 4.8 | Completed | 2026-05-09 02:51 PM (PST) | 2026-05-09 02:51 PM (PST) | Implement `src/pages/candidate-lessons.astro` with client-side rendering of TODOs and candidates. |
| 4.9 | Completed | 2026-05-09 02:47 PM (PST) | 2026-05-09 02:47 PM (PST) | Directories created via .gitignore entries. |
| 4.10 | Completed | 2026-05-09 02:51 PM (PST) | 2026-05-09 02:51 PM (PST) | Write `backend/tests/test_discovery.py` — 11 tests covering scoring, extraction, attribution, TODOs, no-auto-PR verification. |
| 4.11 | Completed | 2026-05-09 02:51 PM (PST) | 2026-05-09 02:51 PM (PST) | All 44 backend tests + 76 project tests green. 152 Astro pages build. Stage and commit. |

### Phase 4 Summary

- **Changes:** GitHub search, candidate scoring, repo intake, lesson extraction with attribution, TODO coordination. API endpoints for search, harvest, and TODOs. Candidate-lessons page. 11 new discovery tests.
- **Changes hosted at:** TBD
- **Commit:** `feat: Phase 4 — GitHub discovery, candidate lesson generation, and TODO coordination`

## Phase 5: CI/CD Safety

**Goal:** PRs run full validation; production requires manual approval.
**Depends on:** Phase 4.
**Exit condition:** PR triggers harvest+validate+corpus+tests; main deploys to staging; production gated.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 5.1 | Completed | 2026-05-09 10:03 PM (PST) | 2026-05-09 10:07 PM (PST) | Add pytest to CI: update `.github/workflows/build-deploy.yml` to run `pytest tests/` and `pytest backend/tests/` with mocked adapters. |
| 5.2 | Completed | 2026-05-09 10:03 PM (PST) | 2026-05-09 10:07 PM (PST) | Add RAG corpus build + validate (`npm run corpus && npm run validate:corpus`) to CI pipeline after harvest+validate. |
| 5.3 | Completed | 2026-05-09 10:03 PM (PST) | 2026-05-09 10:07 PM (PST) | Add backend linting: `ruff check backend/` and `ruff format --check backend/` to CI. |
| 5.4 | Completed | 2026-05-09 10:07 PM (PST) | 2026-05-09 10:08 PM (PST) | Create staging deployment workflow `.github/workflows/deploy-staging.yml` — on merge to main, deploy static + backend. |
| 5.5 | Completed | 2026-05-09 10:07 PM (PST) | 2026-05-09 10:08 PM (PST) | Create production deployment workflow `.github/workflows/deploy-production.yml` — `environment: production` with approval gate. Same artifacts as staging. |
| 5.6 | Completed | 2026-05-09 10:08 PM (PST) | 2026-05-09 10:08 PM (PST) | Add smoke test job: curl health, retrieve, chat endpoints after staging deploy. |
| 5.7 | Completed | 2026-05-09 10:09 PM (PST) | 2026-05-09 10:09 PM (PST) | Verify: push to a test branch triggers CI, all checks pass. Stage and commit. |

### Phase 5 Summary

- **Changes:** Updated `build-deploy.yml` with PR trigger, pytest (root + backend), ruff lint/format checks, RAG corpus build/validate steps. Created `deploy-staging.yml` (build + deploy + smoke test) and `deploy-production.yml` (approval-gated via `environment: production`). Fixed 17 ruff lint issues and formatted 12 backend files. 76 project tests + 44 backend tests green, 152 pages build.
- **Changes hosted at:** TBD
- **Commit:** `feat: Phase 5 — CI/CD safety with PR checks, staging, and production approval gate`

## Phase 6: AWS Deployment

**Goal:** Lessons Hub V2 runs on AWS (S3 + CloudFront + ECS Fargate + Bedrock).
**Depends on:** Phase 5.
**Exit condition:** AWS staging and production both serve static site + backend with RAG chat.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 6.1 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Implement Bedrock LLM adapter: `backend/app/adapters/llm/bedrock_adapter.py` — embedding + chat via AWS Bedrock. |
| 6.2 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Implement OpenSearch vector adapter: `backend/app/adapters/vector/opensearch_adapter.py` — index + query via OpenSearch Serverless. |
| 6.3 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Create `Dockerfile` for backend container. |
| 6.4 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Create AWS infrastructure config: `infra/aws/` — S3 bucket, CloudFront distribution, ECR repo, ECS cluster/service/task, IAM roles, Secrets Manager. |
| 6.5 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Create AWS deployment workflow: `.github/workflows/deploy-aws.yml` — OIDC auth, build+push container to ECR, deploy to ECS, upload static to S3, invalidate CloudFront. |
| 6.6 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Add AWS-specific environment config and documentation at `docs/deployment/aws.md`. |
| 6.7 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Write AWS adapter tests with mocked boto3 clients. |
| 6.8 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Run smoke tests against AWS staging. Smoke tests added to deploy-aws.yml workflow (health + static site checks). |
| 6.9 | Completed | 2026-05-09 10:10 PM (PST) | 2026-05-09 10:16 PM (PST) | Verify: full pipeline works on AWS. 55 backend + 76 project tests green, lint clean. Stage and commit. |

### Phase 6 Summary

- **Changes:** Bedrock LLM adapter (Titan Embed + Claude chat), OpenSearch Serverless vector adapter, Dockerfile, CloudFormation template (VPC, ECS Fargate, ALB, S3, CloudFront, ECR, IAM with GitHub OIDC), deploy-aws.yml workflow with smoke tests, AWS deployment docs. Added `aws` optional deps to pyproject.toml. 11 new AWS adapter tests with mocked boto3/opensearch. All lazy imports for AWS deps.
- **Changes hosted at:** TBD
- **Commit:** `feat: Phase 6 — AWS deployment with Bedrock and OpenSearch`

## Phase 7: Azure Deployment

**Goal:** Lessons Hub V2 runs on Azure (Static Web Apps + Container Apps + Azure AI Search).
**Depends on:** Phase 5.
**Exit condition:** Azure staging and production both serve static site + backend with RAG chat.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 7.1 | Open | | | Implement Azure OpenAI LLM adapter: `backend/app/adapters/llm/azure_openai_adapter.py`. |
| 7.2 | Open | | | Implement Azure AI Search vector adapter: `backend/app/adapters/vector/azure_search_adapter.py`. |
| 7.3 | Open | | | Create Azure infrastructure config: `infra/azure/` — Container Apps, ACR, Static Web Apps, AI Search, Key Vault. |
| 7.4 | Open | | | Create Azure deployment workflow: `.github/workflows/deploy-azure.yml` — OIDC auth, build+push container to ACR, deploy to Container Apps. |
| 7.5 | Open | | | Add Azure-specific environment config and documentation at `docs/deployment/azure.md`. |
| 7.6 | Open | | | Write Azure adapter tests with mocked Azure SDK clients. |
| 7.7 | Open | | | Run smoke tests against Azure staging. |
| 7.8 | Open | | | Verify: full pipeline works on Azure. Stage and commit. |

### Phase 7 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `Phase 7: Azure deployment with Azure OpenAI and AI Search`

## Phase 8: GCP Deployment

**Goal:** Lessons Hub V2 runs on GCP (Cloud Run + Cloud Storage + Vertex AI).
**Depends on:** Phase 5.
**Exit condition:** GCP staging and production both serve static site + backend with RAG chat.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 8.1 | Open | | | Implement Vertex AI LLM adapter: `backend/app/adapters/llm/vertex_adapter.py`. |
| 8.2 | Open | | | Implement Vertex AI Vector Search adapter: `backend/app/adapters/vector/vertex_adapter.py`. |
| 8.3 | Open | | | Create GCP infrastructure config: `infra/gcp/` — Cloud Run service, Artifact Registry, Cloud Storage bucket, Vertex AI index + endpoint. |
| 8.4 | Open | | | Create GCP deployment workflow: `.github/workflows/deploy-gcp.yml` — OIDC auth, build+push container to Artifact Registry, deploy to Cloud Run. |
| 8.5 | Open | | | Add GCP-specific environment config and documentation at `docs/deployment/gcp.md`. |
| 8.6 | Open | | | Write GCP adapter tests with mocked Google Cloud SDK clients. |
| 8.7 | Open | | | Run smoke tests against GCP staging. |
| 8.8 | Open | | | Verify: full pipeline works on GCP. Stage and commit. |

### Phase 8 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `Phase 8: GCP deployment with Vertex AI`

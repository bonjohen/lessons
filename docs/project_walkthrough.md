# Lessons Hub — Project Walkthrough

Lessons Hub is a full-stack system that collects engineering lessons from multiple GitHub repositories and consolidates them into a single searchable, browsable, AI-queryable library. It combines a static site (Astro + Pagefind) with a RAG-powered chatbot backend (FastAPI + pluggable LLM/vector adapters) and includes corpus gap detection, GitHub project discovery, and multi-cloud deployment infrastructure.

This document walks through the entire system end-to-end: how data flows from source repositories to a deployed site, how the RAG backend answers questions, and how gaps in knowledge trigger automated discovery of new sources.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Repository Layout](#2-repository-layout)
3. [The Source Repository Contract](#3-the-source-repository-contract)
4. [The Repo Registry](#4-the-repo-registry)
5. [The Harvest Pipeline](#5-the-harvest-pipeline)
6. [Validation](#6-validation)
7. [The RAG Corpus](#7-the-rag-corpus)
8. [The Astro Static Site](#8-the-astro-static-site)
9. [Search (Pagefind)](#9-search-pagefind)
10. [The FastAPI Backend](#10-the-fastapi-backend)
11. [The Adapter Pattern](#11-the-adapter-pattern)
12. [Gap Detection](#12-gap-detection)
13. [GitHub Discovery](#13-github-discovery)
14. [Deployment](#14-deployment)
15. [CI/CD](#15-cicd)
16. [Testing](#16-testing)
17. [Configuration Reference](#17-configuration-reference)
18. [Getting Started](#18-getting-started)

---

## 1. High-Level Architecture

The system has two halves that can run independently:

**Static site (V1 core):** A build-time pipeline clones source repos, extracts lesson markdown, normalizes metadata, generates JSON, builds an Astro static site, and indexes it with Pagefind. Deployed to GitHub Pages. Works with zero backend dependencies.

**RAG backend (V2):** A FastAPI service that chunks the lesson corpus, embeds it into a vector store, and answers natural-language questions with grounded citations. When the corpus can't answer a question well, the gap detector logs the gap. Gaps can trigger GitHub discovery to find new source repositories.

```
Source Repos (GitHub)
        │
        ▼
   data/repos.yml ──► harvest_lessons.py ──► clone + parse + normalize
        │                                            │
        │                                            ▼
        │                              src/content/generated/lessons.json
        │                              src/content/generated/repos.json
        │                              src/content/generated/tags.json
        │                              public/exports/lessons-pack.json
        │                                            │
        │                        ┌───────────────────┤
        │                        ▼                   ▼
        │               build_rag_corpus.py     Astro build
        │                        │                   │
        │                        ▼                   ▼
        │               data/rag-chunks.json    dist/ (static HTML)
        │                        │                   │
        │                        ▼                   ▼
        │               embed_rag_corpus.py     Pagefind index
        │                        │                   │
        │                        ▼                   ▼
        │               ChromaDB / cloud        GitHub Pages
        │               vector store
        │                        │
        │                        ▼
        │               FastAPI Backend
        │               ├── /api/chat        (RAG Q&A)
        │               ├── /api/retrieve    (raw chunk search)
        │               ├── /api/gaps        (gap records)
        │               └── /api/discovery   (GitHub search)
        │                        │
        │                        ▼
        │               Gap Detector ──► GitHub Discovery ──► New source repos
        │                                                         │
        └─────────────────────────────────────────────────────────┘
                              (cycle: new repos feed back into harvest)
```

---

## 2. Repository Layout

```
lessons/
├── data/
│   ├── repos.yml                  # Source repo registry (the single config file)
│   ├── platform-keywords.json     # Keywords for gap type classification
│   ├── rag-chunks.json            # Generated: chunked lessons for RAG
│   ├── rag-manifest.json          # Generated: corpus metadata
│   ├── embed-hashes.json          # Generated: incremental embedding tracking
│   ├── chromadb/                  # Generated: local vector store
│   └── gaps/                      # Generated: corpus gap records (JSON)
│
├── scripts/
│   ├── harvest_lessons.py         # Clone repos, parse lessons, generate JSON
│   ├── validate_lessons.py        # Validate generated lesson data
│   ├── build_rag_corpus.py        # Chunk lessons by heading for RAG
│   ├── validate_rag_corpus.py     # Validate RAG corpus integrity
│   ├── embed_rag_corpus.py        # Embed chunks into vector store
│   └── lesson_core.py             # Shared harvesting utilities
│
├── backend/
│   ├── Dockerfile                 # Multi-profile container build
│   ├── pyproject.toml             # Python package with optional dependency groups
│   └── app/
│       ├── main.py                # FastAPI app, middleware, router registration
│       ├── api/
│       │   ├── health.py          # GET /health
│       │   ├── chat.py            # POST /api/chat
│       │   ├── retrieve.py        # POST /api/retrieve
│       │   ├── gaps.py            # CRUD for corpus gap records
│       │   ├── todos.py           # Coordination TODO records
│       │   └── github_discovery.py # POST /api/discovery/search
│       ├── rag/
│       │   ├── retriever.py       # Embed query → vector search → top-k chunks
│       │   ├── generator.py       # Build prompt → LLM chat → extract citations
│       │   ├── gap_detector.py    # 7-rule gap detection engine
│       │   ├── gap_store.py       # JSON-file gap persistence
│       │   ├── prompt_builder.py  # System/user prompt construction
│       │   └── cache.py           # TTL cache for retrieval/generation
│       ├── adapters/
│       │   ├── llm/
│       │   │   ├── base.py              # Abstract LLMAdapter (embed + chat)
│       │   │   ├── ollama_adapter.py     # Local: Ollama
│       │   │   ├── openai_adapter.py     # OpenAI API
│       │   │   ├── bedrock_adapter.py    # AWS Bedrock
│       │   │   ├── azure_openai_adapter.py  # Azure OpenAI
│       │   │   └── vertex_adapter.py     # GCP Vertex AI
│       │   └── vector/
│       │       ├── base.py               # Abstract VectorAdapter
│       │       ├── chromadb_adapter.py    # Local: ChromaDB
│       │       ├── opensearch_adapter.py  # AWS OpenSearch
│       │       ├── azure_search_adapter.py # Azure AI Search
│       │       └── vertex_adapter.py     # GCP Vertex AI Vector Search
│       ├── discovery/
│       │   ├── github_search.py    # GitHub API search client
│       │   ├── candidate_scorer.py # Score/rank discovered repos
│       │   ├── repo_intake.py      # Clone candidates locally
│       │   ├── lesson_extractor.py # Extract lessons from candidates
│       │   └── todo_writer.py      # Create coordination TODOs
│       ├── models/
│       │   └── schemas.py          # Pydantic v2 models for all API types
│       ├── metrics.py              # Prometheus metrics (optional)
│       └── logging_config.py       # Structured logging setup
│
├── src/
│   ├── pages/
│   │   ├── index.astro             # Home page
│   │   ├── ask.astro               # Chat interface ("Ask the Lessons")
│   │   ├── gaps.astro              # Corpus gap browser
│   │   ├── candidate-lessons.astro # Discovered candidate lessons
│   │   ├── lessons/
│   │   │   ├── index.astro         # All lessons listing
│   │   │   └── [id].astro          # Individual lesson page
│   │   ├── repos/
│   │   │   ├── index.astro         # All repos listing
│   │   │   └── [repo].astro        # Lessons filtered by repo
│   │   ├── tags/[tag].astro        # Lessons filtered by tag
│   │   ├── phases/[phase].astro    # Lessons filtered by phase
│   │   └── types/[type].astro      # Lessons filtered by type
│   ├── layouts/                    # Astro layout templates
│   ├── components/                 # Reusable Astro/TS components
│   └── content/generated/          # Generated JSON (not committed)
│
├── public/exports/                 # AI-readable export packs (generated)
├── .github/workflows/              # 8 CI/CD workflows
├── docs/                           # Design docs, PDRs, plans
├── tests/                          # Python tests for harvest/validation
└── tmp/                            # Temporary clone directory
```

---

## 3. The Source Repository Contract

Any GitHub repository can feed lessons into the hub. The contract is simple:

1. Store lesson files at a configurable path (default: `docs/lessons/*.md`).
2. Each lesson is a standalone markdown file.
3. Files may include YAML frontmatter. Missing frontmatter is fine — the harvester normalizes everything.

**Recommended frontmatter fields:**

| Field | Required | Notes |
|---|---|---|
| `title` | Required (after normalization) | Falls back to first H1 or filename |
| `summary` | Recommended | One-line description |
| `date` | Recommended | ISO date |
| `phase` | Recommended | Project phase (e.g., "design", "implementation") |
| `lesson_type` | Recommended | One of: architecture, implementation, testing, deployment, debugging, data-design, ai-assisted-development, documentation, maintenance, process, other |
| `tags` | Recommended | List of topic tags |
| `status` | Optional | active (default), superseded, draft, deprecated |

**Minimal valid lesson:** a file with either a `title` in frontmatter, a first-line `# Heading`, or a filename that can be slugified into a title. The body must not be empty.

---

## 4. The Repo Registry

The entire system is driven by one configuration file: `data/repos.yml`.

```yaml
repos:
  - id: certification          # Stable kebab-case identifier
    name: Certification        # Display name
    owner: bonjohen            # GitHub owner
    repo: certification        # GitHub repo name
    branch: main               # Branch to harvest
    lessons_path: docs/lessons # Path to lesson files in the repo
    project_url: https://github.com/bonjohen/certification
    enabled: true              # Optional, defaults to true

  - id: artemis
    name: Artemis
    owner: bonjohen
    repo: Artemis
    branch: main
    lessons_path: docs/lessons
    project_url: https://github.com/bonjohen/Artemis
    enabled: true
```

**Adding a new source repo is a one-line edit.** Add an entry to `repos.yml` and the next harvest picks it up. No code changes needed. All repos — whether you own them or not — go through the same pipeline.

---

## 5. The Harvest Pipeline

The harvest is the core data pipeline. It runs via `npm run harvest` (which calls `python scripts/harvest_lessons.py`).

### What it does

1. **Reads** `data/repos.yml` to get the list of source repos.
2. **Clones** each enabled repo into `tmp/repos/` using `git clone --depth 1`. If a `LESSONS_REPO_TOKEN` environment variable is set, it authenticates the clone for private repos.
3. **Scans** each repo's `lessons_path` for `*.md` files.
4. **Parses** each file with `python-frontmatter` to extract YAML frontmatter and markdown body.
5. **Normalizes** metadata:
   - Title: from frontmatter, first H1, or filename.
   - ID: `{repo_id}-{slugified-title}`.
   - Tags: coerced to a list of lowercase strings (handles YAML quirks where scalars appear as lists).
   - Date: parsed and ISO-formatted.
   - Reading time: estimated from word count.
   - Source URL: constructed from GitHub owner/repo/branch/path.
6. **Generates** output files:
   - `src/content/generated/lessons.json` — all lesson records.
   - `src/content/generated/repos.json` — repo metadata.
   - `src/content/generated/tags.json` — tag index.
   - `src/content/generated/phases.json` — phase index.
   - `src/content/generated/lesson_types.json` — type index.
   - `public/exports/lessons-pack.json` — full lesson data for AI consumption.
   - `public/exports/lessons-index.json` — lightweight index.
   - `public/exports/lessons-pack.md` — all lessons in a single markdown file.

### Shared utilities (`scripts/lesson_core.py`)

The harvester and validator share a core library with functions for slug generation, tag normalization, date coercion, title extraction, and validation constants (required fields, ID patterns, controlled vocabularies).

---

## 6. Validation

Validation runs via `npm run validate:lessons` (calls `python scripts/validate_lessons.py`).

It reads the generated `lessons.json` and checks every lesson record against the schema. Issues are classified by severity:

**ERROR (build fails):**
- Missing or malformed `repos.yml`.
- Duplicate lesson IDs.
- Empty lesson content.
- Unreadable files.
- Invalid generated JSON.

**WARNING (build continues):**
- Missing `summary`, `date`, `tags`, `phase`, or `lesson_type`.
- Unknown values in controlled vocabularies (e.g., an unrecognized `lesson_type`).
- Very short content.

A separate validator exists for the RAG corpus (`npm run validate:corpus`) that checks `data/rag-chunks.json` for structural integrity — valid chunk IDs, non-empty text, correct lesson references, and consistent metadata.

---

## 7. The RAG Corpus

The RAG corpus is built from the harvested lessons via `npm run corpus` (calls `python scripts/build_rag_corpus.py`).

### Chunking strategy

Lessons are split by **H2 headings**. Each heading boundary becomes a chunk. Content before the first H2 becomes the "Introduction" chunk (index 0). This preserves semantic structure — each chunk is a coherent section of a lesson.

Each chunk record contains:

```json
{
  "chunk_id": "certification-schema-drift-0",
  "lesson_id": "certification-schema-drift",
  "repo_id": "certification",
  "title": "Schema Drift Validation",
  "summary": "How we caught schema drift in production",
  "lesson_url": "/lessons/certification-schema-drift",
  "chunk_index": 0,
  "heading_path": "Schema Drift Validation > Introduction",
  "chunk_text": "...",
  "token_count": 142,
  "tags": ["validation", "schema"],
  "content_hash": "a1b2c3d4e5f6g7h8"
}
```

The `content_hash` enables incremental embedding — only chunks whose content has changed since the last run need re-embedding.

### Embedding

`npm run embed` (calls `python scripts/embed_rag_corpus.py`) reads `rag-chunks.json`, embeds each chunk via the configured LLM adapter, and indexes the embeddings into the vector store. Change detection uses `data/embed-hashes.json` to skip unchanged chunks.

---

## 8. The Astro Static Site

The frontend is an Astro static site configured for pure static output (`output: 'static'` in `astro.config.mjs`). It generates HTML at build time from the JSON produced by the harvest pipeline.

### Pages

| Route | Source | Description |
|---|---|---|
| `/` | `src/pages/index.astro` | Home page with lesson count, repo list, recent lessons |
| `/lessons/` | `src/pages/lessons/index.astro` | All lessons, sortable and filterable |
| `/lessons/[id]` | `src/pages/lessons/[id].astro` | Individual lesson with rendered markdown |
| `/repos/` | `src/pages/repos/index.astro` | All source repositories |
| `/repos/[repo]` | `src/pages/repos/[repo].astro` | Lessons from a single repo |
| `/tags/[tag]` | `src/pages/tags/[tag].astro` | Lessons with a specific tag |
| `/phases/[phase]` | `src/pages/phases/[phase].astro` | Lessons from a project phase |
| `/types/[type]` | `src/pages/types/[type].astro` | Lessons of a specific type |
| `/ask` | `src/pages/ask.astro` | RAG chat interface ("Ask the Lessons") |
| `/gaps` | `src/pages/gaps.astro` | Corpus gap browser |
| `/candidate-lessons` | `src/pages/candidate-lessons.astro` | Discovered candidate lessons |

### Build

`npm run build` runs the Astro build. It reads JSON from `src/content/generated/` and produces static HTML in `dist/`. The site uses `marked` for markdown rendering and `sanitize-html` for XSS protection.

---

## 9. Search (Pagefind)

After the Astro build, `npm run index` runs Pagefind against the `dist/` directory. Pagefind generates a client-side search index that works entirely in the browser with no backend. Users can search by keyword across all lesson content, titles, tags, and metadata.

Pagefind was chosen because it works with any static host (no server-side search infrastructure) and scales well for documentation-sized corpora.

---

## 10. The FastAPI Backend

The backend is a Python FastAPI application at `backend/app/main.py`. It runs independently of the static site — if the backend is down, the static site still works (the chat panel shows a fallback message).

### API Endpoints

All API routes are mounted at both `/api/` and `/api/v1/` for forward-compatible versioning.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check with component status |
| `POST` | `/api/chat` | Ask a question, get a grounded answer with citations |
| `POST` | `/api/retrieve` | Raw chunk retrieval without answer generation |
| `GET/POST` | `/api/gaps` | List, create, update corpus gap records |
| `POST` | `/api/discovery/search` | Search GitHub for repos relevant to a gap |
| `GET/POST` | `/api/todos` | Coordination TODOs for external lesson handling |
| `GET` | `/metrics` | Prometheus metrics (if `prometheus_client` is installed) |

### Chat flow

When a user sends a message to `/api/chat`:

1. **Retriever** embeds the query using the LLM adapter, queries the vector store for the top-k most similar chunks, and returns ranked results. Results are cached with a TTL.
2. **Generator** takes the retrieved chunks, builds a grounded prompt (system message with instructions + user question + context chunks), sends it to the LLM, and extracts the answer with lesson citations.
3. **Gap Detector** evaluates whether the answer is well-supported by the corpus. If not, it creates or updates a gap record.

The response includes the answer text, a list of relevant lessons with similarity scores and links, and a flag indicating whether a corpus gap was detected.

### Request/Response Models

All API types are defined as Pydantic v2 models in `backend/app/models/schemas.py`:

- `ChatRequest` / `ChatResponse` — message, optional filters (repo, tags, lesson_type), answer, relevant lessons, gap info.
- `RetrieveRequest` / `RetrieveResponse` — query, ranked chunk results.
- `GapRecord` — gap ID, trigger query, normalized topic, gap type, status, suggested GitHub queries.
- `CandidateRepo` — discovered repo with score, harvest status, candidate lesson paths.
- `TodoRecord` — coordination TODO with priority, severity, linked gap/project.

### Middleware

- **CORS:** Configurable via `CORS_ORIGINS` environment variable. Defaults to localhost ports 4321 and 3000.
- **Metrics:** Request duration and count tracked per path/method/status when `prometheus_client` is installed.

---

## 11. The Adapter Pattern

All LLM and vector store operations go through abstract base classes. This is how the system supports local development, multiple cloud providers, and testing with the same application code.

### LLM Adapters

The `LLMAdapter` abstract class defines two methods:

```python
class LLMAdapter(ABC):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def chat(self, messages: list[dict]) -> str: ...
```

Implementations:

| Adapter | Provider | Use Case |
|---|---|---|
| `ollama_adapter.py` | Ollama (local) | Local development, no cloud dependencies |
| `openai_adapter.py` | OpenAI API | OpenAI models |
| `bedrock_adapter.py` | AWS Bedrock | AWS deployment |
| `azure_openai_adapter.py` | Azure OpenAI | Azure deployment |
| `vertex_adapter.py` | GCP Vertex AI | GCP deployment |

### Vector Adapters

The `VectorAdapter` abstract class defines:

```python
class VectorAdapter(ABC):
    def index_chunks(self, chunks, embeddings) -> int: ...
    def query(self, embedding, top_k, filters) -> list[dict]: ...
    def delete_collection(self) -> None: ...
    def count(self) -> int: ...
```

Implementations:

| Adapter | Provider | Use Case |
|---|---|---|
| `chromadb_adapter.py` | ChromaDB (local) | Local development |
| `opensearch_adapter.py` | AWS OpenSearch | AWS deployment |
| `azure_search_adapter.py` | Azure AI Search | Azure deployment |
| `vertex_adapter.py` | GCP Vertex AI Vector Search | GCP deployment |

### Lazy imports

Cloud adapters import their SDKs (`boto3`, `azure-*`, `google-cloud-*`) inside `__init__`, not at module level. This means the application starts without requiring any cloud SDK installed — only the adapter you actually use needs its SDK present.

### Testing cloud adapters

Tests use `sys.modules.setdefault()` to inject mock modules before the adapter's `__init__` runs. This avoids needing real cloud SDKs installed in the test environment while still testing the adapter logic.

---

## 12. Gap Detection

The gap detector (`backend/app/rag/gap_detector.py`) runs after every chat response and evaluates whether the corpus adequately answered the question. It uses 7 rules:

1. **No results:** Zero chunks retrieved.
2. **Low relevance:** All chunk similarity scores below the threshold (default 0.3).
3. **Related but unanswered:** Chunks are somewhat related but not directly answering the question.
4. **Thin coverage:** Fewer than the minimum distinct lessons (default 2) match.
5. **Missing platform:** Query mentions a specific platform/technology not represented in results.
6. **Weak-answer signals:** The LLM response contains phrases like "does not appear to contain," "no relevant lessons," etc.
7. **General-knowledge answer:** The LLM gave a long answer but with weak evidence from the corpus (it's generating from training data, not from lessons).

Each detected gap is classified into a type:

- `missing_topic` — the corpus has no coverage of this area.
- `thin_coverage` — some related lessons exist but not enough depth.
- `missing_platform` — platform-specific gap (e.g., "Azure Container Apps").
- `missing_example`, `missing_deployment_pattern`, `missing_failure_case`, `missing_comparison`, `missing_reference_implementation` — specific knowledge types.

Gap records are stored as JSON files in `data/gaps/` and exposed via the `/api/gaps` endpoint.

---

## 13. GitHub Discovery

When a corpus gap is identified, the discovery system can search GitHub for repositories that might fill it.

### Flow

1. **Search** (`discovery/github_search.py`): Takes queries derived from the gap record. Searches the GitHub API for repositories, filters by language and star count, respects rate limits.
2. **Score** (`discovery/candidate_scorer.py`): Ranks discovered repos by relevance — does the repo's description, topics, and README match the gap? Does it have lessons-like documentation?
3. **Intake** (`discovery/repo_intake.py`): Clones high-scoring candidates locally.
4. **Extract** (`discovery/lesson_extractor.py`): Applies the lesson extraction workflow to the cloned repo — looks for documentation that could be converted to lessons.
5. **TODO** (`discovery/todo_writer.py`): Creates a coordination TODO so the maintainer can review the candidate lessons and, if appropriate, contact the repo owner before proposing contributions.

Generated candidate lessons always include clear attribution (source project, URL, harvest date, review status). Nothing is treated as authoritative until a human reviews it.

---

## 14. Deployment

The project supports multiple deployment targets. The static site and backend can be deployed independently.

### Static Site — GitHub Pages

The primary deployment. The `build-deploy.yml` workflow builds the site and deploys to GitHub Pages on every push to `main`. The site is available at `https://bonjohen.github.io/lessons/`.

### Backend — Docker

The backend `Dockerfile` uses a build argument for deployment profile:

```dockerfile
FROM python:3.11-slim
ARG PROFILE=local
RUN pip install --no-cache-dir -e ".[${PROFILE}]"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build with a specific profile to pull in the right cloud SDK dependencies:

```bash
docker build --build-arg PROFILE=aws -t lessons-backend .    # AWS
docker build --build-arg PROFILE=azure -t lessons-backend .  # Azure
docker build --build-arg PROFILE=gcp -t lessons-backend .    # GCP
docker build --build-arg PROFILE=local -t lessons-backend .  # Local (default)
```

### Platform-Specific Deployments

| Platform | Workflow | Config |
|---|---|---|
| GitHub Pages | `.github/workflows/build-deploy.yml` | `astro.config.mjs` |
| AWS | `.github/workflows/deploy-aws.yml` | Bedrock + OpenSearch adapters |
| Azure | `.github/workflows/deploy-azure.yml` | Azure OpenAI + AI Search adapters |
| GCP | `.github/workflows/deploy-gcp.yml` | Vertex AI + Vector Search adapters |
| Fly.io | `.github/workflows/deploy-flyio.yml` | `fly.toml` |
| Railway | `.github/workflows/deploy-railway.yml` | `railway.toml` |
| Staging | `.github/workflows/deploy-staging.yml` | Pre-production validation |
| Production | `.github/workflows/deploy-production.yml` | Production promotion |

Cloud deployments use **OIDC / Workload Identity Federation** — no long-lived credentials stored in GitHub secrets.

---

## 15. CI/CD

The main workflow (`.github/workflows/build-deploy.yml`) runs on every push, PR, and daily at 06:00 UTC (to pick up new lessons from source repos).

### Pipeline stages

1. **Checkout** the repo.
2. **Setup** Python 3.11 and Node 22.
3. **Install** Python and Node dependencies.
4. **Lint** the backend with `ruff check` and `ruff format --check`.
5. **Test** project tests (`pytest tests/` — 76 tests covering harvesting, validation, slugs, corpus).
6. **Test** backend tests (`pytest backend/tests/` — 102 tests covering health, chat, adapters, gaps, discovery, cloud).
7. **Harvest** lessons from all source repos.
8. **Validate** the harvested lesson data.
9. **Build** the RAG corpus.
10. **Validate** the RAG corpus.
11. **Build** the Astro static site.
12. **Index** with Pagefind.
13. **Deploy** to GitHub Pages (skipped on PRs).

The daily schedule means the site automatically picks up new lessons added to source repos without manual intervention.

---

## 16. Testing

### Project tests (`tests/`)

76 tests covering the harvest and validation pipeline:

- Repo registry loading and validation.
- Frontmatter parsing and normalization.
- Slug generation edge cases.
- Tag coercion (YAML list-valued scalars to strings).
- Date parsing across formats.
- Export file generation.
- RAG corpus chunking.
- Validation rule coverage.

### Backend tests (`backend/tests/`)

102 tests covering the FastAPI backend:

- Health endpoint responses.
- Chat request/response serialization.
- Retriever and generator logic.
- Gap detection rules (all 7).
- Gap store persistence.
- GitHub discovery search, scoring, intake, extraction.
- TODO creation.
- Cloud adapter initialization and method calls (mocked via `sys.modules.setdefault()`).
- Prompt builder output.
- Cache TTL behavior.
- Metrics middleware.

### Running tests

```bash
# Project tests
python -m pytest tests/

# Backend tests
python -m pytest backend/tests/

# Lint
ruff check backend/
ruff format --check backend/
```

---

## 17. Configuration Reference

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `LESSONS_REPO_TOKEN` | GitHub token for cloning private repos | None (public repos only) |
| `GITHUB_TOKEN` | GitHub API token for discovery searches | None (anonymous, lower rate limits) |
| `CORS_ORIGINS` | Comma-separated allowed origins for backend | `http://localhost:4321,http://localhost:3000` |
| `GAP_MIN_RELEVANCE_THRESHOLD` | Minimum chunk relevance to avoid gap detection | `0.3` |
| `GAP_MIN_DISTINCT_LESSONS` | Minimum distinct lessons for adequate coverage | `2` |
| `GAP_RELATED_BUT_UNANSWERED_THRESHOLD` | Threshold for rule 3 | `0.5` |
| `GAP_MIN_CHUNKS_FOR_RELATED` | Minimum chunks for related-but-unanswered | `3` |
| `GAP_MIN_ANSWER_LENGTH_FOR_WEAK_EVIDENCE` | Length threshold for general-knowledge detection | `200` |

### npm Scripts

| Script | What it does |
|---|---|
| `npm run dev` | Start Astro dev server with hot reload |
| `npm run build` | Build static site to `dist/` |
| `npm run harvest` | Clone source repos and generate JSON |
| `npm run validate:lessons` | Validate generated lesson data |
| `npm run corpus` | Build RAG corpus from lessons.json |
| `npm run validate:corpus` | Validate RAG corpus integrity |
| `npm run embed` | Embed chunks into vector store |
| `npm run index` | Run Pagefind indexing on `dist/` |
| `npm run build:full` | Full pipeline: harvest → validate → corpus → validate → build → index |
| `npm run backend` | Start FastAPI backend with hot reload |

---

## 18. Getting Started

### Prerequisites

- Node.js 22+
- Python 3.11+
- Git

### Quick start (static site only)

```bash
git clone https://github.com/bonjohen/lessons.git
cd lessons
npm install
pip install -r requirements.txt
npm run build:full
npm run dev                # Open http://localhost:4321/lessons/
```

### Full stack (with RAG backend)

```bash
# Install backend with local development dependencies
pip install -e "backend[dev]"

# Build the corpus and embed it
npm run harvest
npm run corpus
npm run embed

# Start the backend (in one terminal)
npm run backend            # Runs on http://localhost:8000

# Start the frontend (in another terminal)
npm run dev                # Open http://localhost:4321/lessons/ask
```

### Adding a new source repository

1. Edit `data/repos.yml` — add an entry with `id`, `name`, `owner`, `repo`, `branch`, and `lessons_path`.
2. Run `npm run build:full`.
3. The new repo's lessons appear on the site.

### Writing a lesson

Create a markdown file in your source repo's `docs/lessons/` directory:

```markdown
---
title: What We Learned About Schema Drift
summary: Schema drift caught in production after mock tests passed
date: 2026-01-15
lesson_type: debugging
tags: [validation, schema, production]
phase: implementation
---

## Context

We deployed a database migration that changed column types...

## What Went Wrong

Our mocked tests didn't exercise the actual database...

## What We Changed

We switched to integration tests against a real database...
```

The next harvest will pick it up automatically.

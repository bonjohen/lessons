# Architecture

## Repo Treatment

All source repos are treated identically regardless of ownership. Whether the repo belongs to the project maintainer or an external contributor, it goes through the same pipeline: register in `data/repos.yml`, harvest, validate, render. There is no separate workflow for "external" or "candidate" repos.

Each source repo gets an `index.md` checked into the lessons project that documents:
- The source repository URL and owner
- A brief description of the project
- An overview of the harvested lesson files

## Data Flow

### V1 Pipeline (Static Site)

```
data/repos.yml
    │
    ▼
harvest_lessons.py
    │
    ├─ git clone --depth 1 → tmp/repos/{repo_id}/
    │
    ├─ scan docs/lessons/**/*.md
    │
    ├─ parse YAML frontmatter + markdown body
    │
    ├─ normalize (IDs, slugs, tags, defaults)
    │
    ├─ check in harvested lessons + index.md per repo
    │
    ├─ generate → src/content/generated/
    │   ├─ lessons.json
    │   ├─ repos.json
    │   ├─ tags.json
    │   ├─ phases.json
    │   └─ lesson_types.json
    │
    └─ generate → public/exports/
        ├─ lessons-pack.json
        ├─ lessons-index.json
        └─ lessons-pack.md

validate_lessons.py
    │
    ├─ validate repos.yml structure
    ├─ validate generated JSON
    ├─ check lesson records (errors + warnings)
    └─ exit non-zero on errors

Astro build
    │
    ├─ import generated JSON via src/lib/data.ts
    ├─ render static pages (100+ pages)
    └─ output → dist/

Pagefind index
    │
    ├─ index lesson detail pages (data-pagefind-body)
    └─ output → dist/pagefind/

GitHub Pages deploy
    └─ upload dist/ as Pages artifact
```

### V2 Pipeline (RAG Backend)

```
lessons.json
    │
    ▼
build_rag_corpus.py
    │
    ├─ chunk by H2 headings → data/rag-chunks.json (793 chunks)
    └─ manifest → data/rag-manifest.json
    │
    ▼
embed_rag_corpus.py
    │
    ├─ embed chunks via LLMAdapter.embed()
    └─ index into VectorAdapter (ChromaDB locally)

User query → ChatPanel.astro → POST /api/chat
    │
    ▼
FastAPI Backend
    │
    ├─ Retriever: embed query → vector search → top-k chunks
    ├─ Generator: build grounded prompt → LLM chat → extract citations
    ├─ GapDetector: 7 rules → gap record if corpus can't answer
    └─ Discovery: GitHub search → score repos → extract candidate lessons
```

## Component Map

### Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `harvest_lessons.py` | Clone repos, parse lessons, generate JSON + exports |
| `validate_lessons.py` | Validate repos.yml and generated data |
| `build_rag_corpus.py` | Chunk lessons.json into RAG corpus by H2 headings |
| `validate_rag_corpus.py` | Validate RAG corpus schema, IDs, token counts |
| `embed_rag_corpus.py` | Embed corpus chunks and index into vector store |

### Backend (`backend/app/`)

| Module | Purpose |
|--------|---------|
| `api/health.py` | Health check with version and corpus status |
| `api/chat.py` | Chat endpoint with automatic gap detection |
| `api/retrieve.py` | Raw chunk retrieval without generation |
| `api/gaps.py` | Gap CRUD and status transitions |
| `api/github_discovery.py` | GitHub search and candidate harvesting |
| `api/todos.py` | Coordination TODO management |
| `api/_deps.py` | Lazy-loaded singleton dependency injection |
| `rag/retriever.py` | Query embedding + vector search |
| `rag/generator.py` | Grounded prompt building + LLM chat |
| `rag/prompt_builder.py` | System prompt construction |
| `rag/gap_detector.py` | 7-rule gap detection |
| `rag/gap_store.py` | JSON-backed gap CRUD |
| `discovery/github_search.py` | GitHub Repos API search |
| `discovery/candidate_scorer.py` | 10-criteria repo scoring |
| `discovery/lesson_extractor.py` | Candidate lesson extraction with attribution |
| `adapters/llm/base.py` | Abstract LLM adapter (embed + chat) |
| `adapters/llm/ollama_adapter.py` | Local: nomic-embed-text + llama3.1:8b |
| `adapters/llm/bedrock_adapter.py` | AWS: Titan Embed v2 + Claude 3 Haiku |
| `adapters/llm/azure_openai_adapter.py` | Azure: text-embedding-3-small + gpt-4o-mini |
| `adapters/llm/vertex_adapter.py` | GCP: text-embedding-004 + Gemini 1.5 Flash |
| `adapters/vector/base.py` | Abstract vector adapter (index, query, delete, count) |
| `adapters/vector/chromadb_adapter.py` | Local: ChromaDB with cosine HNSW |
| `adapters/vector/opensearch_adapter.py` | AWS: OpenSearch Serverless |
| `adapters/vector/azure_search_adapter.py` | Azure: AI Search |
| `adapters/vector/vertex_adapter.py` | GCP: Vertex AI Vector Search |

### Data Layer (`src/lib/`)

| Module | Purpose |
|--------|---------|
| `data.ts` | Typed JSON loader; imports generated JSON files |

### Components (`src/components/`)

| Component | Purpose |
|-----------|---------|
| `LessonCard.astro` | Lesson summary card with title, metadata, tags |
| `LessonList.astro` | Sorted list of LessonCards |
| `RepoCard.astro` | Repository summary card |
| `TagList.astro` | Linked tag badges |
| `MetadataPanel.astro` | Lesson detail metadata grid |
| `SearchBox.astro` | Pagefind search UI |
| `ChatPanel.astro` | RAG chatbot UI (vanilla JS) |
| `CorpusGapNotice.astro` | Gap detection notification |

### Pages (`src/pages/`)

| Page | Route |
|------|-------|
| `index.astro` | `/` — homepage with stats and recent lessons |
| `lessons/index.astro` | `/lessons/` — all lessons with filtering and search |
| `lessons/[id].astro` | `/lessons/{id}` — lesson detail with rendered markdown |
| `repos/index.astro` | `/repos/` — all repos |
| `repos/[repo].astro` | `/repos/{id}` — repo detail with lessons |
| `tags/index.astro` | `/tags/` — all tags with counts |
| `tags/[tag].astro` | `/tags/{tag}` — lessons for a tag |
| `phases/index.astro` | `/phases/` — all phases |
| `phases/[phase].astro` | `/phases/{phase}` — lessons for a phase |
| `types/index.astro` | `/types/` — all lesson types |
| `types/[type].astro` | `/types/{type}` — lessons for a type |

## Generated Files (not committed)

| Path | Source | Content |
|------|--------|---------|
| `src/content/generated/lessons.json` | harvester | Full normalized lesson records |
| `src/content/generated/repos.json` | harvester | Repo metadata with lesson counts |
| `src/content/generated/tags.json` | harvester | Tag → lesson ID mapping |
| `src/content/generated/phases.json` | harvester | Phase → lesson ID mapping |
| `src/content/generated/lesson_types.json` | harvester | Type → lesson ID mapping |
| `public/exports/lessons-pack.json` | harvester | Full records (AI export) |
| `public/exports/lessons-index.json` | harvester | Compact records (AI export) |
| `public/exports/lessons-pack.md` | harvester | All lessons in markdown (AI export) |
| `data/rag-chunks.json` | corpus builder | RAG chunks (793 from 116 lessons) |
| `data/rag-manifest.json` | corpus builder | Corpus build statistics |
| `data/chromadb/` | embedder | ChromaDB vector store |
| `data/gaps/corpus-gaps.json` | gap detector | Gap records |
| `data/todos/` | lesson extractor | Coordination TODOs |

## Build Pipeline

```bash
npm run build:full
# Equivalent to:
# npm run harvest && npm run validate:lessons && npm run corpus && npm run validate:corpus && npm run build && npm run index
```

1. **Harvest**: clone repos, parse lessons, generate JSON + exports
2. **Validate**: check for errors (fail) and warnings (continue)
3. **Corpus**: chunk lessons into RAG corpus
4. **Build**: Astro compiles pages from generated JSON
5. **Index**: Pagefind creates search index from built HTML

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-deploy.yml` | push/PR to main, daily, manual | Lint + test + harvest + build + deploy to GitHub Pages |
| `deploy-staging.yml` | push to main | Build + deploy to staging + smoke tests |
| `deploy-production.yml` | after staging, or manual | Production deploy with approval gate |
| `deploy-aws.yml` | manual | ECR + ECS + S3 + CloudFront |
| `deploy-azure.yml` | manual | ACR + Container Apps + Static Web Apps |
| `deploy-gcp.yml` | manual | Artifact Registry + Cloud Run + Cloud Storage |

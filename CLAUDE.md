# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lessons Hub is a static website and build pipeline that consolidates markdown-based lesson documents from multiple GitHub repositories into one searchable, browsable, AI-readable lessons library. All source repos — whether owned by the maintainer or by external parties — are treated identically through the same harvest pipeline. Harvested lessons are checked into the hub repo with per-repo `index.md` files. Deployed via GitHub Pages.

V2 adds a RAG chatbot (FastAPI backend with LLM + vector adapters), gap detection, GitHub discovery, candidate lesson extraction, multi-cloud deployment infrastructure (AWS/Azure/GCP), and CI/CD hardening.

## Key Documents

- `docs/PDR.md` — V1 authoritative build spec
- `docs/PDR_V2.md` — V2 feature spec (RAG, gaps, discovery, cloud adapters)
- `docs/architecture.md` — System architecture, data flow, repo treatment
- `docs/project_walkthrough.md` — End-to-end walkthrough (rendered as About page)
- `docs/lesson-schema.md` — Frontmatter schema, controlled vocabularies, ID rules
- `docs/adding-a-repo.md` — How to add a source repository
- `docs/archive/` — Completed plans, historical reviews, superseded specs

## Technology Stack

- **Static site:** Astro (TypeScript, static output mode)
- **Backend:** FastAPI (Python 3.11+), Pydantic v2
- **RAG pipeline:** Ollama (local LLM/embeddings), ChromaDB (local vector store)
- **Cloud adapters:** AWS Bedrock+OpenSearch, Azure OpenAI+AI Search, GCP Vertex AI+Vector Search
- **Harvesting & validation:** Python 3.11+ (PyYAML, python-frontmatter, python-slugify)
- **Search:** Pagefind (static, no backend)
- **CI/CD:** GitHub Actions → GitHub Pages (+ staging/production + AWS/Azure/GCP deploy workflows)
- **Package management:** npm (Node), pip/pyproject.toml (Python)

## Build Commands

```bash
npm install                  # Install Node dependencies
pip install -e backend[dev]  # Install backend + dev dependencies
npm run harvest              # Clone source repos + generate JSON
npm run validate:lessons     # Validate harvested data
npm run build                # Astro build
npm run index                # Pagefind indexing (post-build)
npm run build:full           # Full pipeline: harvest → validate → corpus → build → index
npm run dev                  # Astro dev server (localhost:4331)
npm run backend              # Start FastAPI backend (localhost:8010)
npm run corpus               # Build RAG corpus from lessons.json
npm run validate:corpus      # Validate RAG corpus
```

## Testing

```bash
python -m pytest tests/           # Project tests (76): harvesting, validation, slugs, corpus
python -m pytest backend/tests/   # Backend tests (138): health, chat, adapters, gaps, discovery, cloud
ruff check backend/               # Lint
ruff format --check backend/      # Format check
```

**Important:** Use `python -m pytest` (not bare `pytest`) to avoid Python version mismatch issues on this machine where `python` (3.14) and the `pytest` binary (3.12) point to different interpreters.

## Architecture

### V1 Data Flow

```
data/repos.yml → harvest_lessons.py → [clone repos to tmp/repos/] → parse docs/lessons/*.md
    → normalize → src/content/generated/*.json + public/exports/*
    → validate_lessons.py → Astro build → Pagefind index → GitHub Pages deploy
```

### V2 Backend

```
ChatPanel.astro → POST /api/chat → FastAPI Backend
    → Retriever (embed query → vector search → top-k chunks)
    → Generator (build grounded prompt → LLM chat → extract citations)
    → GapDetector (7 rules → gap record if corpus can't answer)
    → Discovery (GitHub search → score repos → extract candidate lessons)
```

**Adapter pattern:** All LLM and vector operations go through abstract base classes (`LLMAdapter`, `VectorAdapter`). Cloud adapters use lazy imports — `import boto3` inside `__init__`, not at module level. Tests mock via `sys.modules.setdefault()` to avoid requiring cloud SDKs.

### Key Boundaries

- **All repos are treated identically** — whether owned by the project maintainer or by an external party. Every repo goes through the same harvest pipeline.
- **Source repos** store lessons at `docs/lessons/*.md` with optional YAML frontmatter.
- **Hub repo** owns the registry (`data/repos.yml`), harvesting, validation, rendering, and deployment.
- **Adding a new source repo** requires editing only `data/repos.yml`.
- **Backend runs independently** of the static site. If the backend is unavailable, the static site still works (chat panel shows fallback message).

### Generated Files (not committed)

- `src/content/generated/*.json` — lessons.json, repos.json, tags.json, phases.json, lesson_types.json
- `public/exports/` — lessons-pack.json, lessons-index.json, lessons-pack.md
- `data/rag-chunks.json`, `data/rag-manifest.json` — RAG corpus
- `data/chromadb/` — vector store
- `data/gaps/`, `data/todos/` — gap detection and coordination records
- `tmp/`, `dist/`, `.astro/`, `node_modules/`

### Repo Registry Schema (`data/repos.yml`)

Each entry under `repos:` requires: `id`, `name`, `owner`, `repo`, `branch`, `lessons_path`. Optional: `project_url`, `enabled`.

### Lesson Frontmatter

Required (after normalization): `title`. Recommended: `summary`, `date`, `phase`, `lesson_type`, `tags`. Lesson IDs are `{repo_id}-{lesson_slug}`. Controlled vocabularies for `lesson_type` and `status` are defined in PDR sections 11.

### Validation Severity

- **ERROR** (build fails): missing/invalid repos.yml, duplicate IDs, empty content, unreadable files, generated JSON invalid.
- **WARNING** (build continues): missing summary/date/tags/phase/type, unknown controlled values, short content.

## Security

- Never expose `LESSONS_REPO_TOKEN` in logs, generated files, or error output.
- Never print authenticated clone URLs.
- All cloud infrastructure uses OIDC/Workload Identity Federation — no long-lived credentials in GitHub secrets.

# Lessons Hub

A static website and build pipeline that consolidates markdown-based lesson documents from multiple GitHub repositories into one searchable, browsable, AI-readable lessons library. Includes a RAG-powered chatbot for querying lessons with source citations. Deployed via GitHub Pages.

## Architecture

```
data/repos.yml → harvest_lessons.py → [clone repos to tmp/repos/]
  → parse docs/lessons/*.md → normalize → generated JSON + exports
  → validate_lessons.py → Astro build → Pagefind index → GitHub Pages

ChatPanel.astro → POST /api/chat → FastAPI Backend
  → RAG retrieval → grounded LLM answer with citations
  → gap detection → GitHub discovery → candidate lesson extraction
```

### Key Components

- **Source repos** own their lessons at `docs/lessons/*.md` with optional YAML frontmatter
- **Hub repo** owns the registry (`data/repos.yml`), harvesting, validation, rendering, and deployment
- **Generated JSON** in `src/content/generated/` drives all Astro pages
- **Export packs** in `public/exports/` provide AI-readable lesson data
- **FastAPI backend** provides RAG chatbot, gap detection, and GitHub discovery (runs independently of the static site)

### V2 Features

- **RAG chatbot** — ask questions, get grounded answers citing specific lessons
- **Gap detection** — queries the corpus can't answer create trackable gap records
- **GitHub discovery** — gaps produce candidate external repos, scored and ranked
- **Multi-cloud deployment** — AWS (Bedrock + OpenSearch), Azure (OpenAI + AI Search), GCP (Vertex AI)
- **CI/CD hardening** — pytest, ruff, corpus validation; staging/production split with approval gates

## Source Repository Contract

Each participating repository stores lessons in `docs/lessons/*.md`. Each lesson is a standalone markdown document. Subdirectories are supported (e.g., `docs/lessons/phase1/*.md`).

### Frontmatter

Lessons may include YAML frontmatter:

```yaml
---
title: My Lesson Title
summary: One-line summary
date: 2025-01-15
phase: implementation
lesson_type: architecture
status: active
tags: [python, testing, ci-cd]
---
```

Required (after normalization): `title` (can be inferred from H1 or filename).
Recommended: `summary`, `date`, `tags`, `phase`, `lesson_type`.

## Adding a Source Repository

1. Edit `data/repos.yml` and add an entry:

```yaml
  - id: my-project
    name: My Project
    owner: github-username
    repo: repo-name
    branch: main
    lessons_path: docs/lessons
    project_url: https://github.com/username/repo
    enabled: true
```

2. Run `npm run harvest` to test
3. Run `npm run validate:lessons` to check for issues
4. Commit the updated `data/repos.yml`

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Git
- Ollama (for RAG chatbot, optional)

### Setup

```bash
npm install
pip install -e backend[dev]
```

### Commands

```bash
npm run dev              # Astro dev server
npm run harvest          # Clone repos and generate JSON
npm run validate:lessons # Validate harvested data
npm run build            # Astro build
npm run index            # Pagefind indexing
npm run build:full       # Full pipeline: harvest → validate → corpus → build → index
npm run backend          # Start FastAPI backend (localhost:8000)
npm run corpus           # Build RAG corpus from lessons.json
npm run validate:corpus  # Validate RAG corpus
```

### Testing

```bash
python -m pytest tests/           # Project tests (76)
python -m pytest backend/tests/   # Backend tests (102)
ruff check backend/               # Lint
ruff format --check backend/      # Format check
```

## Deployment

### GitHub Pages (default)

The site deploys automatically via GitHub Actions on:
- Push to `main`
- Manual workflow dispatch
- Daily schedule (6:00 UTC)

The workflow runs: checkout → Python/Node setup → lint → test → harvest → validate → corpus → build → Pagefind index → deploy to GitHub Pages.

For private repos, set the `LESSONS_REPO_TOKEN` secret in the repository settings.

### Cloud Deployment

AWS, Azure, and GCP deployment workflows are available via manual dispatch. Each uses OIDC/Workload Identity Federation for keyless CI/CD auth.

| Cloud | Backend | LLM | Vector Store | Workflow |
|-------|---------|-----|-------------|----------|
| AWS | ECS Fargate | Bedrock (Claude 3 Haiku) | OpenSearch Serverless | `deploy-aws.yml` |
| Azure | Container Apps | Azure OpenAI (gpt-4o-mini) | Azure AI Search | `deploy-azure.yml` |
| GCP | Cloud Run | Vertex AI (Gemini 1.5 Flash) | Vertex Vector Search | `deploy-gcp.yml` |

Infrastructure templates: `infra/aws/cloudformation.yml`, `infra/azure/main.bicep`, `infra/gcp/deploy.sh`.

## Export Files

After build, the following AI-readable exports are available at `/exports/`:

- `lessons-pack.json` — full normalized lesson records
- `lessons-index.json` — compact records (id, title, repo, summary, tags, url)
- `lessons-pack.md` — all lessons in one markdown document, grouped by repo

## Validation

Validation uses two severity levels:

- **ERROR** (build fails): missing registry, duplicate IDs, empty content, invalid JSON
- **WARNING** (build continues): missing summary/date/tags, unknown lesson types, short content

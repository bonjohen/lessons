# Lessons Hub

A static website and build pipeline that consolidates markdown-based lesson documents from multiple GitHub repositories into one searchable, browsable, AI-readable lessons library. Deployed via GitHub Pages.

## Architecture

```
data/repos.yml → harvest_lessons.py → [clone repos to tmp/repos/]
  → parse docs/lessons/*.md → normalize → generated JSON + exports
  → validate_lessons.py → Astro build → Pagefind index → GitHub Pages
```

### Key Components

- **Source repos** own their lessons at `docs/lessons/*.md` with optional YAML frontmatter
- **Hub repo** owns the registry (`data/repos.yml`), harvesting, validation, rendering, and deployment
- **Generated JSON** in `src/content/generated/` drives all Astro pages
- **Export packs** in `public/exports/` provide AI-readable lesson data

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

### Setup

```bash
npm install
pip install -r requirements.txt
```

### Commands

```bash
npm run dev              # Astro dev server
npm run harvest          # Clone repos and generate JSON
npm run validate:lessons # Validate harvested data
npm run build            # Astro build
npm run index            # Pagefind indexing
npm run build:full       # Full pipeline: harvest → validate → build → index
```

### Python Scripts

```bash
python scripts/harvest_lessons.py    # Harvest lessons
python scripts/validate_lessons.py   # Validate data
```

## Deployment

The site deploys automatically via GitHub Actions on:
- Push to `main`
- Manual workflow dispatch
- Daily schedule (6:00 UTC)

The workflow runs: checkout → Python/Node setup → harvest → validate → build → Pagefind index → deploy to GitHub Pages.

For private repos, set the `LESSONS_REPO_TOKEN` secret in the repository settings.

## Export Files

After build, the following AI-readable exports are available at `/exports/`:

- `lessons-pack.json` — full normalized lesson records
- `lessons-index.json` — compact records (id, title, repo, summary, tags, url)
- `lessons-pack.md` — all lessons in one markdown document, grouped by repo

## Validation

Validation uses two severity levels:

- **ERROR** (build fails): missing registry, duplicate IDs, empty content, invalid JSON
- **WARNING** (build continues): missing summary/date/tags, unknown lesson types, short content

## V1 Scope

Version 1 includes: Astro static site, Python harvester/validator, Pagefind search, AI exports, GitHub Actions deployment, and documentation.

Not included in V1: database, auth, comments, online editing, embeddings, vector search, graph visualization.

## Testing

```bash
pytest
```

Tests cover repo config parsing, lesson frontmatter parsing, slug generation, and validation rules.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lessons Hub is a static website and build pipeline that consolidates markdown-based lesson documents from multiple GitHub repositories into one searchable, browsable, AI-readable lessons library. Deployed via GitHub Pages. No backend, no database, no auth — static output only (Version 1).

The full specification lives in `docs/PDR.md`. Treat that as the authoritative build spec.

## Technology Stack

- **Static site:** Astro (TypeScript, static output mode)
- **Harvesting & validation:** Python 3.11+ (PyYAML, python-frontmatter, python-slugify, pathlib, subprocess)
- **Search:** Pagefind (static, no backend)
- **CI/CD:** GitHub Actions → GitHub Pages
- **Package management:** npm (Node), pip/requirements.txt (Python)

## Build Commands

```bash
npm install                  # Install Node dependencies
pip install -r requirements.txt  # Install Python dependencies
npm run harvest              # Clone source repos + generate JSON
npm run validate:lessons     # Validate harvested data
npm run build                # Astro build
npm run index                # Pagefind indexing (post-build)
npm run build:full           # Full pipeline: harvest → validate → build → index
npm run dev                  # Astro dev server
```

## Python Scripts

```bash
python scripts/harvest_lessons.py    # Harvest lessons from repos in data/repos.yml
python scripts/validate_lessons.py   # Validate generated lesson data
```

## Testing

```bash
pytest                       # Run Python tests
```

Test files live in `tests/` and cover repo config parsing, lesson frontmatter parsing, slug generation, and validation rules.

## Architecture

### Data Flow

```
data/repos.yml → harvest_lessons.py → [clone repos to tmp/repos/] → parse docs/lessons/*.md
    → normalize → src/content/generated/*.json + public/exports/*
    → validate_lessons.py → Astro build → Pagefind index → GitHub Pages deploy
```

### Key Boundaries

- **Source repos** own their lessons at `docs/lessons/*.md` with optional YAML frontmatter.
- **Hub repo** owns the registry (`data/repos.yml`), harvesting, validation, rendering, and deployment.
- **Adding a new source repo** requires editing only `data/repos.yml`.

### Generated Files (not committed)

- `src/content/generated/*.json` — lessons.json, repos.json, tags.json, phases.json, lesson_types.json
- `public/exports/` — lessons-pack.json, lessons-index.json, lessons-pack.md
- `tmp/` — cloned repos during harvest
- `dist/`, `.astro/`, `node_modules/`

### Repo Registry Schema (`data/repos.yml`)

Each entry under `repos:` requires: `id`, `name`, `owner`, `repo`, `branch`, `lessons_path`. Optional: `project_url`, `enabled`.

### Lesson Frontmatter

Required (after normalization): `title`. Recommended: `summary`, `date`, `phase`, `lesson_type`, `tags`. Lesson IDs are `{repo_id}-{lesson_slug}`. Controlled vocabularies for `lesson_type` and `status` are defined in PDR sections 11.

### Validation Severity

- **ERROR** (build fails): missing/invalid repos.yml, duplicate IDs, empty content, unreadable files, generated JSON invalid.
- **WARNING** (build continues): missing summary/date/tags/phase/type, unknown controlled values, short content.

## Site Pages

Astro pages at `src/pages/`: home, `/lessons/`, `/lessons/[id]`, `/repos/`, `/repos/[repo]`, `/tags/`, `/tags/[tag]`, `/phases/`, `/phases/[phase]`, `/types/`, `/types/[type]`. Components at `src/components/`.

## Security

- Never expose `LESSONS_REPO_TOKEN` in logs, generated files, or error output.
- Never print authenticated clone URLs.

## Implementation Phases

The PDR defines 8 phases (section 31): skeleton → registry + harvester → validation → static pages → search → export packs → GitHub Pages deployment → documentation. Suggested document ordering for additional planning is in `docs/DPR-suggestions.md`.

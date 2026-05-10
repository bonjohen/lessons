# Startup Instructions

Resume file for Lessons Hub implementation. Read this, then execute.

## Current State

- **Branch:** `main`
- **Active plan:** `docs/lessons_hub_plan.md`
- **Current phase:** Phase 1 (Project Skeleton) — not yet started, all rows Open
- **PDR:** `docs/PDR.md` (authoritative spec)
- **CLAUDE.md:** exists at repo root
- **Commits so far:** none (repo initialized with only `docs/` directory)
- **Existing files:** `docs/PDR.md`, `docs/DPR-suggestions.md`, `docs/lessons_hub_plan.md`, `CLAUDE.md`
- **No code exists yet.** No `package.json`, no `src/`, no `scripts/`, no `astro.config.mjs`.

## What To Do

1. Read `docs/lessons_hub_plan.md` (the plan file — it has the task table).
2. Read `docs/PDR.md` sections 7-8 (tech stack and repo layout) for reference.
3. Execute Phase 1 using `/phase docs/lessons_hub_plan.md`.
4. Phase 1 tasks (1.1–1.11) create the Astro skeleton: init project, `.gitignore`, directory scaffold, base layout, placeholder pages, sample JSON stubs, `requirements.txt`, README stub, verify, commit.

## Key Decisions Already Made

- **Astro** static output mode with TypeScript.
- **Python 3.11+** for harvesting/validation (PyYAML, python-frontmatter, python-slugify).
- **Pagefind** for search (installed in Phase 5, not Phase 1).
- Generated JSON stubs go in `src/content/generated/` so Astro can build before the harvester exists.
- Styling: simple, documentation-oriented, low-noise. No heavy frameworks.
- `.gitignore` must exclude `dist/`, `tmp/`, `.astro/`, `node_modules/`, `src/content/generated/*.json`, `public/exports/*.json`, `public/exports/*.md`.

## Effort Level

Set `/effort low` before starting Phase 1. It is mechanical scaffold work.

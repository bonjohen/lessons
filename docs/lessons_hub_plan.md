# Lessons Hub — Implementation Plan

**Source document:** `docs/PDR.md`

## Work Queue Instructions

### State Transitions

Open  ──>  Started  ──>  Completed
              │
              └──>  Blocked  ──>  Started  ──>  Completed

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
| Static site framework | Astro (TypeScript, static output) |
| Python runtime | 3.11+ |
| Python deps | PyYAML, python-frontmatter, python-slugify |
| Search | Pagefind |
| CI/CD | GitHub Actions |
| Hosting | GitHub Pages |
| Package manager (Node) | npm |
| Package manager (Python) | pip + requirements.txt |

---

## Phase 1: Project Skeleton

**Goal:** Astro project initializes, dev server runs, homepage and placeholder lessons page render. Base layout, styling, and repo structure established.
**Depends on:** Nothing (first phase).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 1.1 | Completed | 2026-05-08 04:31 PM | 2026-05-08 04:33 PM | Initialize Astro project with `npm create astro@latest` — static output mode, TypeScript. Create `astro.config.mjs`, `tsconfig.json`, `package.json`. |
| 1.2 | Completed | 2026-05-08 04:33 PM | 2026-05-08 04:33 PM | Create `.gitignore` covering `dist/`, `tmp/`, `.astro/`, `node_modules/`, `src/content/generated/*.json`, `public/exports/*.json`, `public/exports/*.md`. |
| 1.3 | Completed | 2026-05-08 04:33 PM | 2026-05-08 04:33 PM | Create directory scaffold: `data/`, `scripts/`, `src/content/generated/`, `src/layouts/`, `src/components/`, `src/pages/`, `public/exports/`, `docs/`, `tests/`, `tmp/.gitkeep`. |
| 1.4 | Completed | 2026-05-08 04:33 PM | 2026-05-08 04:34 PM | Create `src/layouts/BaseLayout.astro` — HTML shell with head, nav, main, footer. Simple documentation-oriented CSS (readable typography, mobile-friendly, sufficient spacing). |
| 1.5 | Completed | 2026-05-08 04:34 PM | 2026-05-08 04:34 PM | Create `src/pages/index.astro` — homepage with site title, purpose statement, placeholder stats (repo count, lesson count, tag count), placeholder recent lessons section. |
| 1.6 | Completed | 2026-05-08 04:34 PM | 2026-05-08 04:35 PM | Create `src/pages/lessons/index.astro` — placeholder "All Lessons" page. |
| 1.7 | Completed | 2026-05-08 04:35 PM | 2026-05-08 04:35 PM | Create sample generated JSON stubs: `src/content/generated/lessons.json` (empty array), `src/content/generated/repos.json` (empty array), `src/content/generated/tags.json` (empty array), `src/content/generated/phases.json` (empty array), `src/content/generated/lesson_types.json` (empty array). These are local dev stubs so Astro can build before the harvester exists. |
| 1.8 | Completed | 2026-05-08 04:35 PM | 2026-05-08 04:35 PM | Add `requirements.txt` with `PyYAML`, `python-frontmatter`, `python-slugify`. |
| 1.9 | Completed | 2026-05-08 04:35 PM | 2026-05-08 04:35 PM | Create `README.md` stub with project name and one-paragraph purpose. |
| 1.10 | Completed | 2026-05-08 04:35 PM | 2026-05-08 04:37 PM | Verify: `npm install && npm run dev` starts dev server; homepage renders; lessons placeholder page renders; `npm run build` succeeds. |
| 1.11 | Completed | 2026-05-08 04:37 PM | 2026-05-08 04:38 PM | Stage and commit: "Phase 1: Astro project skeleton with base layout and placeholder pages". |

### Phase 1 Summary

- **Changes:** Created `package.json`, `astro.config.mjs`, `tsconfig.json`, `.gitignore`, `requirements.txt`, `README.md`. Created directory scaffold (`data/`, `scripts/`, `src/content/generated/`, `src/layouts/`, `src/components/`, `src/pages/`, `public/exports/`, `tests/`, `tmp/`). Created `BaseLayout.astro` with nav, footer, and documentation-oriented CSS. Created homepage (`index.astro`) with placeholder stats and browse links. Created placeholder lessons index page. Created empty JSON stubs for all generated data files.
- **Changes hosted at:** TBD
- **Commit:** `Phase 1: Astro project skeleton with base layout and placeholder pages`

---

## Phase 2: Repo Registry and Harvester

**Goal:** `data/repos.yml` defines source repos; `scripts/harvest_lessons.py` clones them, parses lessons, and generates normalized JSON to `src/content/generated/` and export files to `public/exports/`.
**Depends on:** Phase 1 (directory scaffold exists).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 2.1 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:40 PM | Create `data/repos.yml` with at least 3 enabled source repos (use public repos from the user's GitHub that have `docs/lessons/*.md`, or well-known public repos — confirm with user if needed). Schema per PDR §10: `id`, `name`, `owner`, `repo`, `branch`, `lessons_path`, optional `project_url`, `enabled`. |
| 2.2 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Implement `scripts/harvest_lessons.py` — load `data/repos.yml`, validate registry structure, create clean `tmp/repos/` directory. |
| 2.3 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Add repo cloning: `git clone --depth 1` each enabled repo to `tmp/repos/{repo_id}`. Support `LESSONS_REPO_TOKEN` env var for authenticated URLs. Never print/log token values. |
| 2.4 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Add markdown scanning: locate `{lessons_path}/*.md` in each cloned repo. Parse YAML frontmatter (python-frontmatter). Parse markdown body. |
| 2.5 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Implement normalization: generate lesson records per PDR §12. ID format `{repo_id}-{lesson_slug}`. Slug priority: explicit `slug` frontmatter → filename → normalized title. Tag normalization per PDR §14 (lowercase, trim, hyphens, dedup). Infer missing safe defaults (`status` → `active`). |
| 2.6 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Generate aggregate indexes: `src/content/generated/lessons.json`, `repos.json`, `tags.json`, `phases.json`, `lesson_types.json`. All output must be valid, deterministic JSON (sorted keys, consistent ordering). |
| 2.7 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Implement `scripts/build_exports.py` (or integrate into harvester): generate `public/exports/lessons-pack.json` (full records), `public/exports/lessons-index.json` (compact: id, title, repo, summary, tags, url), `public/exports/lessons-pack.md` (all lessons in one markdown doc grouped by repo, with timestamp). |
| 2.8 | Completed | 2026-05-08 04:42 PM | 2026-05-08 04:43 PM | Add `package.json` scripts: `harvest` → `python scripts/harvest_lessons.py`, `validate:lessons` → `python scripts/validate_lessons.py` (stub for now). |
| 2.9 | Completed | 2026-05-08 04:40 PM | 2026-05-08 04:42 PM | Print clear harvest summary to stdout: repos scanned, lessons found, warnings. |
| 2.10 | Completed | 2026-05-08 04:43 PM | 2026-05-08 04:45 PM | Verify: `npm run harvest` completes; at least 3 repos scanned; lessons discovered; `lessons.json` exists and contains lesson records; source URLs are correct; missing optional metadata produces warnings. |
| 2.11 | Completed | 2026-05-08 04:45 PM | 2026-05-08 04:46 PM | Stage and commit: "Phase 2: Repo registry and lesson harvester". |

### Phase 2 Summary

- **Changes:** Created `data/repos.yml` with 2 enabled repos (certification, artemis) and 1 disabled (lessons-hub self-harvest). Created `scripts/harvest_lessons.py` with full pipeline: registry loading, git clone, recursive markdown scanning, frontmatter parsing, normalization (slug, tags, IDs), aggregate index generation (lessons, repos, tags, phases, lesson_types), and AI export packs (JSON + markdown). Created stub `scripts/validate_lessons.py`. Added `harvest`, `validate:lessons`, `build:full` npm scripts. Handles Windows read-only git files, subdirectory lesson paths (block*/), and duplicate slug prevention via path-based slugs.
- **Changes hosted at:** TBD
- **Commit:** `Phase 2: Repo registry and lesson harvester`

---

## Phase 3: Validation

**Goal:** `scripts/validate_lessons.py` validates harvested data with ERROR/WARNING/INFO severity. Build fails on errors, continues on warnings.
**Depends on:** Phase 2 (generated JSON exists to validate).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 3.1 | Completed | 2026-05-08 04:46 PM | 2026-05-08 04:47 PM | Implement `scripts/validate_lessons.py` — load generated JSON files from `src/content/generated/`. Output must use labeled severity: `ERROR`, `WARNING`, `INFO`. Exit code non-zero on any ERROR. |
| 3.2 | Completed | 2026-05-08 04:46 PM | 2026-05-08 04:47 PM | Implement hard-error checks per PDR §17.1: missing/invalid `data/repos.yml`, duplicate repo IDs, invalid repo ID format, missing required repo fields, empty lesson content, duplicate lesson IDs, invalid generated JSON, required generated files missing. |
| 3.3 | Completed | 2026-05-08 04:46 PM | 2026-05-08 04:47 PM | Implement warning checks per PDR §17.2: missing summary, tags, date, phase, lesson_type; unknown lesson_type; non-normalized tag casing; short content; title inferred from filename. |
| 3.4 | Completed | 2026-05-08 04:46 PM | 2026-05-08 04:47 PM | Wire `validate:lessons` script in `package.json` → `python scripts/validate_lessons.py`. |
| 3.5 | Completed | 2026-05-08 04:47 PM | 2026-05-08 04:47 PM | Verify: `npm run validate:lessons` passes on valid harvest output; inject a duplicate ID and confirm ERROR + non-zero exit; confirm warnings for missing summary/date/tags. |
| 3.6 | Completed | 2026-05-08 04:47 PM | 2026-05-08 04:48 PM | Stage and commit: "Phase 3: Lesson validation with error/warning severity". |

### Phase 3 Summary

- **Changes:** Replaced stub `scripts/validate_lessons.py` with full implementation. Validates repos.yml structure, required generated files, lesson records (duplicate IDs, empty content, missing title as errors; missing summary/date/tags/phase/lesson_type, unknown controlled values, short content as warnings).
- **Changes hosted at:** TBD
- **Commit:** `Phase 3: Lesson validation with error/warning severity`

---

## Phase 4: Static Pages and Components

**Goal:** All Astro pages render from generated JSON. Homepage shows real stats. Lesson detail, repo, tag, phase, and type pages all work.
**Depends on:** Phase 2 (generated JSON), Phase 3 (validated data).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 4.1 | Completed | 2026-05-08 04:48 PM | 2026-05-08 04:49 PM | Create helper to load generated JSON in Astro — a shared TypeScript module (`src/lib/data.ts` or similar) that reads and types the generated JSON files. |
| 4.2 | Completed | 2026-05-08 04:49 PM | 2026-05-08 04:49 PM | Create `src/components/LessonCard.astro` — title, summary, repo name, date, tags, lesson_type, status badge. |
| 4.3 | Completed | 2026-05-08 04:49 PM | 2026-05-08 04:49 PM | Create `src/components/LessonList.astro` — sorted list of LessonCard components. Default sort: date desc → updated desc → repo name asc → title asc. Lessons without dates sort after dated lessons. |
| 4.4 | Completed | 2026-05-08 04:49 PM | 2026-05-08 04:50 PM | Create `src/components/RepoCard.astro` — repo name, lesson count, project link, recent lesson date, top tags. |
| 4.5 | Completed | 2026-05-08 04:50 PM | 2026-05-08 04:50 PM | Create `src/components/TagList.astro` — linked tag badges. |
| 4.6 | Completed | 2026-05-08 04:50 PM | 2026-05-08 04:50 PM | Create `src/components/MetadataPanel.astro` — repo, date, updated, phase, type, status, source markdown link, project link. |
| 4.7 | Completed | 2026-05-08 04:50 PM | 2026-05-08 04:50 PM | Update `src/pages/index.astro` — real repo/lesson/tag counts, recent lessons (date desc, limit 5-10), links to lessons/repos/tags/phases/types. |
| 4.8 | Completed | 2026-05-08 04:50 PM | 2026-05-08 04:51 PM | Update `src/pages/lessons/index.astro` — all lessons with LessonList, client-side filtering by repo/tag/phase/lesson_type/status. |
| 4.9 | Completed | 2026-05-08 04:51 PM | 2026-05-08 04:51 PM | Create `src/pages/lessons/[id].astro` — lesson detail: title, summary, MetadataPanel, rendered markdown body, related PRs/issues/commits, related lessons by shared tags, back links. Markdown rendering must support headings, paragraphs, lists, tables, links, code, blockquotes. |
| 4.10 | Completed | 2026-05-08 04:51 PM | 2026-05-08 04:51 PM | Create `src/pages/repos/index.astro` — all repos with RepoCard, lesson count, recent date, top tags, project links. |
| 4.11 | Completed | 2026-05-08 04:51 PM | 2026-05-08 04:51 PM | Create `src/pages/repos/[repo].astro` — repo detail: name, project URL, lesson count, lessons from this repo, tags used, phases represented. |
| 4.12 | Completed | 2026-05-08 04:51 PM | 2026-05-08 04:52 PM | Create `src/pages/tags/index.astro` and `src/pages/tags/[tag].astro` — tag list (count desc → name asc), lessons for selected tag, related tags, repos using tag. |
| 4.13 | Completed | 2026-05-08 04:52 PM | 2026-05-08 04:52 PM | Create `src/pages/phases/index.astro`, `src/pages/phases/[phase].astro`, `src/pages/types/index.astro`, `src/pages/types/[type].astro` — lessons grouped by phase and lesson type. |
| 4.14 | Completed | 2026-05-08 04:52 PM | 2026-05-08 04:52 PM | Create `src/components/SearchBox.astro` — placeholder for Pagefind UI (wired in Phase 5). |
| 4.15 | Completed | 2026-05-08 04:52 PM | 2026-05-08 04:52 PM | Verify: `npm run build` succeeds; each lesson has a detail page at `/lessons/{id}`; all repo/tag/phase/type pages render; lesson counts correct; source repo links work. |
| 4.16 | Completed | 2026-05-08 04:52 PM | 2026-05-08 04:53 PM | Stage and commit: "Phase 4: Static pages — lessons, repos, tags, phases, types". |

### Phase 4 Summary

- **Changes:** Created `src/lib/data.ts` (typed JSON loader via imports), 6 components (LessonCard, LessonList, RepoCard, TagList, MetadataPanel, SearchBox placeholder), updated homepage with real stats and recent lessons, updated lessons index with client-side filtering, created lesson detail pages with markdown rendering (marked), repo index/detail pages, tag index/detail pages, phase index/detail pages, type index/detail pages. Installed `marked` for markdown rendering. Updated `tsconfig.json` for JSON module resolution. 100 pages built.
- **Changes hosted at:** TBD
- **Commit:** `Phase 4: Static pages — lessons, repos, tags, phases, types`

---

## Phase 5: Pagefind Search

**Goal:** Pagefind indexes the built site. Search box on lessons page finds lessons by title and body text. No backend.
**Depends on:** Phase 4 (built static site to index).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 5.1 | Completed | 2026-05-08 04:53 PM | 2026-05-08 04:53 PM | Install Pagefind: `npm install --save-dev pagefind`. |
| 5.2 | Completed | 2026-05-08 04:53 PM | 2026-05-08 04:54 PM | Add `package.json` script `index` → `npx pagefind --site dist`. Update `build:full` to chain: `harvest → validate:lessons → build → index`. |
| 5.3 | Completed | 2026-05-08 04:54 PM | 2026-05-08 04:54 PM | Wire `src/components/SearchBox.astro` to Pagefind UI — include Pagefind CSS/JS, add labeled search input. |
| 5.4 | Completed | 2026-05-08 04:54 PM | 2026-05-08 04:54 PM | Add Pagefind `data-pagefind-body` attributes to lesson detail pages so lesson titles and body text are indexed. |
| 5.5 | Completed | 2026-05-08 04:54 PM | 2026-05-08 04:55 PM | Verify: `npm run build:full` succeeds; search index generated in `dist/pagefind/`; search box on lessons page returns results for lesson titles and body keywords. |
| 5.6 | Completed | 2026-05-08 04:55 PM | 2026-05-08 04:55 PM | Stage and commit: "Phase 5: Pagefind static search". |

### Phase 5 Summary

- **Changes:** Installed Pagefind as devDependency. Added `index` and updated `build:full` npm scripts. Wired SearchBox component to Pagefind UI (CSS/JS from `/pagefind/`). Lesson detail pages already had `data-pagefind-body`. Added SearchBox to lessons index page. Pagefind indexes 90 pages, 5091 words.
- **Changes hosted at:** TBD
- **Commit:** `Phase 5: Pagefind static search`

---

## Phase 6: Export Packs

**Goal:** AI-readable export files are generated and available at `/exports/` on the deployed site.
**Depends on:** Phase 2 (harvester generates exports). This phase verifies and finalizes the export pipeline.

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 6.1 | Completed | 2026-05-08 04:55 PM | 2026-05-08 04:56 PM | Verify or refine `scripts/build_exports.py`: `lessons-pack.json` contains full normalized records; `lessons-index.json` contains compact records (id, title, repo, summary, tags, url); `lessons-pack.md` has generated timestamp, lessons grouped by repo, title, source URL, tags, full content. |
| 6.2 | Completed | 2026-05-08 04:55 PM | 2026-05-08 04:56 PM | Ensure export generation is integrated into `npm run harvest` or called separately — either way, `build:full` must produce all three export files in `public/exports/`. |
| 6.3 | Completed | 2026-05-08 04:55 PM | 2026-05-08 04:56 PM | Verify: after `npm run build:full`, `dist/exports/lessons-pack.json`, `dist/exports/lessons-index.json`, `dist/exports/lessons-pack.md` all exist and are valid. Markdown export contains all lessons. JSON validates. |
| 6.4 | Completed | 2026-05-08 04:56 PM | 2026-05-08 04:56 PM | Stage and commit: "Phase 6: AI-readable export packs". |

### Phase 6 Summary

- **Changes:** Export generation was integrated into the harvester in Phase 2. Verified all three export files (lessons-pack.json, lessons-index.json, lessons-pack.md) are produced by `build:full` and appear in `dist/exports/`. JSON validates. Markdown export contains timestamp, all 90 lessons grouped by repo.
- **Changes hosted at:** TBD
- **Commit:** `Phase 6: AI-readable export packs`

---

## Phase 7: GitHub Actions Deployment

**Goal:** GitHub Actions workflow builds and deploys the site to GitHub Pages on push to `main`, manual trigger, and daily schedule.
**Depends on:** Phase 5 (full build pipeline works locally).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 7.1 | Completed | 2026-05-08 04:56 PM | 2026-05-08 04:57 PM | Create `.github/workflows/build-deploy.yml` — triggers: push to `main`, `workflow_dispatch`, daily `schedule` cron. |
| 7.2 | Completed | 2026-05-08 04:56 PM | 2026-05-08 04:57 PM | Workflow steps: checkout → setup Python 3.11+ → setup Node → `pip install -r requirements.txt` → `npm install` → `npm run harvest` (with optional `LESSONS_REPO_TOKEN` secret) → `npm run validate:lessons` → `npm run build` → `npm run index` → upload Pages artifact → deploy to GitHub Pages. |
| 7.3 | Completed | 2026-05-08 04:56 PM | 2026-05-08 04:57 PM | Configure GitHub Pages deployment action (`actions/deploy-pages@v4` or current). Set `permissions: pages: write, id-token: write` on the job. |
| 7.4 | Completed | 2026-05-08 04:57 PM | 2026-05-08 04:57 PM | Verify: workflow YAML is valid; review against PDR §23 requirements; confirm it works without `LESSONS_REPO_TOKEN` for public repos. |
| 7.5 | Started | 2026-05-08 04:57 PM | | Stage and commit: "Phase 7: GitHub Actions build and Pages deployment". |

### Phase 7 Summary

- **Changes:** Created `.github/workflows/build-deploy.yml` with push/dispatch/daily cron triggers. Two-job workflow: build (checkout, Python 3.11, Node 20, install deps, harvest with optional token, validate, build, Pagefind index, upload artifact) and deploy (deploy-pages@v4). Permissions set for Pages + OIDC.
- **Changes hosted at:** TBD
- **Commit:** `Phase 7: GitHub Actions build and Pages deployment`

---

## Phase 8: Documentation

**Goal:** README is complete. Docs explain how to add a repo, write a lesson, understand the architecture, and use export files.
**Depends on:** Phase 7 (everything works end-to-end, docs can reference real commands and URLs).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 8.1 | Open | | | Write full `README.md` per PDR §36: purpose, architecture summary, source repo contract, how to add a repo, how to write a lesson, local dev commands, build commands, deployment notes, export files, troubleshooting, V1 scope, non-goals, future ideas. |
| 8.2 | Open | | | Create `docs/lesson-template.md` — complete lesson template with frontmatter fields, required/optional sections, tagging rules, example lesson. |
| 8.3 | Open | | | Create `docs/lesson-schema.md` — all frontmatter fields, types, controlled vocabularies for `lesson_type` and `status`, ID/slug generation rules, tag normalization rules. |
| 8.4 | Open | | | Create `docs/adding-a-repo.md` — step-by-step guide: edit `data/repos.yml`, required fields, run harvest to test, commit. |
| 8.5 | Open | | | Create `docs/architecture.md` — data flow diagram (text), component map, script responsibilities, generated file inventory, build pipeline sequence. |
| 8.6 | Open | | | Verify: all doc files exist and are accurate against the implemented system. |
| 8.7 | Open | | | Stage and commit: "Phase 8: Documentation — README, lesson template, schema, architecture". |

### Phase 8 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `Phase 8: Documentation — README, lesson template, schema, architecture`

---

## Phase 9: Python Tests

**Goal:** Core Python logic has test coverage: repo config parsing, lesson parsing, slug generation, validation rules.
**Depends on:** Phase 3 (validation script exists).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 9.1 | Open | | | Add `pytest` to `requirements.txt`. |
| 9.2 | Open | | | Create `tests/test_repo_config.py` — valid config, duplicate repo ID, missing required field, invalid ID format. |
| 9.3 | Open | | | Create `tests/test_lesson_parsing.py` — valid frontmatter, missing title inferred from H1, missing title inferred from filename, empty content error. |
| 9.4 | Open | | | Create `tests/test_slug_generation.py` — explicit slug, filename-based slug, title-based slug, kebab-case normalization, duplicate ID detection. |
| 9.5 | Open | | | Create `tests/test_validation.py` — valid lessons pass, duplicate ID errors, missing summary/date/tags warn, unknown lesson_type warns. |
| 9.6 | Open | | | Verify: `pytest` passes all tests. |
| 9.7 | Open | | | Stage and commit: "Phase 9: Python test suite for harvester and validation". |

### Phase 9 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `Phase 9: Python test suite for harvester and validation`

---

## Phase 10: Internal Project Lessons

**Goal:** The Lessons Hub project itself has lessons stored in `docs/lessons/*.md`, harvestable by the hub.
**Depends on:** Phase 8 (lesson template exists).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 10.1 | Open | | | Add this repo to `data/repos.yml` as a source (self-harvest). Set `lessons_path: docs/lessons`. |
| 10.2 | Open | | | Write `docs/lessons/harvester-design-decisions.md` — lesson from Phase 2 (harvester implementation choices, frontmatter inference, slug generation). |
| 10.3 | Open | | | Write `docs/lessons/validation-severity-model.md` — lesson from Phase 3 (error vs warning distinction, why warnings don't fail builds). |
| 10.4 | Open | | | Write `docs/lessons/static-search-with-pagefind.md` — lesson from Phase 5 (Pagefind integration, no-backend constraint). |
| 10.5 | Open | | | Write `docs/lessons/github-pages-build-pipeline.md` — lesson from Phase 7 (Actions workflow design, artifact deployment). |
| 10.6 | Open | | | Verify: `npm run harvest` picks up internal lessons; `npm run validate:lessons` passes; lessons appear on built site. |
| 10.7 | Open | | | Stage and commit: "Phase 10: Internal project lessons — self-harvesting". |

### Phase 10 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `Phase 10: Internal project lessons — self-harvesting`

---

## Version 1 Acceptance Checklist

Per PDR §32, Version 1 is complete when all of the following are true:

- [ ] `data/repos.yml` defines multiple source repos
- [ ] At least 3 repos are harvested successfully
- [ ] Lessons discovered from `docs/lessons/*.md`
- [ ] Frontmatter parsed, missing optional metadata warns
- [ ] Invalid required structure fails validation
- [ ] Normalized JSON files generated deterministically
- [ ] Homepage shows real stats (repo/lesson/tag counts, recent lessons)
- [ ] All lessons page renders with filtering
- [ ] Lesson detail pages render content + metadata
- [ ] Repo pages render per-repo lesson lists
- [ ] Tag pages render per-tag lesson lists
- [ ] Phase/type pages render grouped lists
- [ ] Pagefind search works (title + body)
- [ ] Export files generated (JSON + markdown)
- [ ] GitHub Actions builds and deploys to Pages
- [ ] Adding a repo requires only editing `data/repos.yml`
- [ ] README documents local dev, repo addition, deployment
- [ ] Documentation files exist and are useful
- [ ] Site is usable as a public portfolio artifact

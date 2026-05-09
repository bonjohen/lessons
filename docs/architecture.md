# Architecture

## Repo Treatment

All source repos are treated identically regardless of ownership. Whether the repo belongs to the project maintainer or an external contributor, it goes through the same pipeline: register in `data/repos.yml`, harvest, validate, render. There is no separate workflow for "external" or "candidate" repos.

Each source repo gets an `index.md` checked into the lessons project that documents:
- The source repository URL and owner
- A brief description of the project
- An overview of the harvested lesson files

## Data Flow

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

## Component Map

### Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `harvest_lessons.py` | Clone repos, parse lessons, generate JSON + exports |
| `validate_lessons.py` | Validate repos.yml and generated data |

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

## Build Pipeline

```bash
npm run build:full
# Equivalent to:
# npm run harvest && npm run validate:lessons && npm run build && npm run index
```

1. **Harvest**: clone repos, parse lessons, generate JSON + exports
2. **Validate**: check for errors (fail) and warnings (continue)
3. **Build**: Astro compiles pages from generated JSON
4. **Index**: Pagefind creates search index from built HTML

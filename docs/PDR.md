# PDR.md

# Physical Design Requirements: Lessons Hub

## 1. Project Name

Lessons Hub

## 2. Project Purpose

Lessons Hub is a GitHub-hosted static website and supporting build pipeline that consolidates markdown-based lesson documents from multiple GitHub repositories into one searchable, browsable, AI-readable lessons library.

Each source repository owns its own lessons under:

`docs/lessons/*.md`

The Lessons Hub repository owns:

* the source repository registry
* lesson harvesting
* metadata normalization
* validation
* static site rendering
* full-text static search
* AI-readable export packs
* GitHub Pages deployment
* documentation for adding new repositories and writing consistent lessons

The project should function as both a useful personal engineering knowledge base and a public demonstration project showing software architecture, automation, static publishing, validation, documentation, and lessons-learned discipline.

## 3. Project Type

Lessons Hub is a static documentation/data-processing project with a build-time data pipeline.

It is not a dynamic web application in Version 1.

The final deployed site is static HTML, CSS, JavaScript, JSON, and markdown-derived content hosted through GitHub Pages.

## 4. Primary Users

### 4.1 Human Readers

Human readers use the site to browse lessons by:

* project
* repository
* tag
* phase
* lesson type
* date
* status
* keyword search

### 4.2 Future Maintainers

Future maintainers use the project to:

* add new source repositories
* update lesson schema rules
* validate lesson files
* troubleshoot failed builds
* improve static site pages
* extend the harvesting/export pipeline

### 4.3 AI Coding Agents

AI coding agents use generated export files to:

* understand prior project lessons
* avoid repeating previous mistakes
* reuse known implementation patterns
* review project-specific engineering rules
* support future coding tasks with historical project context

## 5. Version 1 Scope

Version 1 must build a working static Lessons Hub site from lessons stored in multiple GitHub repositories.

Version 1 must include:

* Astro static site
* Python harvesting scripts
* Python validation scripts
* source repository registry
* normalized generated JSON
* generated static lesson pages
* generated repo pages
* generated tag pages
* generated phase/type pages
* Pagefind static search
* AI export files
* GitHub Actions build workflow
* GitHub Pages deployment
* documentation
* lesson template
* repo addition guide

## 6. Version 1 Non-Goals

Version 1 must not include:

* database backend
* authentication UI
* user accounts
* comments
* online editing
* browser-side GitHub API fetching
* automatic AI lesson generation
* PR mining
* commit mining
* issue mining
* embeddings
* vector search
* graph visualization
* private repo publishing controls beyond basic clone-token support
* complex access-control logic
* cloud-provider deployment beyond GitHub Pages

These may be considered for future versions.

## 7. Required Technology Stack

### 7.1 Static Site

Use:

* Astro
* TypeScript
* Markdown rendering
* static output mode

Astro is required because the project is content-heavy, static-first, and suited to GitHub Pages deployment.

### 7.2 Harvesting and Validation

Use:

* Python 3.11+
* PyYAML
* python-frontmatter or equivalent frontmatter parser
* python-slugify or equivalent slug logic
* pathlib
* subprocess for Git clone operations

### 7.3 Search

Use:

* Pagefind

Search must work on the generated static site without a backend service.

### 7.4 Automation

Use:

* GitHub Actions

### 7.5 Hosting

Use:

* GitHub Pages deployed from a GitHub Actions artifact

## 8. Repository Layout Requirements

The repository must use this layout:

* `README.md`
* `package.json`
* `requirements.txt`
* `astro.config.mjs`
* `tsconfig.json`
* `.gitignore`
* `data/repos.yml`
* `scripts/harvest_lessons.py`
* `scripts/validate_lessons.py`
* `scripts/build_exports.py`
* `src/content/generated/`
* `src/layouts/`
* `src/components/`
* `src/pages/`
* `public/exports/`
* `docs/`
* `tmp/.gitkeep`
* `.github/workflows/build-deploy.yml`

Required documentation files:

* `docs/lesson-template.md`
* `docs/lesson-schema.md`
* `docs/adding-a-repo.md`
* `docs/architecture.md`

Generated content directories must exist but generated data files should not be manually edited.

## 9. Source Repository Contract

Each participating source repository must store lessons in:

`docs/lessons/*.md`

Each lesson file must be a standalone markdown document.

Recommended file naming format:

`kebab-case-lesson-name.md`

Example:

`schema-drift-validation.md`

Each lesson may contain YAML frontmatter. Missing optional frontmatter should create warnings, not errors.

A valid minimal lesson must include either:

* a frontmatter `title`, or
* a first markdown H1, or
* a filename that can be converted into a title

The lesson body must not be empty.

## 10. Hub Repository Configuration

The hub must use:

`data/repos.yml`

The file must contain a top-level `repos` list.

Each repo entry must support:

| Field          | Required | Description                            |
| -------------- | -------: | -------------------------------------- |
| `id`           |      yes | Stable lowercase kebab-case identifier |
| `name`         |      yes | Display name                           |
| `owner`        |      yes | GitHub owner or organization           |
| `repo`         |      yes | GitHub repository name                 |
| `branch`       |      yes | Branch to harvest from                 |
| `lessons_path` |      yes | Relative path to lesson folder         |
| `project_url`  |       no | Public project URL                     |
| `enabled`      |       no | Defaults to true                       |

Adding a new source repository must require only one normal edit:

`data/repos.yml`

## 11. Lesson Frontmatter Requirements

Supported frontmatter fields:

| Field             | Requirement                         |
| ----------------- | ----------------------------------- |
| `title`           | Required after normalization        |
| `summary`         | Recommended                         |
| `date`            | Recommended                         |
| `updated`         | Optional                            |
| `repo`            | Optional; inferred from repo config |
| `project`         | Optional; inferred from repo config |
| `phase`           | Recommended                         |
| `lesson_type`     | Recommended                         |
| `status`          | Optional; defaults to active        |
| `tags`            | Recommended                         |
| `source_files`    | Optional                            |
| `related_prs`     | Optional                            |
| `related_issues`  | Optional                            |
| `related_commits` | Optional                            |
| `audience`        | Optional                            |
| `slug`            | Optional                            |

Allowed `lesson_type` values:

* `architecture`
* `implementation`
* `testing`
* `deployment`
* `debugging`
* `data-design`
* `ai-assisted-development`
* `documentation`
* `maintenance`
* `process`
* `other`

Allowed `status` values:

* `active`
* `superseded`
* `draft`
* `deprecated`

Unknown controlled values must produce validation warnings.

## 12. Normalized Lesson Object Requirements

The harvester must create normalized lesson records containing:

| Field             | Requirement                               |
| ----------------- | ----------------------------------------- |
| `id`              | Required, globally unique                 |
| `title`           | Required                                  |
| `summary`         | Required with warning if inferred/missing |
| `repo_id`         | Required                                  |
| `repo_name`       | Required                                  |
| `repo_owner`      | Required                                  |
| `repo_slug`       | Required                                  |
| `source_path`     | Required                                  |
| `source_url`      | Required                                  |
| `project_url`     | Required or generated                     |
| `date`            | Optional with warning if missing          |
| `updated`         | Optional                                  |
| `phase`           | Optional with warning if missing          |
| `lesson_type`     | Optional with warning if missing          |
| `status`          | Required; default active                  |
| `tags`            | Optional with warning if missing          |
| `source_files`    | Optional list                             |
| `related_prs`     | Optional list                             |
| `related_issues`  | Optional list                             |
| `related_commits` | Optional list                             |
| `audience`        | Optional list                             |
| `content`         | Required                                  |
| `word_count`      | Required                                  |
| `reading_minutes` | Required                                  |

Generated JSON output must be valid and deterministic.

## 13. ID Generation Requirements

Lesson IDs must be globally unique.

Preferred format:

`{repo_id}-{lesson_slug}`

Slug source priority:

1. Explicit `slug` frontmatter
2. Markdown filename without extension
3. Normalized title

Slug rules:

* lowercase
* kebab-case
* no spaces
* no unsafe URL characters
* prefix with repo ID

Duplicate IDs must fail validation.

## 14. Tag Normalization Requirements

Tags must be normalized during harvesting.

Rules:

* lowercase
* trim whitespace
* replace spaces with hyphens
* remove duplicate tags
* preserve normalized values for Version 1 display

Examples:

| Input            | Normalized       |
| ---------------- | ---------------- |
| `GitHub Actions` | `github-actions` |
| `Schema Design`  | `schema-design`  |
| `validation`     | `validation`     |

## 15. Harvesting Requirements

The harvester script must be:

`scripts/harvest_lessons.py`

It must:

1. Load `data/repos.yml`
2. Validate repo registry structure
3. Create a clean temporary harvest directory
4. Clone each enabled source repo
5. Locate the configured lessons folder
6. Scan `*.md` files
7. Parse YAML frontmatter
8. Parse markdown body
9. Infer missing safe defaults
10. Generate normalized lesson records
11. Generate source URLs
12. Generate aggregate indexes
13. Generate AI export files
14. Print a clear harvest summary

The harvester must output:

* `src/content/generated/lessons.json`
* `src/content/generated/repos.json`
* `src/content/generated/tags.json`
* `src/content/generated/phases.json`
* `src/content/generated/lesson_types.json`
* `public/exports/lessons-pack.json`
* `public/exports/lessons-pack.md`
* `public/exports/lessons-index.json`

The harvester must continue through warnings but fail on hard errors.

## 16. Repository Fetching Requirements

Version 1 must use:

`git clone --depth 1`

Clone destination:

`tmp/repos/{repo_id}`

Public clone URL format:

`https://github.com/{owner}/{repo}.git`

Private-token support must use:

`LESSONS_REPO_TOKEN`

If a token is present, the harvester may use authenticated clone URLs.

Token values must never be:

* printed
* logged
* stored in generated files
* exposed in errors
* exposed in static output

## 17. Validation Requirements

The validator script must be:

`scripts/validate_lessons.py`

It must run after harvesting and before site build.

Validation output must distinguish:

* `ERROR`
* `WARNING`
* `INFO`

The build must fail on errors.

The build must not fail on warnings.

### 17.1 Hard Errors

Validation must fail for:

* missing `data/repos.yml`
* invalid YAML in `data/repos.yml`
* duplicate repo IDs
* invalid repo ID format
* missing required repo config fields
* enabled repo cannot be cloned
* configured lessons path missing
* unreadable markdown lesson file
* empty lesson content
* duplicate lesson ID
* generated JSON invalid
* required generated files missing
* output write failure

### 17.2 Warnings

Validation must warn for:

* missing summary
* missing tags
* missing date
* missing phase
* missing lesson type
* unknown lesson type
* non-normalized tag casing
* broken local source file references
* relative links in markdown body
* very short lesson content
* title inferred from filename

## 18. Static Site Page Requirements

### 18.1 Home Page

Path:

`src/pages/index.astro`

Must show:

* site title
* purpose statement
* repo count
* lesson count
* tag count
* recent lessons
* featured lesson list
* links to lessons, repos, tags, phases, and types

### 18.2 All Lessons Page

Path:

`src/pages/lessons/index.astro`

Must show:

* all lessons
* title
* summary
* repo
* date
* tags
* lesson type
* status

Must support client-side filtering by:

* repo
* tag
* phase
* lesson type
* status

Must include Pagefind search.

### 18.3 Lesson Detail Page

Path:

`src/pages/lessons/[id].astro`

Must show:

* lesson title
* summary
* metadata panel
* source repo link
* original markdown link
* tags
* lesson body
* related PRs, issues, and commits if present
* related lessons by tag
* back links to repo and lesson index pages

### 18.4 Repos Index Page

Path:

`src/pages/repos/index.astro`

Must show:

* participating repos
* lesson count per repo
* most recent lesson date
* top tags per repo
* project links

### 18.5 Repo Detail Page

Path:

`src/pages/repos/[repo].astro`

Must show:

* repo name
* project URL
* lesson count
* lessons from the repo
* tags used by the repo
* phases represented by the repo

### 18.6 Tags Pages

Paths:

* `src/pages/tags/index.astro`
* `src/pages/tags/[tag].astro`

Must show:

* tag list
* lesson count per tag
* lessons for selected tag
* related tags
* repos using selected tag

### 18.7 Phase and Type Pages

Paths:

* `src/pages/phases/index.astro`
* `src/pages/phases/[phase].astro`
* `src/pages/types/index.astro`
* `src/pages/types/[type].astro`

Must show lessons grouped by phase and lesson type.

## 19. Component Requirements

Required components:

* `LessonCard.astro`
* `LessonList.astro`
* `RepoCard.astro`
* `TagList.astro`
* `SearchBox.astro`
* `MetadataPanel.astro`

### 19.1 LessonCard

Must display:

* title
* summary
* repo name
* date
* tags
* lesson type
* status badge

### 19.2 LessonList

Must display a sorted list of `LessonCard` components.

### 19.3 RepoCard

Must display:

* repo name
* lesson count
* project link
* recent lesson date
* top tags

### 19.4 TagList

Must display linked tag badges.

### 19.5 SearchBox

Must provide Pagefind search UI.

### 19.6 MetadataPanel

Must display:

* repo
* date
* updated date
* phase
* type
* status
* source markdown link
* project link

## 20. Sorting Requirements

Default lesson sort:

1. date descending
2. updated descending
3. repo name ascending
4. title ascending

Lessons without dates sort after dated lessons.

Tag sort:

1. count descending
2. name ascending

Repo sort:

1. name ascending

Recent lessons sort:

1. date descending
2. updated descending
3. title ascending

## 21. Markdown Rendering Requirements

Lesson body markdown must support:

* headings
* paragraphs
* ordered lists
* unordered lists
* tables
* links
* inline code
* fenced code
* blockquotes

Version 1 must keep relative source links unchanged.

Version 1 must warn when relative links are detected.

Version 2 may rewrite relative links to GitHub blob URLs.

## 22. Export Pack Requirements

The project must generate AI-readable export files under:

`public/exports/`

Required files:

* `lessons-pack.json`
* `lessons-index.json`
* `lessons-pack.md`

### 22.1 lessons-pack.json

Must contain full normalized lesson objects.

### 22.2 lessons-index.json

Must contain compact records for fast agent lookup.

Required fields:

* `id`
* `title`
* `repo`
* `summary`
* `tags`
* `url`

### 22.3 lessons-pack.md

Must contain all lessons in one markdown document.

Required structure:

* generated timestamp
* lessons grouped by repo
* lesson title
* source URL
* tags
* full lesson content

The file must be suitable for Claude Code, ChatGPT, or other coding agents.

## 23. GitHub Actions Requirements

Workflow file:

`.github/workflows/build-deploy.yml`

The workflow must:

1. Trigger on push to `main`
2. Trigger manually
3. Trigger daily on schedule
4. Checkout the hub repo
5. Setup Python
6. Setup Node
7. Install Python dependencies
8. Install Node dependencies
9. Run harvester
10. Run validator
11. Build Astro site
12. Run Pagefind indexing
13. Upload Pages artifact
14. Deploy to GitHub Pages

Optional secret:

`LESSONS_REPO_TOKEN`

The workflow must work without this token for public repositories.

## 24. Package Script Requirements

`package.json` must expose scripts for:

* harvest
* lesson validation
* Astro build
* Pagefind indexing
* full build
* dev server

Required script names:

* `harvest`
* `validate:lessons`
* `build`
* `index`
* `build:full`
* `dev`

## 25. Generated Files Policy

The following should not be committed:

* `dist/`
* `tmp/`
* `.astro/`
* `node_modules/`
* `src/content/generated/*.json`
* `public/exports/*.json`
* `public/exports/*.md`

Generated files may exist locally for debugging.

The GitHub Actions workflow must regenerate all required generated files before deployment.

## 26. Local Development Requirements

A developer must be able to run the project locally using this sequence:

1. Install Node dependencies
2. Install Python dependencies
3. Edit `data/repos.yml`
4. Run harvest
5. Run validation
6. Run the dev server
7. Review the generated site
8. Run full build
9. Commit source changes

The README must document these steps clearly.

## 27. Security Requirements

The implementation must:

* never expose private tokens
* never print authenticated clone URLs
* never write token values to generated files
* never include private repo URLs unless intentionally configured
* assume Version 1 source repos are public
* allow future support for private repo visibility controls

Possible future repo config fields:

* `visibility`
* `publish_source_links`
* `publish_lessons`

## 28. Accessibility Requirements

The site must provide:

* readable typography
* mobile-friendly layout
* keyboard-accessible links
* labeled search input
* clear metadata labels
* visible tag links
* visible source links
* sufficient spacing for long-form reading
* no essential information hidden behind hover-only UI

## 29. Styling Requirements

The visual design must be simple, documentation-oriented, and low-noise.

Priorities:

* readability
* dense technical content
* clear hierarchy
* source attribution
* fast scanning
* clean lesson cards
* clear metadata panels
* simple tag badges
* practical navigation

Avoid:

* heavy animations
* complex dashboards
* visual clutter
* unnecessary framework complexity

## 30. Testing Requirements

### 30.1 Python Tests

Recommended test files:

* `tests/test_repo_config.py`
* `tests/test_lesson_parsing.py`
* `tests/test_slug_generation.py`
* `tests/test_validation.py`

Required test cases:

* valid repo config
* duplicate repo ID
* missing required repo field
* valid lesson frontmatter
* missing title inferred from H1
* missing title inferred from filename
* duplicate lesson ID
* tag normalization
* source URL generation

### 30.2 Site Build Tests

At minimum, the full build must verify:

* harvest completes
* validation completes
* Astro build completes
* Pagefind index completes
* generated routes exist
* required generated JSON exists
* no missing generated data causes page failure

## 31. Phase Plan

## Phase 1: Project Skeleton

Create:

* Astro project
* base repo layout
* placeholder pages
* sample generated JSON
* base layout
* basic styling
* README stub

Acceptance criteria:

* `npm run dev` works
* homepage renders
* placeholder lessons page renders
* project builds

## Phase 2: Repo Registry and Harvester

Create:

* `data/repos.yml`
* `scripts/harvest_lessons.py`
* repo cloning
* markdown scanning
* frontmatter parsing
* normalized lesson records
* generated JSON files

Acceptance criteria:

* harvester scans at least three configured repos
* lessons are found
* `lessons.json` is generated
* source URLs are correct
* missing optional metadata creates warnings

## Phase 3: Validation

Create:

* `scripts/validate_lessons.py`
* duplicate ID detection
* repo config validation
* lesson object validation
* warning/error output

Acceptance criteria:

* validation passes for valid lessons
* validation fails for duplicate IDs
* validation warns on missing summary/date/tags
* build pipeline stops on errors

## Phase 4: Static Pages

Create:

* homepage
* all lessons page
* lesson detail pages
* repo index
* repo detail pages
* tag pages
* phase pages
* type pages

Acceptance criteria:

* each lesson has a generated detail page
* all source repo links work
* all tag pages render
* all repo pages render
* lesson counts are correct

## Phase 5: Search

Add:

* Pagefind
* search box
* search index generation after Astro build

Acceptance criteria:

* search works on deployed static site
* lesson titles are searchable
* lesson body text is searchable
* no backend is required

## Phase 6: Export Packs

Create:

* `lessons-pack.json`
* `lessons-index.json`
* `lessons-pack.md`

Acceptance criteria:

* export files are generated
* export files are copied to public output
* exported markdown contains all lessons
* exported JSON validates

## Phase 7: GitHub Pages Deployment

Create:

* `.github/workflows/build-deploy.yml`

Acceptance criteria:

* workflow runs on push
* workflow runs manually
* workflow runs on schedule
* site deploys to GitHub Pages
* public URL serves generated site
* source repo updates are included after scheduled run

## Phase 8: Documentation

Create:

* `docs/lesson-template.md`
* `docs/lesson-schema.md`
* `docs/adding-a-repo.md`
* `docs/architecture.md`

Acceptance criteria:

* README explains project purpose
* README explains local development
* README explains deployment
* docs explain how to add a repo
* docs explain how to write a lesson
* docs explain generated export files
* docs explain architecture and data flow

## 32. Complete Version 1 Acceptance Criteria

Version 1 is complete when:

1. A `lessons-hub` repo exists.
2. `data/repos.yml` defines multiple source repos.
3. At least three repos are harvested.
4. Lessons are discovered from `docs/lessons/*.md`.
5. Markdown frontmatter is parsed.
6. Missing optional metadata produces warnings.
7. Invalid required structure fails validation.
8. Normalized JSON files are generated.
9. Static Astro pages render successfully.
10. Homepage renders repo, lesson, tag, and recent lesson summaries.
11. All lessons page renders all harvested lessons.
12. Individual lesson pages render lesson content and metadata.
13. Repo pages render repo-specific lesson lists.
14. Tag pages render tag-specific lesson lists.
15. Phase/type pages render grouped lesson lists.
16. Pagefind search works.
17. Export files are generated.
18. GitHub Actions builds the site.
19. GitHub Actions deploys to GitHub Pages.
20. Adding a repo requires only editing `data/repos.yml`.
21. README documents local development, adding repos, and deployment.
22. Documentation files exist and are useful to a future maintainer.
23. The deployed site is usable as a public portfolio artifact.

## 33. Demonstration Requirements

The public project must demonstrate:

* static site generation
* build-time data pipeline design
* repository harvesting
* schema normalization
* validation discipline
* deterministic generated outputs
* GitHub Actions automation
* GitHub Pages deployment
* AI-readable export generation
* technical documentation
* repeatable lessons-learned process

The project should be presented as an educational demonstration project, not merely a utility script.

## 34. Lessons-Learned Process Requirements

The project itself must use the same lesson process it is designed to publish.

At minimum, create lessons after:

* Phase 2 harvester completion
* Phase 3 validation completion
* Phase 5 search completion
* Phase 7 deployment completion
* Version 1 completion

Each project lesson must be stored in:

`docs/lessons/*.md`

These local lessons should be harvestable by Lessons Hub itself.

## 35. Suggested First Commit Sequence

1. Initialize Astro project and base layout.
2. Add repo registry and sample lesson data.
3. Implement lesson harvester.
4. Implement validation script.
5. Render lessons, repos, and tags.
6. Add Pagefind search.
7. Generate AI export packs.
8. Add GitHub Actions Pages deployment.
9. Add documentation and lesson template.
10. Add first internal project lessons.

## 36. README Requirements

The README must include:

* project purpose
* architecture summary
* source repo contract
* how to add a repo
* how to write a lesson
* local development commands
* build commands
* deployment notes
* generated export files
* troubleshooting
* Version 1 scope
* known non-goals
* future enhancement ideas

## 37. Future Enhancement Backlog

Potential future versions may add:

* cloud-hosted API
* cloud-provider comparison builds
* GitHub API integration
* private repo publication controls
* commit/PR/issue mining
* lesson quality scoring
* graph visualization
* embeddings
* vector search
* AI-generated lesson drafts
* repo health dashboards
* documentation linting
* cross-repo architectural pattern detection
* MCP server for AI coding agents
* CLI for querying lessons locally

## 38. Coding Agent Handoff

Build the Lessons Hub project described in this PDR.

Implement a static Astro website that consolidates markdown lessons from multiple GitHub repositories. Each source repo contains lessons in `docs/lessons/*.md`. The hub repo contains `data/repos.yml`, Python harvest and validation scripts, generated JSON data, Astro pages, Pagefind search, AI export files, and GitHub Actions deployment to GitHub Pages.

Prioritize a working Version 1.

Do not add backend services, authentication UI, databases, AI generation, graph views, or embeddings.

The completed implementation must allow a new repo to be added by editing only:

`data/repos.yml`

Implement in phases:

1. Astro skeleton
2. Repo registry
3. Python harvester
4. Validation
5. Static pages
6. Search
7. Export packs
8. GitHub Pages deployment
9. Documentation
10. Internal project lessons

Use clear file names, simple code, deterministic outputs, and the acceptance criteria in this PDR.

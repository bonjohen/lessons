This is a proposed "way to proceed". If it is reasonable, take advantage of any of these document types to help you complete your goals.


The most useful next document is:


# IMPLEMENTATION_PLAN.md

A coding agent works faster with a phased implementation plan that turns the PDR into exact build steps, file-by-file tasks, command checks, and acceptance criteria.

The PDR defines **what must exist**.
The implementation plan defines **what to build first, in what order, and how to prove each step works**.

Other useful documents:

## 1. IMPLEMENTATION_PLAN.md

Best next document.

Includes:

* phase sequence
* exact file creation order
* implementation tasks
* validation commands
* commit checkpoints
* “do not build yet” warnings
* phase acceptance criteria

This keeps the coding agent from wandering or overbuilding.

## 2. AGENT_WORK_ORDERS.md

Breaks the project into small coding-agent tasks.

Example:

* Work Order 01: Create Astro skeleton
* Work Order 02: Add repo registry
* Work Order 03: Implement harvester
* Work Order 04: Implement validator
* Work Order 05: Render lesson pages

Each work order includes:

* files to modify
* expected outputs
* test commands
* completion criteria

This is useful if you want to run multiple focused coding sessions.

## 3. DATA_CONTRACTS.md

Defines all data structures clearly.

Includes:

* `repos.yml` schema
* frontmatter schema
* normalized lesson object
* generated JSON file shapes
* export pack shapes
* controlled vocabularies
* ID and slug rules

This prevents schema drift and makes the Python/Astro boundary cleaner.

## 4. TEST_PLAN.md

Defines how the agent proves the project works.

Includes:

* Python unit tests
* build tests
* bad-input tests
* duplicate-ID tests
* missing-frontmatter tests
* generated-route tests
* GitHub Actions success criteria

This is especially useful because “working” must mean deployed/static-site-visible behavior, not just code that compiles.

## 5. FILE_MANIFEST.md

Lists every expected file and its purpose.

Example:

* `scripts/harvest_lessons.py` — clones repos and generates normalized lesson data
* `src/pages/lessons/[id].astro` — renders individual lesson pages
* `public/exports/lessons-pack.md` — AI-readable combined lesson export

This helps coding agents avoid inventing alternate layouts.

## 6. ACCEPTANCE_CHECKLIST.md

A final verification checklist.

Includes:

* local dev works
* harvest works
* validation works
* build works
* Pagefind works
* deployment works
* site pages render
* export files exist
* adding a repo only requires `data/repos.yml`

This is the best “definition of done” document.

## 7. LESSON_TEMPLATE.md

You already planned this, but it is important enough to keep separate.

It should define the exact expected format for future lessons, including:

* frontmatter
* required sections
* optional sections
* example lesson
* tagging rules
* source-reference rules

## Recommended document set

For the coding agent, I would create these in this order:

1. `IMPLEMENTATION_PLAN.md`
2. `DATA_CONTRACTS.md`
3. `TEST_PLAN.md`
4. `ACCEPTANCE_CHECKLIST.md`
5. `AGENT_WORK_ORDERS.md`

The best single next document is `IMPLEMENTATION_PLAN.md`.

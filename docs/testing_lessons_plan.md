# Testing Lessons — Implementation Plan

**Source:** Gap analysis (gap_098f6bcd4621, gap_5494af1f14a8, gap_610159493e80, gap_8478286aeb40) — corpus has zero coverage on "testing" as a topic.

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

## Phase 1: Acceptance Testing with Playwright

**Goal:** A lesson exists at `docs/lessons/acceptance-testing-with-playwright.md` covering BFS link crawling, smoke tests, and targeting live/preview URLs.
**Depends on:** Nothing (first phase).

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 1.1     | Completed | 2026-05-10 09:04 PM (PST) | 2026-05-10 09:06 PM (PST) | Write `docs/lessons/acceptance-testing-with-playwright.md` — cover BFS crawl algorithm, smoke test patterns, env-var URL targeting, CI integration |
| 1.2     | Completed | 2026-05-10 09:06 PM (PST) | 2026-05-10 09:06 PM (PST) | Verify frontmatter matches template (title, summary, date, phase, lesson_type, status, tags) |

### Phase 1 Summary

- **Changes:** Created `docs/lessons/acceptance-testing-with-playwright.md` covering BFS link crawling, smoke tests, env-var URL targeting, CI integration, and the 105-broken-links discovery story.
- **Commit:** `docs: add acceptance testing with Playwright lesson`

---

## Phase 2: Test Pyramid for Static Sites

**Goal:** A lesson exists explaining the unit/integration/acceptance test layers and what each catches in a static site + backend architecture.
**Depends on:** Phase 1.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 2.1     | Open   |               |                  | Write `docs/lessons/test-pyramid-for-static-sites.md` — pytest unit layer (76 project + 138 backend tests), live integration (Ollama/ChromaDB), Playwright acceptance layer |
| 2.2     | Open   |               |                  | Verify frontmatter and cross-reference related lessons |

### Phase 2 Summary

- **Changes:** TBD
- **Commit:** `docs: add test pyramid for static sites lesson`

---

## Phase 3: Mock vs Live Testing Trade-offs

**Goal:** A decision-framework lesson covering when to mock vs when to test against real infrastructure.
**Depends on:** Phase 2.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 3.1     | Open   |               |                  | Write `docs/lessons/mock-vs-live-testing-trade-offs.md` — when mocks mask bugs (migration case), when live is impractical (cloud SDKs), hybrid patterns (sys.modules.setdefault) |
| 3.2     | Open   |               |                  | Verify frontmatter and cross-reference related lessons |

### Phase 3 Summary

- **Changes:** TBD
- **Commit:** `docs: add mock vs live testing trade-offs lesson`

---

## Phase 4: Preflight Gates as Local CI

**Goal:** A lesson covering the pattern of running the same checks CI will run before pushing, preventing the most common CI failure patterns.
**Depends on:** Phase 3.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 4.1     | Open   |               |                  | Write `docs/lessons/preflight-gates-as-local-ci.md` — lint/format/test gates, script existence checks, optional dep detection, single-command pre-push validation |
| 4.2     | Open   |               |                  | Verify frontmatter and cross-reference related lessons |

### Phase 4 Summary

- **Changes:** TBD
- **Commit:** `docs: add preflight gates as local CI lesson`

---

## Phase 5: Testing Cross-Repo Content Pipelines

**Goal:** A lesson covering validation strategies for harvested data spanning multiple repos — slug uniqueness, link resolution, schema enforcement, severity levels.
**Depends on:** Phase 4.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 5.1     | Open   |               |                  | Write `docs/lessons/testing-cross-repo-content-pipelines.md` — validation severity (ERROR vs WARN), slug collision detection, frontmatter schema checks, cross-repo link resolution |
| 5.2     | Open   |               |                  | Verify frontmatter and cross-reference related lessons |

### Phase 5 Summary

- **Changes:** TBD
- **Commit:** `docs: add testing cross-repo content pipelines lesson`

---

## Phase 6: Close Gaps and Commit

**Goal:** All 5 lessons committed, gap records updated to resolved.
**Depends on:** Phase 5.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 6.1     | Open   |               |                  | Run `npm run harvest` to pick up new lessons, verify they appear in generated JSON |
| 6.2     | Open   |               |                  | Update gap files (gap_098f, gap_5494a, gap_84782, gap_61015) status to `resolved` |
| 6.3     | Open   |               |                  | Run `npm run build` to verify site builds cleanly with new lessons |
| 6.4     | Open   |               |                  | Stage and commit all changes |

### Phase 6 Summary

- **Changes:** TBD
- **Commit:** `docs: close testing gaps, update gap status to resolved`

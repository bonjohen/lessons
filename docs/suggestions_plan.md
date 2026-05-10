# Suggestions 2025-05-09 — Implementation Plan

**Source document:** `docs/suggestions20250509.md`
**Prior work:** `docs/v2_hardening_plan.md` (9 phases, all complete)
**Project root:** `C:\Projects\lessons`
**Date:** 2026-05-09

## Scope

This plan addresses the remaining issues from `docs/suggestions20250509.md` that were **not** resolved by the V2 hardening plan. Three of the original nine issues are already fixed:

| Suggestion | Status | Resolution |
|---|---|---|
| 1. API route prefixes | Done | Hardening Phase 9 — routers use local paths, `main.py` mounts at `/api` and `/api/v1` |
| 2. Hardwired adapters | Done | Hardening Phase 2 — `_create_adapters()` factory dispatches on `DEPLOYMENT_PROFILE` |
| 7. Frontend chat not implemented | Done | `ChatPanel.astro` has working chat UI with message display, scores, health check |
| 9. Trust boundary weak | Done | `generator.py` builds `relevant_lessons` deterministically from retriever results, not from LLM output |

Five issues remain and are addressed below.

## Work Queue Instructions

### State Transitions

Open  -->  Started  -->  Completed
              |
              └-->  Blocked  -->  Started  -->  Completed

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
| No new dependencies | All work uses existing stack |

---

## Phase 1: Schema Ordering & RAG Metadata Enrichment (Issues 3, 8)

**Goal:** Pydantic models defined in dependency order. RAG chunks include `lesson_type`, `phase`, and `status` metadata so filters actually work.
**Depends on:** Nothing (first phase).
**Exit condition:** `ChatFilters.lesson_type` filter returns correct results; `ChunkResult` defined before `RetrieveResponse`; `ChatFilters` defined before `ChatRequest`; all tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 1.1 | Completed | 2026-05-10 02:41 AM (PST) | 2026-05-10 02:42 AM (PST) | In `backend/app/models/schemas.py`: reorder Chat section — move `ChatFilters` before `ChatRequest`, move `ChunkResult` before `RetrieveResponse`. No field changes, just declaration order. |
| 1.2 | Completed | 2026-05-10 02:42 AM (PST) | 2026-05-10 02:42 AM (PST) | In `scripts/build_rag_corpus.py`: extract `lesson_type`, `phase`, and `status` from lesson data during chunk construction. Add these three fields to each chunk record dict. |
| 1.3 | Completed | 2026-05-10 02:42 AM (PST) | 2026-05-10 02:43 AM (PST) | In `backend/app/models/schemas.py`: add `lesson_type: str = ""`, `phase: str = ""`, `status: str = ""` fields to `ChunkRecord`. Add `lesson_type: str = ""` to `ChunkResult`. |
| 1.4 | Completed | 2026-05-10 02:43 AM (PST) | 2026-05-10 02:43 AM (PST) | In `backend/app/adapters/vector/chromadb_adapter.py`: include `lesson_type`, `phase`, `status` in the metadata dict at index time (lines ~32-43). Update the `lesson_type` filter logic (line ~67) — it should now work correctly. |
| 1.5 | Completed | 2026-05-10 02:43 AM (PST) | 2026-05-10 02:44 AM (PST) | Add test in `backend/tests/test_schemas.py`: instantiate `ChatRequest` with `ChatFilters`, `RetrieveResponse` with `ChunkResult` — confirm no forward-reference errors at model validation time. |
| 1.6 | Completed | 2026-05-10 02:43 AM (PST) | 2026-05-10 02:44 AM (PST) | Add test in `backend/tests/test_corpus_metadata.py`: build a chunk from a lesson that has `lesson_type: "deployment"`, verify the chunk record includes the field. Mock ChromaDB upsert call, verify metadata dict contains `lesson_type`. |
| 1.7 | Completed | 2026-05-10 02:44 AM (PST) | 2026-05-10 02:46 AM (PST) | Verify: `python -m pytest backend/tests/` green. `python -m pytest tests/` green. `ruff check backend/` clean. |
| 1.8 | Completed | 2026-05-10 02:46 AM (PST) | 2026-05-10 02:47 AM (PST) | Stage and commit all Phase 1 changes. |

### Phase 1 Summary

- **Changes:** Reordered Pydantic models in `schemas.py` (ChatFilters before ChatRequest, ChunkResult before RetrieveResponse). Added `lesson_type`, `phase`, `status` fields to `ChunkRecord` and `lesson_type` to `ChunkResult`. Updated `build_rag_corpus.py` to extract these fields from lesson data. Updated `chromadb_adapter.py` to index and return `lesson_type`/`phase`/`status` metadata. Added `test_schemas.py` (6 tests) and `test_corpus_metadata.py` (3 tests).
- **Changes hosted at:** TBD
- **Commit:** `fix: schema ordering and lesson_type/phase/status in RAG metadata (S-03, S-08)`

---

## Phase 2: Runtime vs. Review Artifact Split (Issue 4)

**Goal:** Gap records, TODO records, and candidate repo data are split into gitignored runtime state and committed review artifacts so reviewers can see gaps and TODOs in PRs.
**Depends on:** Phase 1.
**Exit condition:** `docs/review/gaps/`, `docs/review/todos/` exist and are committed. Runtime scratch stays in `data/` (gitignored). Gap store writes to both locations. Tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 2.1 | Completed | 2026-05-10 02:46 AM (PST) | 2026-05-10 02:47 AM (PST) | Create directory structure: `docs/review/gaps/`, `docs/review/todos/`, `docs/review/candidate-repos/`. Add `.gitkeep` files. |
| 2.2 | Completed | 2026-05-10 02:47 AM (PST) | 2026-05-10 02:49 AM (PST) | In `backend/app/rag/gap_store.py`: add a `_review_path` alongside `_path`. On `create_or_update()` and `update_status()`, write a human-readable markdown summary to `docs/review/gaps/{gap_id}.md` in addition to the JSON runtime file. |
| 2.3 | Completed | 2026-05-10 02:49 AM (PST) | 2026-05-10 02:50 AM (PST) | In `backend/app/discovery/todo_writer.py`: add parallel write to `docs/review/todos/{todo_id}.md` with frontmatter (title, status, priority, source_project_url, candidate_lesson_path) and body text. |
| 2.4 | Completed | 2026-05-10 02:50 AM (PST) | 2026-05-10 02:50 AM (PST) | Update `.gitignore`: confirm `data/gaps/`, `data/todos/`, `data/external/` remain ignored. Add comment clarifying that `docs/review/` is the committed counterpart. |
| 2.5 | Completed | 2026-05-10 02:50 AM (PST) | 2026-05-10 02:51 AM (PST) | Add test: create a gap via `GapStore`, assert both `data/gaps/corpus-gaps.json` and `docs/review/gaps/{gap_id}.md` exist with correct content. |
| 2.6 | Completed | 2026-05-10 02:51 AM (PST) | 2026-05-10 02:51 AM (PST) | Verify: `python -m pytest backend/tests/` green. `ruff check backend/` clean. |
| 2.7 | Started | 2026-05-10 02:51 AM (PST) | | Stage and commit all Phase 2 changes. |

### Phase 2 Summary

- **Changes:** Created `docs/review/gaps/`, `docs/review/todos/`, `docs/review/candidate-repos/` with `.gitkeep`. Updated `gap_store.py` with `_write_review_md()` that writes human-readable markdown to `docs/review/gaps/{gap_id}.md` on create/update. Updated `todo_writer.py` with `_write_review_md()` that writes to `docs/review/todos/{todo_id}.md`. Updated `.gitignore` comment. Added `test_review_artifacts.py` (2 tests).
- **Changes hosted at:** TBD
- **Commit:** `feat: split runtime state from committed review artifacts (S-04)`

---

## Phase 3: GitHub Discovery Security Hardening (Issue 5)

**Goal:** GitHub discovery endpoints are disabled by default, validate inputs, and derive clone URLs internally. Safe for cloud deployment.
**Depends on:** Phase 2.
**Exit condition:** `GITHUB_DISCOVERY_ENABLED=false` by default; harvest endpoint rejects arbitrary clone URLs; owner/repo validated against `^[a-zA-Z0-9._-]+$`; tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 3.1 | Open | | | In `backend/app/api/github_discovery.py`: add `GITHUB_DISCOVERY_ENABLED` env var check (default `"false"`). Return 403 with clear message if disabled. Apply to both search and harvest endpoints. |
| 3.2 | Open | | | In `backend/app/api/github_discovery.py`: add `_validate_owner_repo(owner, repo_name)` that checks both against `^[a-zA-Z0-9._-]+$`. Return 422 on invalid input. |
| 3.3 | Open | | | In `backend/app/api/github_discovery.py`: remove `clone_url` from the harvest endpoint request body. Derive it internally as `https://github.com/{owner}/{repo_name}.git`. Remove `github_url` acceptance — construct it from `owner`/`repo_name`. |
| 3.4 | Open | | | In `backend/app/discovery/repo_intake.py`: add an allowlist check — `clone_url` must start with `https://github.com/`. Reject anything else. |
| 3.5 | Open | | | Add tests: disabled returns 403; invalid owner returns 422; clone_url derived correctly; non-github URL rejected by repo_intake. |
| 3.6 | Open | | | Update existing discovery tests to set `GITHUB_DISCOVERY_ENABLED=true` in test environment. |
| 3.7 | Open | | | Verify: `python -m pytest backend/tests/` green. `ruff check backend/` clean. |
| 3.8 | Open | | | Stage and commit all Phase 3 changes. |

### Phase 3 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `fix(security): gate and validate GitHub discovery endpoints (S-05)`

---

## Phase 4: Candidate Lesson Pipeline Improvement (Issue 6)

**Goal:** Candidate lesson generation produces a structured draft with evidence links and a review checklist, not just a file listing.
**Depends on:** Phase 3 (discovery security changes affect the same code area).
**Exit condition:** Generated candidate lessons have Summary, Evidence From Project (with file links), Lesson Draft, and Review Checklist sections. Attribution and coordination sections preserved. Tests pass.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 4.1 | Open | | | In `backend/app/discovery/lesson_extractor.py`: refactor `_generate_lesson_content()` into a multi-stage pipeline: `_summarize_sources()` → `_draft_lesson()` → `_build_evidence_links()` → `_build_review_checklist()`. |
| 4.2 | Open | | | `_summarize_sources()`: for each detected evidence file (README, CI configs, deploy scripts, docs), extract a 1–3 sentence summary of what the file demonstrates. Return a list of `(file_path, summary)` tuples. |
| 4.3 | Open | | | `_draft_lesson()`: combine source summaries into a cohesive lesson body paragraph. Use the gap's `normalized_topic` and `missing_concepts` to frame the lesson around what was missing from the corpus. |
| 4.4 | Open | | | `_build_evidence_links()`: generate a markdown list of source files with relative paths and one-line descriptions. Link to the GitHub blob URL (`https://github.com/{owner}/{repo}/blob/{branch}/{path}`). |
| 4.5 | Open | | | `_build_review_checklist()`: append a markdown checklist: `[ ] Lesson accurately reflects source project`, `[ ] Attribution is correct`, `[ ] No proprietary content copied`, `[ ] Ready to propose to source project owner`. |
| 4.6 | Open | | | Update candidate lesson frontmatter: set `review_status: needs_review` and add `generated_by: lesson_extractor_v2`. |
| 4.7 | Open | | | Add test: generate a candidate lesson from a mock repo with README + Dockerfile + .github/workflows/deploy.yml. Assert all four sections present. Assert evidence links point to valid GitHub blob URLs. Assert review checklist has 4 items. |
| 4.8 | Open | | | Verify: `python -m pytest backend/tests/` green. `ruff check backend/` clean. |
| 4.9 | Open | | | Stage and commit all Phase 4 changes. |

### Phase 4 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `feat: structured candidate lesson generation with evidence and review checklist (S-06)`

---

## Phase 5: Verification & Cleanup

**Goal:** Full test suite green, lint clean, end-to-end local smoke test passes.
**Depends on:** Phase 4.
**Exit condition:** All 4 prior phases committed. `python -m pytest tests/ backend/tests/` green. `ruff check backend/` clean. `npm run build` succeeds. No regressions.

| PhaseNo | Status | Started (PST) | Completed (PST) | Description |
|---------|--------|---------------|------------------|-------------|
| 5.1 | Open | | | Run full test suite: `python -m pytest tests/` (76 tests) and `python -m pytest backend/tests/` (96+ tests). Fix any failures. |
| 5.2 | Open | | | Run `ruff check backend/` and `ruff format --check backend/`. Fix any issues. |
| 5.3 | Open | | | Run `npm run build` to confirm Astro site still builds. |
| 5.4 | Open | | | Review all changes across phases 1–4 for consistency: schema fields match between corpus builder, ChromaDB adapter, and schemas.py; gap store writes to both paths; discovery tests use enabled flag. |
| 5.5 | Open | | | Stage and commit any final fixes. |

### Phase 5 Summary

- **Changes:** TBD
- **Changes hosted at:** TBD
- **Commit:** `chore: verification and cleanup for suggestions implementation (S-final)`

---

## Suggestion → Phase Cross-Reference

| Suggestion | Title | Phase | Notes |
|---|---|---|---|
| S-01 | API route prefixes | — | Already fixed (hardening Phase 9) |
| S-02 | Hardwired adapters | — | Already fixed (hardening Phase 2) |
| S-03 | Schema ordering | 1 | Reorder model definitions |
| S-04 | Runtime vs. review artifacts | 2 | Split data paths |
| S-05 | GitHub discovery security | 3 | Gate + validate + derive URLs |
| S-06 | Candidate lesson placeholder | 4 | Multi-stage generation pipeline |
| S-07 | Frontend chat | — | Already working |
| S-08 | RAG metadata too thin | 1 | Add lesson_type/phase/status to chunks |
| S-09 | Trust boundary | — | Already deterministic (generator uses retriever results) |

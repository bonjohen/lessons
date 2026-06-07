---
title: Five-Stage Design-to-Execution Workflow
summary: A repeatable workflow — Design, PDR, Plan, Execute, Commit — with table-driven task tracking and one-commit-per-phase discipline, applied across 18 project phases.
date: 2026-05-09
phase: process
lesson_type: process
status: active
tags: [workflow, planning, phased-execution, project-management, process]
---

# Five-Stage Design-to-Execution Workflow

## The Lesson

Breaking implementation into five explicit stages — explore the problem (Design), specify the build (PDR), order the work (Plan), execute with status tracking (Execute), and commit per phase — prevents the most common failure mode in multi-phase projects: starting to code before understanding what to build, then losing track of what's done and what's left.

## Context

A lessons library project went through three major implementation cycles: V1 (static site, 10 phases), V2 (RAG chatbot + multi-cloud, 8 phases), and V2 hardening (production readiness, 9 phases planned). Each cycle involved different technology (Astro/TypeScript, FastAPI/Python, CloudFormation/Bicep) but followed the same five-stage workflow. The total across all cycles was 27 phases containing over 130 individual task rows, all tracked in markdown plan files with timestamps.

## What Happened

1. **Stage 1 (Design):** Explored the problem space — read code, logs, errors, external references. Produced a design document — a structured markdown file with numbered sections covering purpose, scope, core design principles, primary user stories, and functional requirements grouped by area. No code changes. This stage caught misunderstandings before they became wrong implementations.
2. **Stage 2 (PDR):** Translated the design into physical specifications — what exists to reuse, new dependencies, package layout, data model, component specifications with file paths. The PDR is a build spec that could be handed to a different implementor.
3. **Stage 3 (Plan):** Converted the PDR into ordered phases with task tables. Each phase has a goal, dependencies, and exit condition. Each row has 5 columns: PhaseNo, Status, Started (PST), Completed (PST), Description. Numbering is `{phase}.{row}` (e.g., 3.4). Phases end with explicit "stage and commit" rows.
4. **Stage 4 (Execute):** Worked through rows sequentially. Each row flips from Open → Started (with timestamp), work is done and verified, then flips to Completed (with timestamp). The plan file is saved after every status change. When all rows in a phase complete, a Phase Summary block is written and a single commit captures the entire phase.
5. **Stage 5 (Commit):** One commit per phase, only when tests pass and lint is clean. Commit message reflects the phase scope (e.g., "feat: Phase 3 — gap detection with corpus-gap records and gaps UI"). Never commit partial phases. Never batch multiple phases into one commit.
6. V2 executed 8 phases in sequence, each producing one commit (3c1749a through f62a6c8). Every phase commit was self-contained — checking out any phase commit produces a working application with all tests passing.
7. The hardening plan followed the identical format. The plan file was the source of truth for resuming after interruptions — a new session could read the plan, find the first non-Completed row, and pick up exactly where work stopped.

## Key Insights

- **The plan file is the state machine.** Status transitions (Open → Started → Completed) with timestamps are not just tracking — they're the mechanism for resuming interrupted work. After a context switch or session break, reading the plan file tells you exactly where you are without re-analyzing the codebase.

- **One commit per phase enforces testable checkpoints.** If Phase 3 breaks something that Phase 4 needs, the break is caught at the Phase 3 commit boundary (tests must pass). Without this discipline, broken intermediate states accumulate and debugging becomes archaeological — you can't tell which change in a 500-line diff caused the failure.

- **Design documents prevent the most expensive rework.** The V2 design stage identified that the adapter pattern was needed for multi-cloud support before any code was written. Without this stage, the typical path is: build for one cloud, realize it needs to work on others, refactor everything to use adapters. The design doc costs hours; the refactor costs days.

- **PDRs catch dependency conflicts early.** The V2 PDR specified that cloud SDKs would be optional dependencies with lazy imports. This decision, made during specification, prevented the situation where boto3 is added to core requirements and breaks the local development setup. Dependency decisions made during coding tend to be expedient rather than considered.

- **Phases should be independently shippable.** Each V2 phase left the application in a working state. Phase 1 (scaffold + corpus builder) shipped a health endpoint and corpus generation. Phase 2 added chat. Phase 3 added gap detection. No phase depended on a future phase to produce a working system. This means any phase could be the last phase — useful when priorities shift.

- **Timestamps are retrospective data.** Phase 1 started at 2:25 PM and completed at 2:38 PM (13 minutes, 10 rows). Phase 6 (AWS infrastructure) took longer. The timestamps aren't for project management — they're for learning which kinds of phases take how long, informing future planning.

## Applicability

This workflow works when:
- The project is complex enough that "just start coding" leads to rework (more than ~3 files affected)
- Multiple implementation phases need to be coordinated
- Work may be interrupted and resumed by the same or different implementor
- The codebase has tests that can validate each phase independently

It does **not** apply when:
- The change is a single file fix (just make the change and commit)
- The project is exploratory with no clear end state (research, prototyping)
- The team uses a different planning system (Jira, Linear) that already tracks state — don't duplicate

## Related Lessons

- [Code Review as Requirements Source](code-review-as-requirements-source.md) — how review findings feed back into the Design stage of the next cycle
- [GitHub Pages Build Pipeline](github-pages-build-pipeline.md) — the CI/CD pipeline that validates each phase commit

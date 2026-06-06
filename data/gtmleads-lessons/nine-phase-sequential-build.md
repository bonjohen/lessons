---
title: "Nine-Phase Sequential Build"
summary: "For a full-stack application built from scratch, a strict bottom-up phase order — schema, models, data, services, pipeline, API, UI, export — with one commit per phase and a green test suite at each boundary, produces a codebase where every layer is testable in isolation and integration bugs surface..."
date: 2026-06-06
lesson_type: implementation
tags: [database, testing, api, data-modeling, pipeline]
---
# Nine-Phase Sequential Build

## The Lesson

For a full-stack application built from scratch, a strict bottom-up phase order — schema, models, data, services, pipeline, API, UI, export — with one commit per phase and a green test suite at each boundary, produces a codebase where every layer is testable in isolation and integration bugs surface at the phase boundary where they're cheapest to fix.

## Context

GTMLeads is a signal intelligence pipeline with 9 layers: database schema, Pydantic models, config/seed data, scoring/dedup services, pipeline framework + adapters, REST API routes, HTML UI, and export/backup. The entire system was built from an empty directory to 189 passing tests across 9 sequential phases, each independently committed. The project followed a 5-stage SDLC workflow (design doc → PDR → phased plan → execute → commit) with detailed plan files per phase.

## What Happened

1. **Phase 1 (scaffold):** Project structure, SQLite migration system, 9 tables + FTS5 virtual table, WAL mode + foreign keys. One health endpoint to prove the server boots. 0 → ~20 tests.
2. **Phase 2 (models + seed):** Pydantic v2 models with Create/Read variants, `sources.json`, `topic-packs.json`, idempotent seed from JSON. Tests validated model constraints and seed idempotency.
3. **Phase 3 (templates + config validation):** 265 signal templates, query templates, config validation tests ensuring cross-reference consistency. No service code yet — this was pure data.
4. **Phase 4 (services):** Scoring engine (5 components), candidate mapping (3 layers), 4-level dedup, signal CRUD. Tested against in-memory SQLite with real FK constraints.
5. **Phase 5 (pipeline):** `BaseAdapter` ABC, `ImportRunner` orchestrator, GitHub adapter (first adapter), health/status endpoints. Pipeline tests with respx mocks.
6. **Phase 6 (adapters):** Federal Register, NVD, CISA KEV, OpenAlex — 4 more adapters with per-adapter test suites.
7. **Phase 7 (API):** REST routes for signals, candidates, review, imports, topic packs, admin. Full API test suite using TestClient with on-disk SQLite.
8. **Phase 8 (UI):** Jinja2 templates, HTMX interactions, static assets, page routes. Light tests (template rendering, page status codes).
9. **Phase 9 (export + backup):** JSON export for static site, SQLite backup via `.backup()` API, final verification. 189 tests, all green.

## Key Insights

- **Bottom-up ordering eliminates forward references.** Phase 4 (services) can import Phase 2 (models) because models already exist. If the order were reversed, services would need stubs or mocks for models that don't exist yet, creating throwaway code.
- **One commit per phase creates natural rollback points.** If Phase 7 (API routes) introduced a regression, `git revert` cleanly removes it without touching Phase 6 (adapters). Batching multiple phases into one commit makes this impossible.
- **Green tests at each phase boundary are a ratchet.** The test count went 20 → 45 → 60 → 95 → 125 → 145 → 165 → 175 → 189. No phase was allowed to break tests from a prior phase. This means each phase extends the system without degrading it.
- **Data phases (2, 3) feel unproductive but pay off later.** Phases 2 and 3 produce no visible features — just models and JSON files. But they validate the data model so thoroughly that Phases 4-9 never needed schema changes. Zero migrations after the initial schema.
- **UI last is the right order for a pipeline system.** The temptation to build UI early ("show something working") would have forced premature decisions about data shape. By the time Phase 8 arrived, the API and data model were stable, and the UI was a thin layer over settled abstractions.

## Applicability

This pattern applies to greenfield full-stack applications where you control the entire stack and can build bottom-up. It works best when the data model is the primary complexity driver (data pipelines, CRMs, analytics systems, content management).

It is less useful for UI-first products where user feedback drives the data model (consumer apps, prototypes), or for systems where the layers are built by different teams on different timelines.

## Related Lessons

- [Config-First Development](config-first-development.md) — Phases 2 and 3 are the config-first principle applied at project scale
- [Base Adapter ABC Pattern](base-adapter-abc-pattern.md) — Phase 5 established the contract that Phase 6 expanded

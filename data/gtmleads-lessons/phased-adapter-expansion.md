---
title: "Phased Adapter Expansion"
summary: "When scaling a plugin architecture, ship configuration and data files first (before any code), tier new plugins by API complexity, and close with registry-level consistency tests. This ordering catches integration mismatches early and keeps each phase independently shippable."
date: 2026-05-20
lesson_type: architecture
tags: [authentication, data-modeling, pipeline]
---
# Phased Adapter Expansion

## The Lesson

When scaling a plugin architecture, ship configuration and data files first (before any code), tier new plugins by API complexity, and close with registry-level consistency tests. This ordering catches integration mismatches early and keeps each phase independently shippable.

## Context

GTMLeads is a signal intelligence pipeline that ingests data from multiple public APIs (GitHub, Federal Register, NVD, etc.) through a registry of adapter plugins. After the initial 5 adapters were stable, the project needed to add 5 more (SEC EDGAR, arXiv, HN Algolia, Semantic Scholar, Reddit). The adapters share a common base class but each has unique API conventions, rate limits, and response formats. The expansion was planned as a 4-phase effort across ~1,500 lines of new code.

## What Happened

1. **Phase 1 (config-first):** Added all 5 new sources to `sources.json`, their query templates to `query-templates.json`, and source quality scores to `scoring.py` — before writing a single adapter class. This forced early validation that the data model could represent every new source.
2. **Phase 2 (Tier 1 — well-documented APIs):** Implemented SEC EDGAR, arXiv, and HN Algolia. These had the best-documented APIs and simplest auth models, so they served as the test bed for the adapter expansion pattern.
3. **Phase 3 (Tier 2 — complex APIs):** Added Semantic Scholar and Reddit. Reddit required OAuth token handling and a more complex normalization step. By this point the patterns from Phase 2 were proven and reusable.
4. **Phase 4 (verification):** Added registry consistency tests that check every source in `sources.json` has a corresponding adapter in `ADAPTER_REGISTRY`, and vice versa. Also ran live smoke tests against real APIs and documented the results.
5. A post-expansion fix (`7b9b47e`) revealed that two Tier 1 adapters had bugs only visible against real API responses — the SEC EDGAR response used different field names than the PDR assumed, and arXiv used HTTP instead of HTTPS causing 301 redirects. The Phase 4 consistency tests caught these only partially; the live smoke tests caught them fully.

## Key Insights

- **Config before code catches schema mismatches early.** By adding source definitions and scoring weights in Phase 1, the project discovered that two sources needed new fields before any adapter code existed. Fixing a JSON file is cheaper than refactoring a class.
- **Tier by API complexity, not by business priority.** The natural instinct is to build the most important adapter first. Instead, building the simplest APIs first establishes the pattern that harder adapters follow. Tier 1 adapters became the reference implementation for Tier 2.
- **Registry consistency tests are cheap insurance.** A 43-line test that cross-checks the config registry against the code registry caught a mismatch (source ID `edgar` vs `sec_edgar`) that would have caused a silent runtime failure. The test took 5 minutes to write.
- **Live smoke tests are non-negotiable for external APIs.** Mock tests cannot catch field-name mismatches, redirect behavior, or rate-limit quirks. Even a single live request per adapter during development would have caught the SEC EDGAR and arXiv bugs before they were committed.
- **Each phase must be independently committable.** The 4-phase structure meant that if Phase 3 (Reddit/Semantic Scholar) had been blocked by API access issues, Phases 1-2 were already committed and testable. No phase depended on a later phase.

## Applicability

This pattern applies whenever you are adding multiple plugins, integrations, or data sources to a system that already has a working registry pattern. It is less useful for a greenfield system where the plugin contract itself is still evolving — there, you want one adapter end-to-end before generalizing.

## Related Lessons

- [Base Adapter ABC Pattern](base-adapter-abc-pattern.md) — the contract that makes phased expansion possible
- [Live API vs Mock Divergence](live-api-vs-mock-divergence.md) — the specific bugs that Phase 4 and post-expansion fixes caught
- [Config-First Development](config-first-development.md) — the general principle behind Phase 1's ordering

# Archived Documentation

Historical documents from the Lessons Hub project. These are completed plans, superseded specs, and point-in-time reviews preserved for reference. They are not actively maintained.

## Completed Implementation Plans

| File | Description |
|------|-------------|
| [v2_hardening_plan.md](v2_hardening_plan.md) | V2 production hardening — 9 phases, 53 tasks, 18 requirements. All completed 2026-05-09. Covers config, adapters, logging, locking, GitHub security, CSS, caching, stemming, and metrics. |
| [site_enhancements_plan.md](site_enhancements_plan.md) | Site UX improvements — 5 phases. About page walkthrough, lesson carousel, API URL config, chat UI polish, admin dashboard. Completed 2026-05-09. |
| [testing_lessons_plan.md](testing_lessons_plan.md) | Testing lesson authoring — 5 phases. Created lessons on acceptance testing, test pyramid, mock vs live, preflight gates, and cross-repo validation. Completed 2026-05-10. |
| [suggestions_plan.md](suggestions_plan.md) | Code quality fixes — 5 phases. Schema ordering, artifact split, GitHub security, emoji stemming, type safety. Completed 2026-05-09. |
| [lessons_hub_plan.md](lessons_hub_plan.md) | Original V1 implementation plan. Built Astro skeleton, harvest pipeline, validation, rendering, Pagefind search, and GitHub Pages deploy. Superseded by V2 work. |
| [lessons_hub_v2_plan.md](lessons_hub_v2_plan.md) | V2 implementation plan — 8 phases, 178 tests passing at completion. Added RAG chatbot, gap detection, GitHub discovery, multi-cloud adapters. Superseded by hardening and enhancement plans. |

## Design and Requirements Documents

| File | Description |
|------|-------------|
| [v2_suggestions_prd.md](v2_suggestions_prd.md) | Physical design requirements for V2 hardening. 18 requirements (R-01 through R-18) covering config, adapters, logging, and security. Source document for v2_hardening_plan. |
| [prd_v2_suggestions.md](prd_v2_suggestions.md) | Pre-hardening suggestions listing 9 code-level issues found in V2 review. All items were rolled into the hardening and suggestions plans. |
| [v2_summary.md](v2_summary.md) | V2 completion summary. Documents what V2 added (RAG, gaps, discovery, cloud adapters) and the final state: feature-complete across 8 phases with 147 passing tests. |
| [DPR-suggestions.md](DPR-suggestions.md) | Educational document explaining the Design-PDR-Plan workflow and why phased implementation plans are useful. |

## Point-in-Time Reviews

| File | Description |
|------|-------------|
| [review-2026-05-08.md](review-2026-05-08.md) | Pre-hardening code review. Identified XSS via `set:html`, uncommitted production files, duplicated validation, zero E2E tests, CSS duplication. Most issues resolved by hardening plan. |
| [review-2026-05-10.md](review-2026-05-10.md) | Post-hardening code review. Found remaining XSS on innerHTML pages, test coverage gaps in backend modules. Identifies work still open at time of writing. |

## Historical

| File | Description |
|------|-------------|
| [startup.md](startup.md) | Original startup/resume instructions for V1 implementation. Refers to Phase 1 as "not yet started." Obsolete — all implementation is complete. |
| [suggestions20250509.md](suggestions20250509.md) | Initial problem analysis listing 9 code issues in V2. Rolled into prd_v2_suggestions and split between the hardening and suggestions plans. |

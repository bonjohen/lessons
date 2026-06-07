---
title: Code Review as Requirements Source
summary: Systematic triage of code review findings produces a traceable requirements document — turning ad hoc observations into prioritized, implementable work.
date: 2026-05-09
phase: process
lesson_type: process
status: active
tags: [code-review, requirements, process, traceability, prioritization]
---

# Code Review as Requirements Source

## The Lesson

A structured code review produces two kinds of value: immediate fixes and a durable requirements backlog. When review findings are triaged, numbered, and tracked through a status lifecycle, they become inputs to the next implementation plan rather than a list of suggestions that slowly goes stale.

## Context

A static site with a Python harvesting pipeline and a FastAPI RAG backend underwent a full code review after V1 was complete (10 phases, 43 tests). The review produced 11 findings (F-01 through F-11) across 5 severity levels. Subsequently, V2 added 8 more phases of features (RAG chatbot, gap detection, multi-cloud deployment). After V2 was complete, the original review findings needed to be reconciled with the new codebase, and the V2 implementation summary's own "reviewer notes" and "known limitations" needed to be consolidated into actionable requirements.

## What Happened

1. The initial code review produced 11 numbered findings (F-01 through F-11) with severity levels (Critical, High, Medium, Low), evidence (specific file paths and line numbers), impact assessments, and suggested fixes. Each finding had a unique ID.
2. V2 implementation fixed 9 of the 11 findings as side effects of the feature work — XSS sanitization (F-01), uncommitted files (F-02), duplicated validation (F-03), missing integration tests (F-04), documentation drift (F-05), breadcrumb CSS (F-08), @ts-nocheck (F-09), magic numbers (F-10), and CSP headers (F-11).
3. Two findings remained open after V2: inconsistent error handling between scripts (F-06) and duplicated tag CSS (F-07).
4. The V2 implementation summary — a post-implementation document recording what was built, what shortcuts were taken, and what limitations remained — accumulated its own technical debt: 4 "must-fix" items, 4 "should-fix" items, and 4 "nice-to-have" items, plus 5 "reviewer notes" scattered through the architecture sections.
5. A consolidated requirements document was created that merged the 2 remaining review findings with the 12 summary limitations and 5 reviewer notes. This document served as a physical design requirements spec for the hardening work — it listed each requirement with current behavior, required behavior, affected components, and verification criteria. Deduplicated overlapping items (e.g., review F-10 "magic numbers" and summary "magic numbers" merged into one requirement R-08).
6. Assigned new requirement IDs (R-01 through R-18), organized by priority tier, and wrote technical specifications for each — current behavior, required behavior, affected files, and verification criteria.
7. The requirements document became the direct input for a 9-phase hardening plan with 53 task rows, each traceable back to a requirement ID.

## Key Insights

- **Number everything.** F-01 through F-11 and R-01 through R-18 are unambiguous references. "That CSS issue" is not. When a finding becomes a requirement becomes a plan task, the ID chain (F-07 → R-11 → Phase 6, row 6.4) lets anyone trace why a change was made.

- **Feature work fixes review findings accidentally.** 9 of 11 findings were resolved by V2 feature development without explicit attention. This is normal — good feature work improves code quality as a side effect. The risk is assuming all findings are fixed. A reconciliation pass after the feature work confirms which findings actually closed.

- **Reviewer notes are requirements in disguise.** Inline comments like "No thread-safety on the global singletons" or "Clone happens synchronously — will timeout" are observations, not action items. They sit in a summary document and get forgotten. Extracting them into numbered requirements with acceptance criteria turns observations into work.

- **Consolidation eliminates duplicates and reveals gaps.** The review found "magic numbers" (F-10). The summary also noted "magic numbers" (§11.8). These are the same issue but expressed differently. A consolidation pass merged them into R-08 with specific file paths and thresholds. Without consolidation, both would have generated separate plan tasks doing the same work.

- **Priority tiers must be deployment-relative.** "Hardcoded API URL" is a non-issue for local development but a production blocker. The priority tier (must-fix / should-fix / nice-to-have) reflects distance from production readiness, not severity of the code smell. This reframing changed 4 items from "medium" review findings to "must-fix" production blockers.

## Applicability

This pattern works when:
- A project has undergone at least one round of review or audit
- The review produced more findings than can be fixed immediately
- The project is entering a hardening or stabilization phase after active feature development
- Multiple sources of technical debt need to be reconciled (reviews, TODOs, inline notes)

It does **not** apply when:
- The review found only 1-2 issues that can be fixed immediately
- The project is in active feature development where requirements come from product needs, not code quality
- The codebase is being rewritten rather than hardened

## Related Lessons

- [Five-Stage Design-to-Execution Workflow](five-stage-design-to-execution.md) — the workflow that turns consolidated requirements into phased plans
- [Validation Severity Model](validation-severity-model.md) — a related approach to classifying issues by impact

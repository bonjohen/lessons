# Structured Code Review as a Phase Gate

## The Lesson

Running a systematic, category-driven code review after implementation is complete catches a class of issues that per-phase testing and acceptance criteria miss. Per-phase verification asks "does this phase work?" — a structured review asks "what's wrong across the whole codebase?" The two are complementary, not redundant.

## Context

A 7-phase implementation plan built a static knowledge library site with a Python content pipeline, Astro frontend, Pagefind search, and a FastAPI RAG backend. Each phase had its own verification step (tests pass, lint clean, build succeeds). Phase 7 included a 20-item acceptance criteria checklist that verified every feature end-to-end. After all phases were complete and all acceptance criteria were met, a full structured review was run covering 7 categories: security, dead code, documentation drift, test gaps, consistency, architecture, and operations.

## What Happened

1. All 7 phases completed successfully. Each phase committed only after tests passed and lint was clean. The Phase 7 acceptance criteria verified all 20 items as passing.
2. A structured review was run using a systematic protocol: grep for `innerHTML`, check CORS config, scan for secrets, audit `.gitignore`, cross-reference CI scripts with `package.json`, check for unused exports, and verify documentation accuracy.
3. The review found 10 issues: 1 critical (XSS in chat panel), 2 high (hardcoded API URL, CI dependency drift), 5 medium (duplicate adapter instances, dead code, no CSP, npm audit vulns, untested embed script), 2 low (missing gitignore entries, untracked doc file).
4. The critical XSS had survived Phase 5 (implementation), Phase 6 (E2E tests), and Phase 7 (acceptance criteria) — three separate verification passes. None of them included a "grep for innerHTML" check.
5. The review took approximately 5 minutes and produced an actionable remediation plan with prioritized phases. The XSS fix took 2 minutes to implement.
6. The review document (`docs/review-2026-05-11.md`) served as a persistent record of known issues and their disposition, preventing rediscovery of the same issues in future sessions.

## Key Insights

- **Per-phase testing verifies features, not properties.** Tests ask "does the chat endpoint return an answer?" — they don't ask "is the chat panel safe from XSS?" Security, consistency, and architecture quality are cross-cutting properties that no single phase owns.
- **Grep-based audits find classes of bugs instantly.** `grep -rn "innerHTML" src/` finds every instance of a dangerous pattern in seconds. This is categorically different from writing test cases, which find individual bugs. A single grep can be worth more than a dozen unit tests for certain vulnerability classes.
- **Acceptance criteria test the happy path.** The 20 acceptance criteria verified that every feature worked as intended — homepage renders, search returns results, chat shows answers. None of them tested adversarial input, misconfiguration, or edge cases. Acceptance criteria are necessary but not sufficient.
- **The review must produce a durable artifact.** Writing findings to `docs/review-YYYY-MM-DD.md` with severity levels and specific remediation tasks means the review's value persists across sessions. A verbal "we should fix that innerHTML" is forgotten by the next session; a documented F-01 with file paths and fix instructions is actionable indefinitely.
- **Severity calibration matters.** Not every finding needs immediate action. Separating critical (fix now) from medium (fix when touching nearby code) from low (fix opportunistically) prevents review fatigue. A review that marks everything as "high" gets ignored; one that marks the XSS as critical and the gitignore as low gets the right work done first.

## Applicability

This applies to any project completing a significant implementation phase — feature launches, migrations, new subsystems. It's most valuable when the implementation was done quickly or autonomously (automated plans, AI-assisted coding) where cross-cutting concerns may have been deprioritized in favor of feature velocity. It does NOT replace continuous security practices like dependency scanning, SAST, or penetration testing — it complements them with a human-readable, project-specific audit.

## Related Lessons

- [XSS via innerHTML in LLM Chat Interfaces](xss-in-llm-chat-interfaces.md) — the critical finding from this review
- [CI Dependency Lists Drift from pyproject.toml](ci-dependency-drift.md) — a high-severity finding from the same review
- [Preflight Checks Prevent Push-then-Fix Cycles](preflight-prevents-push-fix-cycles.md) — another verification layer, operating at push time rather than review time

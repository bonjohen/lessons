# Phased Plan Execution with One Commit Per Phase

## The Lesson

When building a multi-phase system, track progress at the row level within each phase (Open → Started → Completed with timestamps), commit only when an entire phase is green, and never batch multiple phases into one commit. This granularity makes it possible to resume mid-phase, measure velocity, and bisect regressions to specific phases.

## Context

A six-phase platform build went from empty repository to 203 passing tests in a single session: canonical schema, knowledge model population, Mermaid renderer, REST API, extraction pipeline, and Graphviz + React Flow frontend. Each phase had 6-9 task rows. The plan file (`docs/diagram_plan.md`) was the sole source of truth for progress — not git history, not memory, not conversation state.

## What Happened

1. A plan file was written with six phases, each containing a markdown table with columns: PhaseNo, Status, Started (PST), Completed (PST), Description. Initial state: all rows `Open`.
2. Execution followed a strict loop: read the plan → find the first non-Completed row → flip to `Started` with a timestamp → do the work → verify (tests, lint) → flip to `Completed` with a timestamp → repeat.
3. Each phase ended with a summary block recording what changed, and a single commit containing all of that phase's changes. No partial-phase commits. No multi-phase commits.
4. The plan file itself was committed as part of each phase — so the git history shows both the code changes AND the plan state transitions in the same commit.
5. Phase 4 had two commits (`b7a6731` and `9018726`) because the implementation summary update was missed in the first commit. This was the only deviation from the one-commit-per-phase rule, and it was visible in the plan because timestamps showed the gap.
6. Test counts accumulated predictably: 33 → 70 → 112 → 143 → 184 → 203. Each phase's test delta was recorded in its summary, making it trivial to verify that no tests were lost or skipped.

## Key Insights

- **The plan file is the state machine, not the conversation.** If execution is interrupted (context limit, session timeout, network failure), the plan file's row statuses tell the next session exactly where to resume. Conversation history is ephemeral; the plan file is persisted.
- **Timestamps catch time-sink phases.** Phase 2 (knowledge model) took 9 minutes. Phase 5 (extraction pipeline) took 5 minutes. Phase 4 (API) took 5 minutes. Without timestamps, "it took a while" is the best you get. With timestamps, you can identify which phases are bottlenecks and plan accordingly for future projects.
- **One commit per phase enables clean bisection.** If tests break after Phase 4, you know the API layer caused it — you don't have to untangle a mega-commit. If tests break within a phase, the row-level descriptions narrow the search further.
- **Phase summaries are commit messages with memory.** The summary block records what was created, what was modified, test counts, and lint status. It's more detailed than a commit message needs to be, but it serves as a changelog entry and a verification record in one artifact.
- **Green-only commits prevent cascading failures.** The rule "never commit a partial phase" and "never commit while verification is failing" means every commit in the history is a known-good state. You can check out any phase commit and run the full test suite with confidence.

## Applicability

This pattern applies to any multi-phase build or migration where phases are independently verifiable: platform builds, database migrations, infrastructure provisioning, content migrations, multi-step refactors. It does NOT apply to exploratory or research work where the path is unknown — there, committing frequently (even with failing tests) preserves the exploration trail.

## Related Lessons

- [Canonical Model as Single Source of Truth](canonical-model-single-source-of-truth.md) — the model-first approach that made phased execution possible (Phase 1-2 before any renderer)

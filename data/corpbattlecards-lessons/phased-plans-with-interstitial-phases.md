# Phased Plans with Interstitial Phases

## The Lesson

When mid-project discoveries require new work that doesn't fit the original phase structure, insert interstitial phases (3.5, 6.5) rather than renumbering downstream phases. This preserves commit history references, plan file anchors, and team communication while accommodating scope changes.

## Context

Corporate Battle Cards followed a 10-phase implementation plan tracked in `docs/game_plan.md`. Each phase had a numbered task table with status columns, timestamps, and a commit protocol (one commit per phase). The plan was written before implementation started, based on a PDR. Two significant mid-stream discoveries required new phases: the need for a spreadsheet-to-JSON generator (between Phase 3 and 4) and a public market overhaul plus content flavor pass (between Phase 6 and 7).

## What Happened

1. The original plan had 10 phases numbered 1-10, designed to build up from data model to UI in a linear dependency chain.
2. After Phase 3 (core engine), it became clear that hand-authoring 92 cards in JSON was impractical. Phase 3.5 was inserted to build a generator script that reads from the authoritative spreadsheet.
3. Phase 3.5 was scoped, written, and executed without touching Phase 4's description or numbering. Git commit messages referenced "Phase 3.5" directly.
4. After Phase 6 (AI opponent), playtesting revealed that the 20 single-pool public market cards were too simple and the card names/narratives lacked thematic coherence. Phase 6.5 was inserted for a public market overhaul (20 cards to 12 multi-effect cards) and a GTM flavor pass on all 72 private cards.
5. Phase 6.5 changed the card count (92 to 84), the public card mechanic, and all card names/narratives. Downstream phases (7-10) required no plan edits because they referenced game features, not card counts.
6. The final plan had 12 phases (1, 2, 3, 3.5, 4, 5, 6, 6.5, 7, 8, 9, 10) with a clean commit history where each commit maps to exactly one phase.

## Key Insights

- **Renumbering breaks references.** If Phase 3.5 had been "Phase 4" and everything shifted, commit messages like "Phase 4: effect resolution" would have been wrong retroactively. Half-phases avoid this entirely.
- **Interstitial phases signal that learning happened.** A phase numbered 3.5 communicates to anyone reading the plan that this work was discovered during execution, not anticipated during design. This is useful context for future planning.
- **Downstream phases should reference capabilities, not counts.** Phase 7 said "AI-vs-AI games run headless" — not "92 cards load." This made it resilient to the Phase 6.5 card count change (92 to 84).
- **The half-phase pattern has a natural limit.** You can do 3.5 and 6.5, but 3.25 or 6.75 would be a sign that the plan needs a structural rewrite, not more patches.
- **One commit per phase is the anchor.** The commit protocol (one commit per completed phase, never batched) means each phase is a single, reviewable unit of work in git history. Interstitial phases get the same treatment.

## Applicability

This pattern applies to any phased plan tracked in a document or issue tracker where phases are referenced by number in commits, PRs, or conversations. It does NOT apply when phases are unnamed/unnumbered (just a flat task list) or when the plan is so short that renumbering is trivial.

## Related Lessons

- [Simulation as Acceptance Test](simulation-as-acceptance-test.md) — Phase 7 established the simulation baseline; Phase 10 verified it hadn't regressed despite two interstitial phases of changes.

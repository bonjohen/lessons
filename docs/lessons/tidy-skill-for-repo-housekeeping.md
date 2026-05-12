---
title: Tidy Skill for Repo Housekeeping
summary: A structured, behavior-preserving housekeeping pass prevents repo entropy without the risk of accidental refactors.
date: 2026-05-11
phase: maintenance
lesson_type: process
status: active
tags: [housekeeping, maintenance, dead-code, documentation-drift, archiving, skills]
---

# Tidy Skill for Repo Housekeeping

## The Lesson

Repositories accumulate entropy — stale docs, dead code, orphaned scripts, outdated counts — and the longer it goes unaddressed, the harder it is to trust what's in the repo. A structured, scoped housekeeping pass that archives rather than deletes, verifies before removing, and never changes behavior keeps the codebase trustworthy without introducing risk.

## Context

Across multiple projects (lessons, Artemis, JobClass, Certification), the same pattern repeated: one-time migration scripts lingered in the repo root, documentation counts drifted from reality, unused imports accumulated, and files ended up in the wrong directories. Developers hesitated to clean up because cleanup mixed with behavior changes is dangerous — a "quick tidy" that accidentally removes a dynamically-dispatched module breaks production.

The `/tidy` skill was built to formalize housekeeping as a distinct, auditable activity with explicit safety rails.

## What Happened

1. Early repo maintenance was ad-hoc — developers would notice stale files and delete them inline with feature work, making it hard to distinguish housekeeping from functional changes in code review.
2. Several incidents occurred where "cleanup" commits introduced bugs: an import removed because it looked unused was actually loaded dynamically via a dispatch dictionary; a script archived while another script still referenced it by path.
3. The tidy skill was designed as a six-step protocol: archive stale files, update documentation, clean dead code, normalize file organization, verify consistency, and commit. Each step has explicit "do NOT" rules to prevent overreach.
4. Key safety decisions: files are archived (`git mv` to `archive/`) rather than deleted; every removal requires a `Grep` confirmation that no references exist; test assertions are only updated when the tidy itself changed a path or count; and all housekeeping goes in a single `chore: tidy` commit separate from any feature work.
5. The skill supports scoped runs (`/tidy docs`, `/tidy scripts`, `/tidy code`, or a specific path) so a developer can address one area without committing to a full sweep.

## Key Insights

- **Archive, never delete.** Moving stale files to `archive/` preserves them for reference while removing them from the active codebase. This is reversible — deletion is not (without digging through git history). The archive directory becomes a project's institutional memory.

- **Verify references before removing anything.** The most common housekeeping bug is removing something that's still used dynamically — dispatch dictionaries, plugin registries, `__all__` exports, and CLI entry points all create references that don't show up in static import analysis. A `Grep` for the filename and exported symbols catches most of these.

- **Separate housekeeping from feature work.** A `chore: tidy` commit that only contains non-behavioral changes is easy to review, easy to revert, and easy to skip in `git blame`. Mixing cleanup into feature commits makes both harder to understand.

- **Documentation drift is the quietest rot.** Stale counts, outdated file paths, and "next up" sections describing completed work erode developer trust in docs. Fixing factual inaccuracies without rewriting prose style keeps docs reliable without scope creep.

- **Scoping prevents exhaustion.** A full-repo tidy on a large project can touch dozens of files. Scoped runs (`/tidy docs`) let you address one category at a time, keeping each pass reviewable and the commit message meaningful.

## Applicability

This pattern applies to any project that lives longer than a few months. It's especially valuable for:
- Multi-contributor projects where no single person has full context on what's still active
- Projects with a `docs/` directory that includes counts, module maps, or status sections
- Monorepos where files migrate between packages over time

It does NOT apply to:
- Greenfield projects with no accumulated history
- One-off scripts or experiments that won't be maintained

## Related Lessons

- [Skill-Driven Workflow Automation](skill-driven-workflow-automation.md) — The tidy skill is one instance of the broader pattern of encoding workflows as composable slash commands
- [Five-Stage Design-to-Execution Workflow](five-stage-design-to-execution.md) — Tidy runs happen between stages or after a phase completes, not during active implementation
- [Validation Severity Model](validation-severity-model.md) — The tidy skill's "verify consistency" step uses the same lint/test/format gates as CI

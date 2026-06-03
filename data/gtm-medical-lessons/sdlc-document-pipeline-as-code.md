---
phase: process
---

# SDLC Document Pipeline as Code

## The Lesson

A structured document pipeline (user requirements → PDR → plan → expand → implement) turns vague product conversations into executable phase plans. The pipeline's value isn't the documents themselves — it's forcing decisions at the right time and preventing implementation from starting before the design is settled.

## Context

A medical portal needed to go from zero code to a working authenticated shell with OAuth, session management, role-based access, encrypted config, and audit logging. The team used an AI-assisted pipeline with five stages: draft user requirements, generate a physical design review (PDR), generate a release plan, expand into per-phase execution plans, then implement phase-by-phase. Sprint 1 produced 7 phases across 17 commits. Sprint 2 planning (11 phases) followed the same pipeline.

## What Happened

1. User requirements were captured as a structured document with functional requirements, acceptance criteria, and explicit gaps.
2. A PDR was generated from the requirements — making concrete decisions about data model, component interfaces, API endpoints, and technology choices.
3. A phased release plan was generated from the PDR, with task tables and dependency ordering.
4. The plan was expanded into standalone phase files, each containing enough context (schema, patterns, imports) for an implementer to work without re-reading the full PDR.
5. Phases were executed sequentially. Each phase committed independently. Status was tracked via timestamps in the plan files themselves.
6. Sprint 1 completed 7 phases in a single session. Sprint 2 planning (PDR → plan → expand) reused the same pipeline with no structural changes.

## Key Insights

- **The PDR is where the hard decisions happen.** User requirements say "the system shall support roles." The PDR says "six roles, 12 permissions, union-merged, stored in these tables." Skipping the PDR means making these decisions mid-implementation, where they're harder to change.
- **Phase plans must be self-contained.** An implementer holding only the phase plan and the codebase should be able to do the work. This means copying schema, patterns, and rationale from the PDR into each phase's Context section. Verbose phase plans are better than ones that require cross-referencing.
- **Explicit gap tracking prevents silent assumptions.** Both user requirements and PDR documents have "Gaps" sections. Writing "the conversation did not define X" is more useful than silently choosing a default — it creates a decision record.
- **Dashboard format scales.** Sprint 1 used per-task rows in the master plan. Sprint 2 switched to a dashboard (one row per phase, task detail in phase files only). The dashboard format reduced master plan noise from 200+ rows to 11.
- **The pipeline is reusable across sprints.** Sprint 2 ran the same gen-pdr → finalize → expand sequence with zero structural changes. The pipeline is the process, not a one-time artifact.

## Applicability

This pattern works for greenfield projects where the full scope is known upfront. It's less suited for exploratory/research work where requirements emerge from experimentation. The document overhead is justified for systems with 5+ phases; for a 2-phase feature, a single design doc suffices.

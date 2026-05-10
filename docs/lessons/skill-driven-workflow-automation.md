---
title: Skill-Driven Workflow Automation
summary: Composable slash-command skills turn multi-step developer workflows into repeatable single-command operations that enforce guardrails automatically
date: 2026-05-10
phase: execution
lesson_type: process
status: active
tags: [workflow, automation, skills, ci, process, claude-code]
---

# Skill-Driven Workflow Automation

## The Lesson

When a developer workflow has more than three steps that must happen in a specific order with specific guardrails, encoding it as a composable skill (a reusable prompt-driven command) eliminates both the cognitive load of remembering the steps and the risk of skipping safety checks. Skills compose: a push skill can invoke a preflight skill, which invokes lint/test gates, creating a pipeline that enforces quality without requiring discipline at every step.

## Context

A solo developer managing four repositories with CI/CD pipelines, phased execution plans, and a lessons-learned knowledge base found that the most common source of friction was not writing code — it was the mechanical workflow surrounding code: remembering to run lint before pushing, updating plan file timestamps when starting work, running the right pytest invocation (not bare `pytest` due to interpreter mismatch), checking gap files after writing lessons, and tracking phase state across sessions. Each step was simple; the aggregate sequence was error-prone.

## What Happened

1. The first skill created was `/push` — a commit-push-monitor-fix cycle that replaced a 5-step manual process (stage, commit, create sentinel, push, watch CI). It immediately caught the pattern of pushing unformatted code by invoking preflight checks before the push.
2. `/preflight` was extracted as a standalone skill after recognizing that the same gate-checking logic was useful independently of pushing — during development, before reviews, and when diagnosing CI failures locally.
3. `/phase` encoded the plan-execution loop: read the plan file, find the next open row, flip to Started with a PST timestamp, do the work, flip to Completed, and commit when the phase finishes. This eliminated timestamp drift and partial-phase commits.
4. `/lessons` provided discover/write/audit/repair modes for the knowledge base, ensuring lessons followed a consistent template and were cross-referenced properly.
5. `/review` systematized codebase audits into repeatable categories (security, consistency, hygiene) with structured output that fed directly into remediation plans.
6. `/healthcheck-machine` extended the pattern to infrastructure, running diagnostic scripts on specific machines and reporting PASS/FAIL/WARN status.
7. The composition pattern emerged naturally: `/push` calls `/preflight`, which runs lint → format → test → script-audit → optional-dep-check. A single command (`/push`) triggers a 12-step pipeline that would otherwise require remembering and executing each step manually.

## Key Insights

- **Skills encode guardrails, not just convenience.** The push skill's most important feature isn't saving keystrokes — it's the sentinel file that makes `git push` impossible without running preflight first. The guardrail is structural, not dependent on remembering to do the right thing.

- **Composition beats monoliths.** `/push` invoking `/preflight` means preflight improvements automatically benefit the push workflow. If a new lint rule is added to preflight, every future push checks it. A monolithic push script would need to be updated separately.

- **Skills bridge sessions.** `/phase` reads the plan file to determine where work left off, regardless of whether the current session started the work. Plan state lives in the file (Started/Completed timestamps), not in conversation context. This makes sessions disposable — you can compact, restart, or switch sessions without losing progress.

- **The skill boundary is "would I forget a step?"** If a workflow has steps you always remember (like `git add`), it doesn't need a skill. If it has steps you sometimes skip (like running format checks, or updating a timestamp), that's where a skill adds value. The threshold is about three conditionally-skipped steps.

- **Discovery mode prevents premature automation.** The `/lessons discover` mode proposes candidates without writing files. This separation between "identify what could be done" and "do it" prevents the skill from generating work the user didn't ask for — a critical boundary when automation has write access.

- **Skills are documentation that executes.** Each skill's SKILL.md file serves double duty: it's the implementation (the LLM follows it as a prompt) and the documentation (a human can read it to understand the workflow). There's no drift between docs and behavior because they're the same artifact.

## Examples

### Composition Chain

```
User: /push

/push skill activates:
  1. git status, git diff --stat, git log (pre-flight checks)
  2. Stage files, create commit
  3. Invoke /preflight:
     ├── Gate 1: ruff format --check
     ├── Gate 2: ruff check
     ├── Gate 3: python -m pytest (not bare pytest!)
     ├── Gate 4: Workflow script existence audit
     └── Gate 5: Optional dependency scan
  4. If preflight PASS:
     ├── Create push sentinel file
     ├── git push (hook checks sentinel, deletes after use)
     ├── Poll GitHub Actions run
     └── If CI fails: diagnose, fix, re-commit, re-push (up to 3x)
  5. Report final status
```

### Plan-Driven Execution (`/phase`)

```
Before /phase:
| 3.1 | Open | | | Write adapter factory |

During /phase:
| 3.1 | Started | 2026-05-10 09:04 PM (PST) | | Write adapter factory |

After /phase:
| 3.1 | Completed | 2026-05-10 09:04 PM (PST) | 2026-05-10 09:11 PM (PST) | Write adapter factory |
```

The skill handles: reading the plan, picking the right row, timestamping, doing the work, verifying, committing per-phase. A human just types `/phase docs/my_plan.md`.

### Guardrail Enforcement

```
# Without skills — relies on memory:
git add .
git commit -m "feat: add adapter"
git push                              # Oops, forgot to lint

# With /push — guardrails are structural:
/push "feat: add adapter"
  → preflight runs automatically
  → lint failure caught
  → push blocked until fixed
  → sentinel ensures single-use authorization
```

## Applicability

This pattern works when:
- Workflows have 3+ steps with ordering constraints
- Some steps are safety checks that are tempting to skip under time pressure
- Work spans multiple sessions and needs persistent state (plan files, gap records)
- A single developer or small team wants CI-level discipline without CI-level friction
- The automation layer can read and write files (skills need persistent state)

It does NOT work when:
- Workflows are genuinely one-step (don't over-abstract)
- The steps vary significantly each time (skills encode repeatable patterns, not ad-hoc decisions)
- Multiple people need to agree on workflow changes (skills in a personal dotfiles directory are single-user; team workflows belong in CI)
- The automation layer has no persistent context (skills depend on reading plan files, configs, and prior state)

## Related Lessons

- [Five-Stage Design-to-Execution Workflow](five-stage-design-to-execution.md) — the workflow that `/phase` automates
- [Preflight Gates as Local CI](preflight-gates-as-local-ci.md) — the specific gates that `/preflight` runs
- [Code Review as Requirements Source](code-review-as-requirements-source.md) — the pattern that `/review` systematizes

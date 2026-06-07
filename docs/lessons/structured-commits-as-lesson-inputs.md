---
title: Structured Commits as Lesson Inputs
summary: Commit messages with What/Why/Learned sections capture reusable insights at the moment of discovery, feeding downstream lesson extraction pipelines
date: 2026-06-06
phase: execution
lesson_type: process
status: active
tags: [git, process, knowledge-management, automation, lessons]
---

# Structured Commits as Lesson Inputs

## The Lesson

Commit messages are the cheapest place to capture engineering lessons because they happen at the exact moment of discovery — when the problem, root cause, and fix are all in working memory. Adding a structured "What we learned" section to commit messages creates a pipeline of lesson candidates that can be harvested, ranked, and refined into standalone lessons with minimal effort.

## Context

A lessons-learned knowledge base harvests markdown lesson files from multiple GitHub repositories. Lessons are written manually after the fact, which introduces two problems: (1) the insight has decayed — you remember *what* you did but not *why* that approach won over alternatives, and (2) writing a lesson is a separate task that competes with feature work for attention. Meanwhile, every commit already requires a message, and the developer (or AI assistant) who writes the message has full context on what went wrong and what was learned.

## What Happened

1. A date inference bug surfaced where all harvested lessons showed today's date. The root cause was that `infer_date_from_file()` used filesystem mtime, which is set to clone time for cloned repos.
2. The fix was straightforward — use `git log` instead of `stat()` — but the original commit message was a single line: `fix: use git commit date instead of filesystem mtime for lesson date inference`. The *what* was clear; the *why* and the reusable insight (filesystem metadata is unreliable in clone-based workflows) were lost.
3. This pattern repeated across the project's history. Good engineering decisions were buried in diffs with minimal commit messages, making lesson extraction harder.
4. A structured commit template was introduced with three sections: **What changed** (factual), **Why** (motivation), and **What we learned** (reusable insight). The third section maps directly to the "Key Insights" section of a lesson document.
5. Three implementation options were evaluated:
   - `.gitmessage` (git's `commit.template` config) — only works when git opens an editor, not with `git commit -m`
   - `commit-msg` hook — could validate structure, but the message author is the one who needs guidance, not enforcement
   - Feedback memory + versioned template doc — governs the AI assistant's behavior directly, which is where the messages originate
6. The feedback memory approach was chosen because it matches the actual mechanism: the template is a reference doc at `docs/commit-template.md`, and a persistent memory entry ensures the assistant follows it on every commit.

## Key Insights

- **Capture lessons at the point of discovery, not after.** The moment you understand a root cause is the moment to write down the reusable principle. Deferring to a separate "write lessons" task loses the nuance of *why* one approach won over alternatives. Commit messages are a natural capture point because they're already mandatory.

- **Structure enables automation; prose does not.** A commit message with labeled sections (What changed / Why / What we learned) is parseable by a harvester. A freeform paragraph with the same information is not. The structure costs the author almost nothing but makes downstream extraction dramatically easier.

- **The right enforcement mechanism depends on who writes the message.** `.gitmessage` and `commit-msg` hooks are designed for human developers using git interactively. When an AI assistant generates commit messages programmatically via `git commit -m`, the effective enforcement mechanism is the assistant's instruction set (memory/prompts), not git's hook system.

- **Not every commit has a lesson.** Formatting fixes, renames, and dependency bumps don't produce reusable insights. The template explicitly allows minimal messages for mechanical changes. Forcing structure on trivial commits creates noise that degrades the signal in the lesson pipeline.

## Examples

**Before (typical commit message):**
```
fix: use git commit date for lesson date inference
```

**After (structured commit message):**
```
fix: use git commit date instead of filesystem mtime for lesson date inference

What changed: infer_date_from_file() now runs git log to get the last
commit date before falling back to filesystem mtime. Corrected hardcoded
dates for gtmleads and data-readiness virtual lesson files.

Why: The harvester stamped all cloned-repo lessons with today's date
because git clone sets every file's mtime to the clone time.

What we learned: Filesystem metadata is unreliable for provenance in any
workflow that involves cloning or regenerating files. Git log is the
authoritative source for "when was this file last meaningfully changed."
```

## Applicability

This pattern applies to any project that extracts knowledge artifacts from development history — changelogs, postmortems, onboarding guides, architecture decision records. The key requirement is that someone (human or AI) is already writing commit messages and can add 2-3 sentences of structured context at negligible marginal cost.

It does NOT apply when commit messages are squash-merged away, when the team uses "fixup" commits extensively, or when the lesson extraction pipeline doesn't exist yet (build the pipeline first, then optimize its inputs).

## Related Lessons

- [Skill-Driven Workflow Automation](skill-driven-workflow-automation.md) — the `/push` skill that executes commits is the natural place to enforce the template
- [Code Review as Requirements Source](code-review-as-requirements-source.md) — another pattern for extracting knowledge from development artifacts

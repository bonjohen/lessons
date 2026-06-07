# Commit Message Template

This template governs how Claude Code structures commit messages in this project. The goal is to produce commit messages that double as raw material for lesson extraction — capturing not just *what* changed, but *why* and *what we learned*.

## Format

```
<type>: <short summary>

<What changed>
<paragraph describing the factual changes — files, functions, behavior>

<Why>
<paragraph explaining the motivation — what broke, what constraint drove this,
what the user asked for, what gap existed>

<What we learned>
<paragraph capturing the reusable insight — the thing that would be valuable
to someone facing a similar situation in a different project. This is the
section that maps directly to lesson content.>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

## Type Prefixes

Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`.

## Section Guidelines

### What changed
- Factual, concise. Name the files and functions affected.
- Describe behavior changes, not line-level diffs (the diff does that).

### Why
- State the problem, constraint, or user request that motivated the change.
- If a bug, describe the symptom and root cause.
- If a feature, describe the gap it fills.

### What we learned
- Frame as a reusable principle, not a project-specific fact.
- Good: "Filesystem mtime is unreliable for date inference in cloned repos because git clone sets all mtimes to the clone time."
- Bad: "Fixed the date bug."
- If the change is purely mechanical (formatting, renames), this section can be omitted.

## When to Omit Sections

- **Style/format commits**: type + summary line is sufficient. Omit Why and What we learned.
- **Trivial fixes**: type + summary + one-line Why. Omit What we learned if there's nothing reusable.
- **Feature/fix/refactor commits**: all three sections expected.

## Examples

### Full commit message
```
fix: use git commit date instead of filesystem mtime for lesson date inference

What changed: infer_date_from_file() in scripts/lesson_core.py now runs
git log to get the last commit date for a file before falling back to
filesystem mtime. Also corrected hardcoded frontmatter dates for gtmleads
(2026-05-20) and data-readiness (2026-05-24) virtual lesson files.

Why: The harvester was stamping all cloned-repo lessons with today's date
because git clone sets every file's mtime to the clone time. This made
the "Recent Lessons" section on the homepage show stale repos as if they
were just updated.

What we learned: Filesystem metadata is unreliable for provenance in any
workflow that involves cloning, copying, or regenerating files. Git log
is the authoritative source for "when was this file last meaningfully
changed" — but only within the repo that owns the file's history. For
virtual/local repos whose files are checked into a different repo, the
date must be set explicitly in frontmatter or derived from the source
project's history.
```

### Minimal commit message
```
style: format lesson_core.py
```

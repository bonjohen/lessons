---
title: Validation Severity Model
summary: Why the validator uses ERROR/WARNING/INFO levels and why warnings never fail the build.
date: 2026-05-08
phase: implementation
lesson_type: process
status: active
tags: [validation, error-handling, build-pipeline]
---

## Context

The lesson validator (`scripts/validate_lessons.py`) checks harvested data for correctness. Source repos have varying levels of frontmatter completeness — some lessons have full metadata, many have none.

## Decision

The validator uses three severity levels:

- **ERROR**: Build fails. Reserved for structural problems that would cause broken pages or corrupt data: duplicate IDs, empty content, missing required files, invalid JSON.
- **WARNING**: Build continues. Used for missing optional metadata (summary, date, tags, phase, lesson_type) and quality concerns (short content, unknown controlled values). These are informational — the site renders correctly without them.
- **INFO**: Pure diagnostics. Repo counts, lesson counts.

## Why Warnings Don't Fail the Build

Real-world lesson files rarely have complete frontmatter. The certification repo has 28 lessons with no frontmatter at all — they're still valid, useful lessons. Failing on missing optional fields would block the build for every repo that doesn't follow the ideal schema.

The harvester infers safe defaults (title from H1 or filename, status defaults to `active`) so the site always builds. Warnings alert maintainers to improvement opportunities without blocking deployment.

## Key Takeaway

Validation severity should match the impact of the problem. Only fail the build for things that would actually break the output. Everything else is a suggestion.

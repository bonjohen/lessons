# Lesson Template

Use this template when writing a new lesson document. Save as `docs/lessons/your-lesson-name.md` in your source repository.

## Template

```markdown
---
title: Short Descriptive Title
summary: One-sentence summary of the key takeaway.
date: YYYY-MM-DD
phase: design | implementation | testing | deployment | maintenance
lesson_type: architecture | implementation | testing | deployment | debugging | data-design | ai-assisted-development | documentation | maintenance | process | other
status: active | draft | superseded | deprecated
tags: [tag-one, tag-two, tag-three]
---

## Context

What was the situation? What were you trying to accomplish?

## Decision

What did you decide to do and why?

## Outcome

What happened? What worked, what didn't?

## Key Takeaway

The one thing someone should remember from this lesson.
```

## Field Reference

| Field | Required | Notes |
|-------|----------|-------|
| `title` | Yes (after normalization) | Can be inferred from first H1 or filename if missing |
| `summary` | Recommended | Shown in lesson cards and search results |
| `date` | Recommended | ISO format (YYYY-MM-DD) |
| `phase` | Recommended | Project phase when this lesson was learned |
| `lesson_type` | Recommended | Must be from controlled vocabulary |
| `status` | Optional | Defaults to `active` |
| `tags` | Recommended | Lowercase, hyphenated; normalized during harvest |

## Tagging Rules

- Use lowercase, hyphenated tags: `github-actions` not `GitHub Actions`
- Be specific: `python-frontmatter` not just `python`
- Reuse existing tags when possible
- 2-5 tags per lesson is ideal

## Example

```markdown
---
title: Schema Drift Validation
summary: Catch schema changes early by validating generated output against a known-good snapshot.
date: 2025-03-15
phase: testing
lesson_type: testing
status: active
tags: [schema-validation, json, testing, ci-cd]
---

## Context

Our build pipeline generates JSON data files from multiple sources. Schema changes in upstream sources silently broke downstream consumers.

## Decision

Added a validation step that compares generated JSON structure against a schema definition. Errors fail the build; warnings flag new optional fields.

## Outcome

Caught three breaking changes in the first week. Build failures now point directly to the changed field.

## Key Takeaway

Validate generated data at build time, not at runtime. The cost of a schema check is negligible compared to debugging a silent data format change.
```

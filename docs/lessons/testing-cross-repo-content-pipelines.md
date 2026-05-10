---
title: Testing Cross-Repo Content Pipelines
summary: Validate harvested content spanning multiple repositories with severity levels, slug uniqueness, schema enforcement, and link resolution
date: 2026-05-10
phase: execution
lesson_type: implementation
status: active
tags: [testing, validation, pipeline, cross-repo, content, schema]
---

# Testing Cross-Repo Content Pipelines

## The Lesson

When a build pipeline aggregates content from multiple source repositories, validation must operate at two levels: per-document correctness (schema, content quality) and cross-document consistency (unique IDs, resolvable links, no collisions). Severity levels (ERROR vs WARN) let the pipeline fail fast on data corruption while tolerating cosmetic issues that shouldn't block a deploy.

## Context

Lessons Hub harvests markdown lessons from 4+ source repositories, each with its own commit history, naming conventions, and frontmatter habits. The harvester clones each repo, parses `docs/lessons/*.md`, normalizes frontmatter, generates slugified IDs, and outputs a unified JSON dataset. This dataset feeds the Astro static site, the Pagefind search index, and the RAG corpus. A single bad document can break the site build, corrupt the search index, or produce nonsensical RAG responses — but not every imperfection is equally dangerous.

## What Happened

1. Early harvesting had no validation. A lesson with a duplicate slug silently overwrote another lesson in the JSON output, losing content without any error message.
2. A `validate_lessons.py` script was added post-harvest. The first version treated everything as an error — missing tags, no summary, short content all blocked the build. This made adding new repos painful because source authors hadn't followed the hub's conventions.
3. The validation was restructured into two severity levels:
   - **ERROR** (build fails): missing `repos.yml` fields, duplicate lesson IDs, empty content, unreadable files, generated JSON that doesn't match schema
   - **WARNING** (build continues): missing summary/date/tags/phase/lesson_type, unknown controlled vocabulary values, content shorter than 100 characters
4. Slug collision detection was formalized: lesson IDs are `{repo_id}-{lesson_slug}`, where `lesson_slug` is derived from the filename. Two lessons in different repos can have the same filename, so the repo prefix is mandatory. Two lessons in the same repo cannot have the same slug — that's an ERROR.
5. Cross-repo link resolution was added after discovering that lessons referencing other lessons via relative `.md` paths worked within their source repo but broke in the hub context. The validator checks that referenced lessons exist in the same repo's harvest output.

## Key Insights

- **Two severity levels is the minimum viable model.** One level (everything fails) makes the pipeline brittle and hostile to new content. Three+ levels add configuration burden without proportional benefit. ERROR/WARN maps directly to "blocks deploy" / "appears in report."

- **Validate at the boundary, not in the source repo.** Source repos don't know they're being harvested. Validation belongs in the hub pipeline, not as a pre-commit hook in each source repo. This keeps source repos autonomous while the hub enforces its own requirements.

- **Slug collision is the most dangerous silent failure.** When two documents produce the same ID, one overwrites the other with no trace. Detection must happen at aggregate time (after all repos are harvested) because the collision is cross-document:
  ```python
  seen_ids = {}
  for lesson in all_lessons:
      if lesson.id in seen_ids:
          errors.append(f"Duplicate ID '{lesson.id}': "
                       f"{lesson.source_path} collides with {seen_ids[lesson.id]}")
      seen_ids[lesson.id] = lesson.source_path
  ```

- **Frontmatter schema checks should be permissive on types.** Source repos may have YAML that produces lists where the hub expects strings (e.g., `tags: testing` vs `tags: [testing]` vs `tags:\n  - testing`). The validator should coerce, not reject. Only structural impossibilities (title is a nested object) are errors.

- **Link resolution is repo-scoped.** A lesson in repo A referencing `./other-lesson.md` can only link to lessons from repo A's harvest. Cross-repo references don't exist at the source level — they're a hub-level concern handled by the renderer, not the validator.

## Examples

### Validation Severity Model

```python
class Severity(Enum):
    ERROR = "error"    # Build must fail
    WARN = "warning"   # Report but continue

RULES = [
    # ERROR: data integrity
    Rule("id_unique",      Severity.ERROR, "Lesson IDs must be unique across all repos"),
    Rule("content_exists", Severity.ERROR, "Lesson must have non-empty content"),
    Rule("file_readable",  Severity.ERROR, "Source file must be parseable as markdown+frontmatter"),
    Rule("json_schema",    Severity.ERROR, "Generated JSON must validate against schema"),
    
    # WARN: content quality
    Rule("has_summary",    Severity.WARN, "Lesson should have a summary field"),
    Rule("has_date",       Severity.WARN, "Lesson should have a date field"),
    Rule("has_tags",       Severity.WARN, "Lesson should have at least one tag"),
    Rule("min_length",     Severity.WARN, "Lesson content should be >100 characters"),
    Rule("known_type",     Severity.WARN, "lesson_type should be a known value"),
]
```

### Slug Collision Detection

| Repo | Filename | Generated ID | Collision? |
|------|----------|-------------|------------|
| hub | `static-search.md` | `hub-static-search` | No |
| lab | `static-search.md` | `lab-static-search` | No (different repo prefix) |
| hub | `static_search.md` | `hub-static-search` | YES (same slug after normalization) |

### Frontmatter Coercion

```python
def coerce_to_string(value):
    """Source YAML may produce unexpected types."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return ""
    return str(value)

# Apply to fields that must be strings in output
lesson["summary"] = coerce_to_string(raw.get("summary"))
lesson["phase"] = coerce_to_string(raw.get("phase"))
```

### Pipeline Integration

```
harvest_lessons.py (clone + parse)
        │
        ▼
validate_lessons.py (run rules)
        │
        ├── Any ERROR? → Exit 1, print errors, stop build
        │
        └── Only WARNs? → Print warnings, continue
                │
                ▼
        build_corpus.py (generate RAG chunks)
                │
                ▼
        astro build (render site)
```

## Applicability

This pattern applies to any content aggregation pipeline where:
- Multiple sources contribute content (documentation hubs, knowledge bases, blog networks)
- Content undergoes ID generation or slug derivation that could collide
- The build output has strict schema requirements even if inputs are loose
- Different quality problems have different severity to the end user

It is less necessary for:
- Single-source pipelines (no collision risk, simpler validation)
- Systems where source repos control their own publishing (validation belongs there)
- Real-time content (validation latency matters more than completeness)

## Related Lessons

- [Validation Severity Model](validation-severity-model.md) — the ERROR/WARN framework in depth
- [Harvester Design Decisions](harvester-design-decisions.md) — how the pipeline handles multiple repos
- [Test Pyramid for Static Sites](test-pyramid-for-static-sites.md) — where pipeline validation fits in the test pyramid

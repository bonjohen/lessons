# Lesson Schema

This document defines all frontmatter fields, controlled vocabularies, ID generation rules, and tag normalization rules for lesson documents.

## Frontmatter Fields

| Field | Type | Requirement | Description |
|-------|------|-------------|-------------|
| `title` | string | Required (after normalization) | Lesson title. Inferred from first H1 or filename if missing. |
| `summary` | string | Recommended | One-line summary. Warning if missing. |
| `date` | date | Recommended | ISO format (YYYY-MM-DD). Warning if missing. |
| `updated` | date | Optional | Last update date. |
| `phase` | string | Recommended | Project phase. Warning if missing. |
| `lesson_type` | string | Recommended | Must be from controlled vocabulary. Warning if missing or unknown. |
| `status` | string | Optional | Defaults to `active`. Must be from controlled vocabulary. |
| `tags` | list | Recommended | List of tag strings. Warning if missing. |
| `slug` | string | Optional | Explicit slug override for ID generation. |
| `source_files` | list | Optional | Related source file paths. |
| `related_prs` | list | Optional | Related pull request references. |
| `related_issues` | list | Optional | Related issue references. |
| `related_commits` | list | Optional | Related commit hashes. |
| `audience` | list | Optional | Target audience labels. |

## Controlled Vocabularies

### `lesson_type`

| Value | Description |
|-------|-------------|
| `architecture` | System design, component structure |
| `implementation` | Coding patterns, algorithms |
| `testing` | Test strategies, coverage |
| `deployment` | CI/CD, release processes |
| `debugging` | Bug investigation, root cause analysis |
| `data-design` | Data models, schemas, storage |
| `ai-assisted-development` | AI tools, prompting, agent workflows |
| `documentation` | Docs strategy, writing patterns |
| `maintenance` | Upgrades, migrations, tech debt |
| `process` | Team practices, workflows |
| `other` | Anything not covered above |

### `status`

| Value | Description |
|-------|-------------|
| `active` | Current and relevant (default) |
| `draft` | Work in progress |
| `superseded` | Replaced by a newer lesson |
| `deprecated` | No longer applicable |

## ID Generation

Lesson IDs are globally unique, formatted as `{repo_id}-{lesson_slug}`.

### Slug Priority

1. Explicit `slug` frontmatter field
2. File path relative to lessons directory (preserves subdirectory structure)
3. Normalized title (fallback)

### Slug Rules

- Lowercase
- Kebab-case (hyphens between words)
- No spaces or unsafe URL characters
- Subdirectory paths are included (e.g., `block1/index.md` → `block1-index`)

### Examples

| File | Slug | ID |
|------|------|----|
| `docs/lessons/schema-drift.md` | `schema-drift` | `myrepo-schema-drift` |
| `docs/lessons/block1/setup.md` | `block1-setup` | `myrepo-block1-setup` |
| Frontmatter `slug: custom-name` | `custom-name` | `myrepo-custom-name` |

## Tag Normalization

Tags are normalized during harvest:

| Rule | Example |
|------|---------|
| Lowercase | `GitHub Actions` → `github-actions` |
| Trim whitespace | `  python  ` → `python` |
| Spaces to hyphens | `Schema Design` → `schema-design` |
| Remove duplicates | `[python, Python]` → `[python]` |

## Validation Severity

### Errors (build fails)

- Empty lesson content
- Duplicate lesson IDs
- Unreadable markdown files

### Warnings (build continues)

- Missing `summary`, `date`, `tags`, `phase`, `lesson_type`
- Unknown `lesson_type` or `status` value
- Non-normalized tag casing
- Short content (< 50 words)
- Title inferred from filename

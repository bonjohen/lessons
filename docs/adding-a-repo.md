# Adding a Source Repository

Follow these steps to add a new source repository to Lessons Hub.

## Prerequisites

- The repository is on GitHub (public or private)
- Lessons are stored as markdown files under a `docs/lessons/` directory
- Each lesson is a standalone `.md` file with optional YAML frontmatter

## Step 1: Edit `data/repos.yml`

Add an entry under the `repos:` list:

```yaml
  - id: my-project
    name: My Project
    owner: github-username
    repo: repository-name
    branch: main
    lessons_path: docs/lessons
    project_url: https://github.com/username/repository-name
    enabled: true
```

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Stable lowercase kebab-case identifier | `my-project` |
| `name` | Display name | `My Project` |
| `owner` | GitHub owner or organization | `bonjohen` |
| `repo` | GitHub repository name | `my-project` |
| `branch` | Branch to harvest from | `main` |
| `lessons_path` | Relative path to lesson folder | `docs/lessons` |

### Optional Fields

| Field | Description | Default |
|-------|-------------|---------|
| `project_url` | Public project URL | Generated from owner/repo |
| `enabled` | Whether to harvest this repo | `true` |

## Step 2: Test Locally

```bash
npm run harvest
```

Verify:
- Repo clones successfully
- Lessons are discovered
- No errors (warnings for missing metadata are expected)

## Step 3: Validate

```bash
npm run validate:lessons
```

Check for:
- No duplicate lesson IDs with existing repos
- No hard errors

## Step 4: Build and Preview

```bash
npm run build:full
npm run preview
```

Browse to verify lessons appear on the site.

## Step 5: Commit

```bash
git add data/repos.yml
git commit -m "Add my-project to lesson sources"
```

The GitHub Actions workflow will automatically rebuild and deploy on push to `main`.

## Private Repositories

For private repos, set the `LESSONS_REPO_TOKEN` secret in the Lessons Hub repository settings. The harvester uses this token for authenticated `git clone` operations. Token values are never logged or exposed.

## Subdirectory Lessons

Lessons in subdirectories (e.g., `docs/lessons/phase1/*.md`) are automatically discovered. The subdirectory path is included in the lesson slug to prevent ID collisions.

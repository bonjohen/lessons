---
title: Public and Private Repo Harvesting
summary: A multi-repo content pipeline must handle mixed visibility gracefully — token scope, clone failure semantics, and local fallbacks all need explicit design.
date: 2026-05-11
phase: deployment
lesson_type: architecture
status: active
tags: [harvesting, github, authentication, private-repos, ci-cd, error-handling]
---

# Public and Private Repo Harvesting

## The Lesson

When a content pipeline clones from multiple GitHub repositories, mixing public and private repos introduces three failure modes that don't exist in a public-only setup: token scope gaps, clone failures that abort the entire pipeline, and local development without credentials. Each needs an explicit design choice, not a workaround.

## Context

Lessons Hub harvests markdown lesson files from multiple GitHub repositories into a single static site. The harvester reads a YAML registry that lists every source repo — each entry specifies an ID, GitHub owner/repo, branch, and the path where lessons live (e.g. `docs/lessons`). An `enabled: true/false` flag controls whether the repo is included in the harvest. The harvester clones each enabled repo to a temp directory, parses lesson files, and generates JSON for the Astro build. In CI, `LESSONS_REPO_TOKEN` is injected from a GitHub secret to authenticate clones. Locally, the developer may or may not have the token set.

The pipeline started with only public repos owned by the same user. Adding a private repo (MoreLessons) immediately broke the CI build because the harvester treats any clone failure as a fatal error.

## What Happened

1. A new private repo (`MoreLessons`) was added to the registry with `enabled: true`.
2. The commit was pushed. CI ran the harvest step.
3. The harvester attempted to clone `MoreLessons`. The `LESSONS_REPO_TOKEN` secret existed but its scope did not include the new repo (fine-grained tokens are scoped per-repository).
4. `git clone` failed with `could not read Username for 'https://github.com'` — the same error you'd get for a nonexistent repo, giving no hint that the real issue was token scope.
5. The harvester logged this as an `[ERROR]`, and because any error during harvest triggers `FATAL ... Aborting`, the entire pipeline failed — no lessons from any repo were published.
6. The fix was to set `enabled: false` on the new repo until the token and repo were both ready, then push a second commit.

## Key Insights

- **Token scope is invisible at clone time.** A fine-grained GitHub PAT that lacks access to a repo produces the same error as a missing repo or bad credentials. You cannot distinguish "repo doesn't exist," "token can't see this repo," and "no token at all" from the git error message alone. The only way to know is to check the token's configuration in GitHub Settings → Developer settings → Fine-grained tokens.

- **Fatal-on-any-error is too aggressive for mixed registries.** When the registry mixes public repos, private repos, and repos that may not exist yet, a single clone failure should not abort the entire harvest. The harvester currently logs an error and continues cloning, but then checks the error count and aborts before generating output. A better design would distinguish "clone failed" (warning, skip this repo) from "parse failed" (error, data integrity risk).

- **`enabled: false` is a sufficient gate for repos not yet ready.** The simplest solution is a registry-level flag. A repo with `enabled: false` is skipped entirely — no clone attempt, no error, no risk. This is better than removing the entry because the configuration (owner, repo, branch, lessons_path) is preserved for when the repo is ready.

- **Local development needs a fallback path.** Developers who don't have `LESSONS_REPO_TOKEN` set locally can still harvest public repos — the harvester falls back to unauthenticated HTTPS. But private repos will silently fail. The harvester should warn (not error) when a known-private repo can't be cloned without a token, so developers know what they're missing without the build breaking.

- **Token management is a one-time setup with ongoing maintenance.** Adding a private repo to the pipeline requires: (1) creating or updating a fine-grained PAT with read access to the new repo, (2) updating the `LESSONS_REPO_TOKEN` secret in the hub repo's GitHub settings, (3) optionally setting the token locally for `npm run harvest`. Each new private repo repeats step 1-2.

## Recommendations

1. **Before enabling a private repo**, verify that `LESSONS_REPO_TOKEN` has read access to it. For fine-grained tokens: GitHub Settings → Developer settings → Fine-grained personal access tokens → edit the token → add the repo under "Repository access."

2. **Add new repos with `enabled: false`** until the repo exists on GitHub, has content at the configured `lessons_path`, and the token covers it. Flip to `enabled: true` only after confirming all three.

3. **Consider downgrading clone failures from error to warning** in the harvester so that one unreachable repo doesn't block publishing lessons from the other five. Reserve errors for data integrity issues (duplicate IDs, corrupt frontmatter, empty content).

4. **For local development**, set `LESSONS_REPO_TOKEN` in your shell profile or a `.env` file (never committed) so private repos are harvested locally too. Without it, only public repos will appear in your local build.

## Applicability

This applies to any CI pipeline that aggregates content from multiple repositories with mixed visibility — documentation hubs, monorepo federation tools, multi-repo changelog generators, or any system where `git clone` is a build step. The same token-scope and error-severity considerations apply whenever you mix public and private sources in a single pipeline.

## Related Lessons

- [Harvester Design Decisions](harvester-design-decisions.md) — Covers the overall harvester architecture; this lesson extends it with private-repo considerations
- [GitHub Pages Build Pipeline](github-pages-build-pipeline.md) — The CI workflow where token injection and clone failures surface
- [Validation Severity Model](validation-severity-model.md) — The warning-vs-error distinction that should apply to clone failures

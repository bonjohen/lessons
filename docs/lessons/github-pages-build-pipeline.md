---
title: GitHub Pages Build Pipeline
summary: Designing a GitHub Actions workflow that harvests, validates, builds, indexes, and deploys a static site.
date: 2026-05-08
phase: deployment
lesson_type: deployment
status: active
tags: [github-actions, github-pages, ci-cd, deployment]
---

## Context

Lessons Hub needs automated deployment: clone source repos, run Python harvesting, run Node build, generate search index, and deploy to GitHub Pages. The workflow must handle both public repos (no auth) and optional private repos (token auth).

## Decision

Single workflow file (`.github/workflows/build-deploy.yml`) with two jobs:

1. **Build job**: checkout → setup Python 3.11 → setup Node 20 → install deps → harvest (with optional `LESSONS_REPO_TOKEN`) → validate → Astro build → Pagefind index → upload Pages artifact
2. **Deploy job**: deploy Pages artifact using `actions/deploy-pages@v4`

Triggers: push to `main`, manual dispatch, daily cron (6:00 UTC).

### Token Handling

The `LESSONS_REPO_TOKEN` secret is optional. For public repos, the harvester works without it. When present, it's injected as an environment variable — the harvester uses it for authenticated `git clone` URLs but never logs or prints the token value.

### Permissions

The workflow sets `pages: write` and `id-token: write` at the top level, required for GitHub Pages OIDC deployment.

## Key Takeaway

Keep the CI/CD workflow linear and explicit — each step's purpose should be obvious from the step name. Optional secrets (like repo tokens) should degrade gracefully when absent.

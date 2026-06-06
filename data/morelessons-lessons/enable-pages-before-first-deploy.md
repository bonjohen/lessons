---
title: "Enable GitHub Pages Before First Deploy"
summary: "A GitHub Actions workflow that deploys to GitHub Pages will fail on the first run if Pages is not enabled in the repository settings. The workflow will build successfully but the deploy step returns a 404 — \"Ensure GitHub Pages has been enabled.\" This is a configuration prerequisite, not a code bug,..."
date: 2026-05-13
lesson_type: deployment
tags: [deployment, api, pipeline, python, astro]
---
# Enable GitHub Pages Before First Deploy

## The Lesson

A GitHub Actions workflow that deploys to GitHub Pages will fail on the first run if Pages is not enabled in the repository settings. The workflow will build successfully but the deploy step returns a 404 — "Ensure GitHub Pages has been enabled." This is a configuration prerequisite, not a code bug, and it's easy to miss because the build job passes.

## Context

A new repository was set up with a GitHub Actions workflow (`build-deploy.yml`) that built an Astro static site and deployed it to GitHub Pages using `actions/deploy-pages@v4`. The workflow was committed during Phase 6 of the implementation plan. The first push to `main` triggered the workflow. The build job completed in 28 seconds, producing the static site artifact. The deploy job failed in 3 seconds.

## What Happened

1. The CI workflow was written with two jobs: `build` (checkout, setup, install, build, upload artifact) and `deploy` (download artifact, deploy to Pages). The workflow permissions included `pages: write` and `id-token: write`.
2. The first push to `main` triggered the workflow. The `build` job succeeded — all pipeline steps (scan, validate, corpus, build, index) completed, and the `dist/` artifact was uploaded.
3. The `deploy` job failed immediately: `Error: Failed to create deployment (status: 404)... Ensure GitHub Pages has been enabled`.
4. The fix was a single API call: `gh api repos/owner/repo/pages -X POST -f build_type=workflow`. This enabled Pages with "GitHub Actions" as the source.
5. Re-running just the deploy job succeeded. The site was live within 10 seconds.
6. The total time lost was approximately 2 minutes — not catastrophic, but entirely preventable. In a team setting, the failed deploy would have sent a notification and created a red badge on `main`.

## Key Insights

- **Build success does not imply deploy success.** The build job and deploy job have completely different prerequisites. The build job needs Node, Python, and the project's dependencies. The deploy job needs the Pages feature enabled in repo settings. Testing the build locally tells you nothing about whether the deploy will work.
- **First deploys always have configuration prerequisites.** This is true beyond GitHub Pages: first deploys to AWS need IAM roles, first deploys to Vercel need project linking, first deploys to Netlify need site creation. The workflow file describes *what to do* but can't enforce *what must exist first*. Document these prerequisites in a setup checklist.
- **`gh api` can enable Pages programmatically.** The command `gh api repos/{owner}/{repo}/pages -X POST -f build_type=workflow` enables Pages without visiting the web UI. This can be scripted into a project setup script or documented in the README.
- **Partial job re-runs save time.** GitHub Actions supports re-running only the failed job (`gh run rerun <id> --job <job-id>`) rather than the entire workflow. When the build is correct and only the deploy failed due to configuration, re-running just the deploy job avoids repeating the build.

## Applicability

This applies specifically to GitHub Pages deployments using GitHub Actions with `actions/deploy-pages`. It also applies generally to any CI/CD pipeline deploying to a service that requires one-time setup: cloud provider accounts, DNS records, API keys in secrets, environment configurations. It does NOT apply to self-hosted deployments where the target infrastructure is provisioned alongside the CI pipeline.

## Related Lessons

- [Base URL Misconfiguration Breaks Subdirectory Deploys](base-url-subdirectory-deploys.md) — the other first-deploy failure in this project; both are "works locally, fails on deploy" issues with different root causes

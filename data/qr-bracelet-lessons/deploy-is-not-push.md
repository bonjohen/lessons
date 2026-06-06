---
title: "Deploying is Not Pushing"
summary: "In a serverless workflow where `wrangler deploy` pushes code directly to production, deployment is decoupled from git. This means there's no CI/CD pipeline gating production changes — the developer must impose their own discipline. Treat every production deploy like a `git push --force`: require exp..."
date: 2026-06-06
lesson_type: deployment
tags: [cloudflare, serverless, deployment, data-modeling, devops]
---
# Deploying is Not Pushing

## The Lesson

In a serverless workflow where `wrangler deploy` pushes code directly to production, deployment is decoupled from git. This means there's no CI/CD pipeline gating production changes — the developer must impose their own discipline. Treat every production deploy like a `git push --force`: require explicit authorization each time, and never assume prior approval carries forward.

## Context

MyReachBand deploys to Cloudflare Workers via `wrangler deploy`. There's no GitHub Actions pipeline, no staging gate, no pull request review. The command bundles JavaScript files and uploads them to production in 3 seconds. Git push to GitHub is for backup and collaboration — it has no effect on the live site.

## What Happened

1. During rapid development, deployed to production after every change to test on the live domain.
2. Owner requested that production deploys require explicit permission — same as `git push`.
3. Continued deploying to production automatically after commits, treating "deploy" as part of the development loop.
4. Owner caught an unauthorized production deploy and flagged it. The change was harmless (adding "Placeholder image -" text), but the principle violation was the issue.
5. Established the rule: production deploys are single-use authorizations. "Deploy to production" in one message does not authorize the next deploy.
6. Set up a dev environment (`dev.myreachband.com`) so all testing happens there. Production only updates on explicit "deploy to prod" instructions.

## Key Insights

- **No pipeline means no guardrails.** In a CI/CD workflow, the pipeline is the gate. In a `wrangler deploy` workflow, discipline is the gate. If you don't impose structure, every `wrangler deploy` is a production push.
- **Dev environments are essential.** Without `wrangler deploy -e dev`, the only way to test is on production. A dev environment costs nothing (free tier) and prevents accidental production changes.
- **Authorization is single-use.** "Deploy to production" means this one time. Not "deploy whenever you're done" or "deploy after every commit." Each deploy needs fresh permission.
- **The harmless change is the most dangerous.** A typo fix deployed without permission establishes a precedent. The next unauthorized deploy might break authentication or corrupt data.
- **Document the rule in the project.** Add deployment rules to `CLAUDE.md` or equivalent project docs. The rule should be visible to anyone (human or AI) working on the project.

## Applicability

This applies to any workflow where deployment is a single CLI command: `wrangler deploy`, `vercel --prod`, `netlify deploy --prod`, `fly deploy`. It does NOT apply when CI/CD pipelines gate production — in those cases, the pipeline enforces the discipline automatically.

## Related Lessons

- [Wrangler CLI](wrangler-cli.md) — the tool that makes one-command deploys possible
- [Dev-Prod Schema Parity](dev-prod-schema-parity.md) — why the dev environment must match production

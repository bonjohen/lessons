---
title: "GitHub Pages Deployment Configuration"
summary: "GitHub Pages deployment with static site generators has three independently-failing configuration points — workflow file location, CNAME record, and site URL in the build config — and all three must be correct simultaneously. A deploy that \"almost works\" is usually missing exactly one of these."
date: 2026-05-24
lesson_type: deployment
tags: [cloudflare, deployment, pipeline, astro]
---
# GitHub Pages Deployment Configuration

## The Lesson

GitHub Pages deployment with static site generators has three independently-failing configuration points — workflow file location, CNAME record, and site URL in the build config — and all three must be correct simultaneously. A deploy that "almost works" is usually missing exactly one of these.

## Context

An Astro 5 static site was being deployed to GitHub Pages with a custom domain (`data-readiness.johnboen.com`). The project used a GitHub Actions workflow for building and deploying. The site structure placed the Astro project in a subdirectory (`github/_hub/`) rather than at the repository root, which created a mismatch between where files were expected and where they actually lived.

## What Happened

1. The initial deploy workflow was placed at `github/_hub/.github/workflows/deploy.yml` — inside the Astro project's directory structure, mirroring a convention from development.
2. GitHub Actions only discovers workflows at `.github/workflows/` relative to the repository root. The workflow never triggered because GitHub couldn't find it.
3. The CNAME file in `public/` contained a placeholder or incorrect domain, causing the custom domain configuration to fail even after the workflow was moved.
4. The `site` field in `astro.config.mjs` pointed to the wrong URL, which caused Astro to generate incorrect absolute URLs for canonical links, sitemaps, and asset paths.
5. The fix addressed all three in one commit: moved the workflow to `.github/workflows/deploy.yml` (repo root), corrected the CNAME to `data-readiness.johnboen.com`, and updated `astro.config.mjs` with the correct site URL.

## Key Insights

- **GitHub Actions workflow discovery is repo-root-relative only.** Workflows must be at `<repo-root>/.github/workflows/`. This is easy to forget when the application lives in a subdirectory. No amount of configuration can make GitHub discover workflows in nested directories.
- **CNAME, site URL, and workflow are a triple dependency.** All three must agree: the CNAME tells GitHub which domain to serve, the site URL tells the build tool what base URL to use for generated links, and the workflow connects the two by building and deploying. If any one is wrong, the deploy breaks in a different way (no trigger, wrong domain, broken links).
- **Subdirectory project layouts add a layer of indirection.** When the Astro project isn't at the repo root, every path reference (workflow working directory, CNAME location relative to build output, base path) needs explicit configuration. Monorepo-style layouts trade organizational clarity for deployment complexity.
- **Test deploy configuration before building content.** The first thing to verify after scaffolding is "can I deploy an empty site to the correct domain?" Content and components are wasted work if the deploy pipeline doesn't function.

## Applicability

Applies to any static site deployed to GitHub Pages, especially with custom domains and subdirectory project layouts. The specific triple-dependency pattern (CI location, domain config, build URL) also applies to Netlify, Vercel, and Cloudflare Pages, though the configuration files differ. Less relevant for platforms with zero-config deploys (e.g., Vercel with framework auto-detection at repo root).

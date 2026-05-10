---
title: GitHub Pages Custom Domain Setup
summary: Configuring a custom domain for GitHub Pages requires coordinating DNS, repo settings, build tool config, and deployment mode — each can silently break the others.
date: 2026-05-10
phase: deployment
lesson_type: deployment
status: active
tags: [github-pages, dns, deployment, custom-domain, astro]
---

# GitHub Pages Custom Domain Setup

## The Lesson

Custom domain setup for GitHub Pages is a four-layer coordination problem: DNS records, repository Pages settings, build tool configuration, and deployment mode. A mistake at any layer produces a 404 with no obvious error message. Understanding which layer controls what prevents the silent failures that make this setup frustrating.

## Context

Lessons Hub is a static site built with Astro and deployed to GitHub Pages via GitHub Actions (`actions/deploy-pages@v4`). The site originally lived at `bonjohen.github.io/lessons/` (subpath deployment). Moving it to `lessons.johnboen.com` (custom subdomain at root) required changes at every layer of the stack.

## What Happened

1. **DNS configured correctly.** Added a CNAME record: `lessons.johnboen.com` → `bonjohen.github.io`. GitHub's DNS check passed immediately.
2. **Custom domain set in GitHub Settings.** Entered `lessons.johnboen.com` in Settings → Pages → Custom domain. GitHub auto-created a `CNAME` file at the repository root containing `lessons.johnboen.com`.
3. **First breakage: all navigation links 404'd.** The Astro config still had `base: '/lessons'`, which prefixed every internal link with `/lessons/`. On the custom domain (serving from `/`), those paths didn't exist. Fixed by changing `base` to `'/'` and `site` to `'https://lessons.johnboen.com'`.
4. **Second breakage: CNAME file conflict.** Astro copies `public/` into `dist/` at build time, so the correct location for the CNAME file is `public/CNAME`. But GitHub had auto-created a competing `CNAME` at the repo root. During a merge, the root CNAME was deleted — which also cleared the custom domain setting in GitHub Pages, resetting `cname` to `null`.
5. **Third breakage: deployment mode mismatch.** After the CNAME was cleared, GitHub Pages reverted to `build_type: "legacy"` (deploy from branch). The repo uses `actions/deploy-pages@v4` (Actions-based deployment), which requires `build_type: "workflow"`. The site built and deployed successfully, but GitHub wasn't serving the artifact.
6. **Resolution via API.** Fixed both issues with a single API call:
   ```bash
   gh api -X PUT repos/bonjohen/lessons/pages \
     -f build_type=workflow \
     -f cname=lessons.johnboen.com
   ```

## Key Insights

- **GitHub auto-creates a root CNAME file** when you set a custom domain in the UI. If your build tool manages its own CNAME file (Astro uses `public/CNAME`), the auto-created file conflicts. Deleting the auto-created file can clear the custom domain setting entirely.

- **`build_type` must match your deployment method.** Repos deploying via `actions/deploy-pages` need `build_type: "workflow"`. Repos deploying from a branch need `build_type: "legacy"`. A mismatch produces a successful build but a 404 on the site, with no error in the Actions logs.

- **`base` path must change when the serving root changes.** Moving from `username.github.io/repo/` to `custom.domain.com` means `base` goes from `'/repo'` to `'/'`. Every internal link, asset path, and navigation URL is affected. This is a build-time setting — you must rebuild and redeploy after changing it.

- **The Pages API is the fastest diagnostic tool.** `gh api repos/{owner}/{repo}/pages` shows `cname`, `build_type`, `source`, and `status` in one call. When the site 404s, check this before anything else — the answer is usually visible in the API response.

- **`public/CNAME` is the durable solution for Astro.** Astro copies `public/` contents into `dist/` verbatim. Placing the CNAME file there ensures it survives every build and deploy, unlike a root CNAME file that gets overwritten by the build output.

## Examples

### Diagnosing a 404

```bash
# Check Pages config — look at cname, build_type, and status
gh api repos/bonjohen/lessons/pages

# Response showing the problem:
# { "cname": null, "build_type": "legacy", "status": "built" }
#   ↑ domain cleared    ↑ wrong for Actions deploys
```

### Fixing via API

```bash
# Re-set custom domain and correct build type in one call
gh api -X PUT repos/bonjohen/lessons/pages \
  -f build_type=workflow \
  -f cname=lessons.johnboen.com
```

### Astro config for custom domain

```javascript
// Before (subpath deployment)
export default defineConfig({
  output: 'static',
  site: 'https://bonjohen.github.io',
  base: '/lessons',
});

// After (custom domain at root)
export default defineConfig({
  output: 'static',
  site: 'https://lessons.johnboen.com',
  base: '/',
});
```

## Applicability

This applies to any static site generator (Astro, Next.js, Hugo, Jekyll) deployed to GitHub Pages with a custom domain. The specific file location for CNAME varies by tool (`public/CNAME` for Astro/Next.js, root `CNAME` for Jekyll since Jekyll doesn't overwrite it), but the coordination problem is the same. The `build_type` issue is specific to repos using GitHub Actions deployment rather than branch-based deployment.

## Related Lessons

- [GitHub Pages Build Pipeline](github-pages-build-pipeline.md) — the deployment workflow this lesson's custom domain sits on top of
- [Phased Multi-Cloud Infrastructure](phased-multi-cloud-infrastructure.md) — the broader multi-deployment context where custom domains become one of several serving endpoints

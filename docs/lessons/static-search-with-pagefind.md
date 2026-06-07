---
title: Static Search with Pagefind
summary: Integrating Pagefind for full-text search on a static site with no backend.
date: 2026-05-08
phase: implementation
lesson_type: implementation
status: active
tags: [pagefind, search, static-site, astro]
---

# Static Search with Pagefind

## The Lesson

Static sites don't need a search backend. Pagefind indexes your built HTML at build time and generates a client-side search index that runs entirely in the browser. The integration is a dev dependency, one post-build command, and a UI component — no server, no API, no database.

## Context

A lessons library with 200+ pages needed full-text search. The site is fully static (Astro, deployed to GitHub Pages) with no backend server for search queries. Options included Algolia (external service, API key management, free tier limits), Lunr.js (requires building a JSON index manually), and Pagefind (indexes HTML output directly, generates its own UI).

## What Happened

1. Installed Pagefind as a dev dependency and added a post-build indexing step. Pagefind reads the `dist/` directory (Astro's build output) and creates a search index from the rendered HTML.
2. Without scoping, Pagefind indexed everything — navigation links, footers, sidebar content, boilerplate. Search results returned noise from repeated layout text.
3. Added `data-pagefind-body` to the content wrapper on lesson detail pages. Pagefind only indexes elements inside this attribute, filtering out layout chrome.
4. Integrated Pagefind's prebuilt UI component into a search page. The UI handles input, debouncing, result display, and highlighting with zero custom code.
5. The index regenerates on every build, so new or updated lessons are searchable as soon as the site deploys. No reindexing API calls, no webhook triggers.

## Key Insights

- **Post-build indexing eliminates sync problems.** Because Pagefind reads the same HTML that users see, the search index is always in sync with the deployed content. There's no separate content pipeline to keep up to date.

- **Scoping with `data-pagefind-body` is essential.** Without it, navigation links and footer text dominate search results. One attribute on the right container element is the difference between useful search and noise.

- **Zero operational cost matters for small projects.** Algolia's free tier works until it doesn't — usage spikes, API key rotation, and vendor dependency add ongoing maintenance. Pagefind has no ongoing cost because there's nothing to maintain beyond the build step.

- **The prebuilt UI is good enough.** Custom search UIs are tempting but rarely justify the effort for content sites. Pagefind's default UI handles keyboard navigation, result previews, and search highlighting. Customize with CSS, not a rewrite.

## Implementation Guide

### Step 1: Install and configure Pagefind

Add Pagefind as a dev dependency and create an indexing script that runs after your static site build:

```bash
npm install --save-dev pagefind
```

Add a build script to `package.json` that runs Pagefind after the static site build completes:

```json
{
  "scripts": {
    "build": "astro build",
    "index": "npx pagefind --site dist",
    "build:full": "npm run build && npm run index"
  }
}
```

The `--site` flag points to your build output directory (`dist` for Astro, `build` for Create React App, `out` for Next.js static export, `_site` for Jekyll).

### Step 2: Scope the index to meaningful content

Add the `data-pagefind-body` attribute to the content wrapper on pages you want indexed. Without this, Pagefind indexes everything including navigation, headers, and footers:

```html
<!-- In your page layout or template -->
<main data-pagefind-body>
  <h1>{title}</h1>
  <div class="content">
    <!-- Page content here — this is what gets indexed -->
  </div>
</main>

<!-- Navigation, footer, sidebar — NOT indexed -->
<nav>...</nav>
<footer>...</footer>
```

You can also exclude specific elements within the body using `data-pagefind-ignore`:

```html
<main data-pagefind-body>
  <div data-pagefind-ignore>
    <!-- This section won't be indexed (e.g., auto-generated table of contents) -->
  </div>
  <article>...</article>
</main>
```

### Step 3: Add the search UI

Create a search page and include Pagefind's prebuilt UI. Pagefind generates its assets in `dist/pagefind/` during indexing:

```html
<link href="/pagefind/pagefind-ui.css" rel="stylesheet">
<script src="/pagefind/pagefind-ui.js"></script>

<div id="search"></div>

<script>
  window.addEventListener("DOMContentLoaded", () => {
    new PagefindUI({
      element: "#search",
      showSubResults: true,    // Show matching subsections
      showImages: false,       // Disable image thumbnails
    });
  });
</script>
```

For Astro, wrap this in a component with `is:inline` scripts or use a framework component with `client:load`.

### Step 4: Add indexing to CI

Ensure your CI/CD pipeline runs the indexing step after the build. In a GitHub Actions workflow:

```yaml
- name: Build site
  run: npm run build

- name: Index for search
  run: npm run index

- name: Deploy
  uses: actions/deploy-pages@v4
```

The `dist/pagefind/` directory must be included in the deployed output. Since Pagefind writes directly into the build output directory, this happens automatically.

## Applicability

This pattern works for any static site with moderate content volume (up to several thousand pages). Pagefind handles sites with tens of thousands of pages, but search index size grows with content — very large sites may want to consider server-side search.

It does NOT apply when:
- You need faceted search, fuzzy matching, or semantic search (use a search service)
- Content is generated dynamically and not available at build time
- You need real-time indexing (content changes between builds)

## Related Lessons

- [GitHub Pages Build Pipeline](github-pages-build-pipeline.md) — the CI workflow where the indexing step runs

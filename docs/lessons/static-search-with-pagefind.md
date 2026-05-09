---
title: Static Search with Pagefind
summary: Integrating Pagefind for full-text search on a static site with no backend.
date: 2026-05-08
phase: implementation
lesson_type: implementation
status: active
tags: [pagefind, search, static-site, astro]
---

## Context

Lessons Hub is a fully static site deployed to GitHub Pages. Users need to search lessons by title and body text. No backend is available.

## Decision

Used Pagefind — a static search library that indexes the built HTML and generates a client-side search index. The integration is minimal:

1. Install: `npm install --save-dev pagefind`
2. Index: `npx pagefind --site dist` (runs after Astro build)
3. UI: Include Pagefind's CSS/JS and initialize `PagefindUI` in a component
4. Scope: Add `data-pagefind-body` to lesson detail pages so only lesson content is indexed (not navigation, footers, etc.)

## Outcome

Pagefind indexed 90 pages with 5091 words in under 0.5 seconds. The search UI is functional with zero backend infrastructure. The index is regenerated on every build, so new lessons are immediately searchable.

## Key Takeaway

For static sites with moderate content volume, Pagefind provides excellent search with zero operational cost. The `data-pagefind-body` attribute is critical for scoping the index to meaningful content.

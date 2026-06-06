---
title: "Relative Link Fragility in Multi-Section Static Sites"
summary: "Relative links in templated multi-section static sites break silently when page nesting depth varies. Use a systematic link strategy — either always-absolute paths from the site root, or a helper that resolves relative to the current topic — rather than hand-coding relative hrefs in content files."
date: 2026-06-06
lesson_type: implementation
tags: [astro]
---
# Relative Link Fragility in Multi-Section Static Sites

## The Lesson

Relative links in templated multi-section static sites break silently when page nesting depth varies. Use a systematic link strategy — either always-absolute paths from the site root, or a helper that resolves relative to the current topic — rather than hand-coding relative hrefs in content files.

## Context

A static site served 12 regulatory topics, each with 9 pages at paths like `/soc2/`, `/soc2/about/`, `/soc2/readiness-process/`. Content was authored in MDX files with relative links between sibling pages (e.g., the about page linking to services). The same MDX template was used across all 12 topics, so a link error in the template propagated to all topics simultaneously.

## What Happened

1. MDX content files for each topic's about page used `href="services"` to link to the services page, and readiness-process pages used `href="about"` to link back.
2. These relative links resolved correctly when viewing `/soc2/about` (resolving to `/soc2/services`), but the actual URL structure used trailing slashes (`/soc2/about/`), causing the browser to resolve `href="services"` as `/soc2/about/services` — a 404.
3. The bug affected all 12 topics (24 broken links total) because the content was templated.
4. The fix changed all relative links to use `../` prefix (`../services`, `../about`) so they resolve correctly regardless of trailing slash behavior.
5. Additionally, the Nav component needed topic-aware branding — it showed a generic "Data Readiness" label on topic pages instead of "Data Readiness / SOC 2". The fix used Astro's `Astro.url.pathname` to detect the current topic and render a breadcrumb-style brand.

## Key Insights

- **Trailing slashes change relative link resolution.** `/soc2/about` and `/soc2/about/` are different base URLs for relative resolution. Most static site generators default to directory-style URLs with trailing slashes, which means `href="sibling"` resolves as a child, not a sibling. This catches everyone once.
- **Templated content multiplies link bugs.** One wrong `href` in a shared MDX template produces N broken links (one per topic). The blast radius of a link error scales with the number of instances using the template.
- **Prefer explicit path patterns over mental models.** Instead of remembering "use `../` for siblings in directory-style URLs," establish a project convention: always use `../` for same-level navigation in content files, or use absolute paths from site root (`/soc2/services`).
- **Nav components in multi-section sites need section awareness.** A single Nav that shows the same brand and links on every page fails once users are deep in a topic section. The Nav needs to know which section it's in — via URL parsing, frontmatter, or props — to provide contextual branding and navigation.

## Examples

**Breaks** with trailing slash URLs:
```mdx
<!-- In /soc2/about/ -->
[View Services](services)
<!-- Resolves to /soc2/about/services → 404 -->
```

**Works** — explicit parent traversal:
```mdx
<!-- In /soc2/about/ -->
[View Services](../services)
<!-- Resolves to /soc2/services → correct -->
```

## Applicability

Applies to any static site generator (Astro, Next.js static export, Hugo, Jekyll) using directory-style URLs with trailing slashes. The problem is especially severe with content-driven sites where links live in markdown/MDX files that authors edit without seeing the rendered URL structure. Does not apply to sites using file-style URLs without trailing slashes (e.g., `/soc2/about.html`).

## Related Lessons

- [Hub Consolidation Over Per-Site Scaffolding](hub-consolidation-over-per-site-scaffolding.md) — the consolidation that created the multi-topic URL structure where these links broke

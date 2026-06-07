---
title: "MDX Scoped Styles in Astro"
summary: "Astro's scoped `<style>` blocks do not penetrate MDX `<Content />` output. Any styles that need to reach MDX-rendered HTML must live in global CSS or use `:global()` selectors. This is a framework-level constraint, not a bug to work around."
date: 2026-05-24
lesson_type: implementation
tags: [security, astro]
---
# MDX Scoped Styles in Astro

## The Lesson

Astro's scoped `<style>` blocks do not penetrate MDX `<Content />` output. Any styles that need to reach MDX-rendered HTML must live in global CSS or use `:global()` selectors. This is a framework-level constraint, not a bug to work around.

## Context

A multi-topic regulatory compliance site used Astro 5 with `@astrojs/mdx` to render content pages. Each topic's landing page was an Astro page component (`[topic]/index.astro`) that imported and rendered an MDX file via `<Content />`. The page component contained scoped `<style>` blocks for layout grids (`.value-grid`, `.service-overview-grid`, `.service-overview-card`, `.cta-section`).

## What Happened

1. Page components were built with scoped styles targeting CSS classes used inside the MDX content.
2. When rendered, the MDX content appeared unstyled — grid layouts collapsed, cards lost spacing, CTAs lost formatting.
3. Investigation revealed that Astro's scoping mechanism adds unique `data-astro-cid-*` attributes to elements in the component's own template, but `<Content />` renders its HTML outside that scope. The scoped selectors never match.
4. The fix moved all 82 lines of affected styles from the scoped `<style>` block in `[topic]/index.astro` to `global.css`, where they apply regardless of component boundaries.
5. No `:global()` wrapper was needed because the styles were already targeting class names that were globally unique to the design system.

## Key Insights

- **Scoped styles and content injection are fundamentally incompatible.** Any mechanism that injects HTML from outside the component (`<Content />`, `<slot />` with external content, dynamic HTML via `set:html`) will not receive scoped styles. This is by design, not a limitation to work around.
- **Move styles to global CSS early when you know content will be injected.** Waiting until the unstyled rendering is visible in production wastes a debug cycle. If a component's primary job is rendering external content, its styles should be global from the start.
- **Class name collisions are the real risk of global styles.** The reason Astro scopes styles is to prevent collisions. When moving to global CSS, use specific-enough class names (`.service-overview-card`, not `.card`) to avoid conflicts across the site.
- **This affects all Astro content collection rendering.** Any project using `defineCollection` + `<Content />` will hit this. It's not specific to MDX — Astro's Markdown rendering has the same boundary.

## Examples

**Breaks** — scoped style in the page component:
```astro
<!-- [topic]/index.astro -->
<Content />
<style>
  .value-grid { display: grid; grid-template-columns: repeat(3, 1fr); }
</style>
```

**Works** — style in global.css:
```css
/* global.css */
.value-grid { display: grid; grid-template-columns: repeat(3, 1fr); }
```

## Applicability

Applies to any Astro project rendering content collections, MDX files, or external HTML via `<Content />` or `set:html`. Does not apply to components that only render their own template markup — scoped styles work correctly there.

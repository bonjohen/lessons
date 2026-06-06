---
title: "Content-Driven Architecture for Regulatory Frameworks"
summary: "When multiple domains share identical page structures but differ only in subject matter, model the variation as typed content collections and render everything through shared components. The architecture's value comes from enforcing uniform structure via schemas while allowing unlimited content vari..."
date: 2026-06-06
lesson_type: implementation
tags: [data-modeling, astro]
---
# Content-Driven Architecture for Regulatory Frameworks

## The Lesson

When multiple domains share identical page structures but differ only in subject matter, model the variation as typed content collections and render everything through shared components. The architecture's value comes from enforcing uniform structure via schemas while allowing unlimited content variation.

## Context

A regulatory compliance platform needed to present 12 different data regulation frameworks (CCPA, GDPR, HIPAA, SOC 2, PCI DSS, etc.) with identical page types: landing page, explainer, readiness process, about, plus data-driven pages for controls, advisory modules, services, and tools. The total output was 111 pages (9 per topic × 12 topics + 3 hub pages). Each framework has genuinely different content — HIPAA has different controls than PCI DSS — but the structure of how that content is presented is identical.

## What Happened

1. The initial architecture defined 5 content collection schemas in Astro's `defineCollection`: controls, advisory, services, tools (data collections), and pages (MDX collection). Each schema used Zod validation to enforce structure.
2. Content was organized by topic slug: `controls/soc2/*.md`, `controls/gdpr/*.md`, etc. The slug acts as a namespace — one set of components queries by slug to render the right content.
3. A single dynamic route (`[topic]/index.astro`, `[topic]/[page].astro`) serves all 108 topic pages. The route parameter determines which content collection entries to query.
4. Topic metadata (name, slug, accent color, description) lives in `site.json` manifest files — one per topic. These are lightweight config, not content.
5. Shared components (`ControlCard`, `AdvisoryCard`, `ServiceCard`, `ToolCard`) render collection entries identically across all topics. Visual differentiation comes from topic accent colors, not structural variation.
6. Adding a new regulation topic requires: writing content markdown files matching the schemas, creating a `site.json` manifest, and nothing else. No new components, routes, or config.

## Key Insights

- **Schemas are the architecture.** The Zod schemas in `config.ts` define what a "control" or "service" looks like across all 12 frameworks. If a new regulation's controls don't fit the schema, that's a signal to examine the schema, not to create a one-off template. The schema is the contract between content authors and rendering code.
- **Topic slug as namespace eliminates routing complexity.** Instead of 12 route files or complex routing logic, one `[topic]` parameter plus content collection filtering by slug handles everything. The filesystem structure (`controls/soc2/`, `controls/gdpr/`) mirrors the URL structure (`/soc2/controls/`, `/gdpr/controls/`).
- **Manifest files bridge config and content.** `site.json` files hold per-topic metadata that isn't content (accent colors, short descriptions, ordering) but isn't framework config either. This middle layer lets topics differ in presentation without touching shared code.
- **Uniform structure surfaces content quality gaps.** When every topic has the same 9 pages, it's immediately visible when one topic has thin content. The structure acts as a checklist — missing controls or empty advisory sections stand out during review.
- **Adding a topic is O(content), not O(code).** The marginal cost of topic 13 is writing ~30 markdown files. No component changes, no route changes, no build config changes. This is the payoff of content-driven architecture.

## Applicability

Applies to any platform presenting multiple domains with shared structure: multi-product documentation sites, compliance platforms, certification prep sites, multi-brand marketing sites. Does NOT apply when domains genuinely differ in structure — if product A needs a pricing calculator and product B needs a gallery, shared templates add friction rather than value.

## Related Lessons

- [Hub Consolidation Over Per-Site Scaffolding](hub-consolidation-over-per-site-scaffolding.md) — the consolidation that moved from per-topic projects to this shared architecture
- [Prototype One Instance Before Scaling to N](prototype-one-instance-before-scaling-to-n.md) — SOC 2 as the reference implementation that validated this architecture

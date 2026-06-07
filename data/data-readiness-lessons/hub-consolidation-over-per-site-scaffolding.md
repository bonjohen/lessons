---
title: "Hub Consolidation Over Per-Site Scaffolding"
summary: "When building a platform that serves N variants of the same structure, start with a single consolidated site that treats variation as data, not as separate projects. Late consolidation — after scaffolding N separate sites — is expensive and produces a massive, risky changeset."
date: 2026-05-24
lesson_type: implementation
tags: [deployment, astro]
---
# Hub Consolidation Over Per-Site Scaffolding

## The Lesson

When building a platform that serves N variants of the same structure, start with a single consolidated site that treats variation as data, not as separate projects. Late consolidation — after scaffolding N separate sites — is expensive and produces a massive, risky changeset.

## Context

A regulatory compliance readiness platform needed to serve 12 regulation topics (CCPA, GDPR, HIPAA, SOC 2, etc.), each with 9 identical page types (landing, what-is, readiness-process, about, controls, advisory, services, tools, 404). The initial approach scaffolded each regulation as its own Astro project with its own config, components, content, and deploy workflow. The hub site existed separately as a portal linking to these 12 sites.

## What Happened

1. Phase 010 built SOC 2 as the first standalone topic site across 5 sub-phases (scaffold, content collections, components, pages, hub integration). This produced a working reference implementation.
2. Phase 011 replicated the SOC 2 content collection structure across the remaining 11 regulation topics — 11 separate content directories with the same 4 schemas.
3. Phase 012 scaffolded all 11 regulation sites as independent Astro projects, each with their own `astro.config.mjs`, components, pages, and deploy workflows.
4. After seeing the result — 12 near-identical projects with duplicated components, styles, and build configs — the decision was made to consolidate everything into the existing hub site.
5. The consolidation commit touched 840 files, deleted ~99,000 lines of duplicated code, and moved all content into a single Astro project with shared components and content collections keyed by topic slug.
6. Post-consolidation, several fixes were needed: MDX scoped styles didn't work (moved to global CSS), deploy workflow was in the wrong directory, relative links broke across topic pages, and nav branding needed topic-awareness.

## Key Insights

- **Duplication at the project level is harder to fix than duplication at the file level.** When 12 projects share the same Nav component, fixing a bug means touching 12 files. When it's one component with a topic parameter, it's one file. The consolidation deleted 99K lines because the duplication was structural.
- **"Build one, then replicate" only works if you replicate the right unit.** SOC 2 was a good prototype, but the decision to replicate at the project level (full Astro site) rather than the content level (data files plugged into shared templates) created unnecessary work.
- **Late consolidation produces high-risk commits.** An 840-file, 99K-deletion commit is hard to review, hard to revert partially, and likely to introduce secondary bugs. Starting consolidated avoids this.
- **The signal to consolidate is when your "scaffold" phase is mostly copy-paste.** If Phase 012 had been "write 11 site.json manifests," consolidation would have been the obvious architecture from the start.
- **Content collections are the right abstraction for multi-variant sites.** Astro's content collections with topic-keyed directory structure (`controls/soc2/`, `controls/gdpr/`) let one set of components and pages serve all 12 topics. The variation lives in markdown files, not in code.

## Applicability

This applies to any platform serving multiple instances of the same structure: multi-tenant SaaS marketing sites, documentation sites for multiple products, or compliance portals for multiple frameworks. It does NOT apply when the variants genuinely diverge in structure — if topic A needs 9 pages and topic B needs 3, separate projects may be warranted.

## Related Lessons

- [Content-Driven Architecture for Regulatory Frameworks](content-driven-architecture-for-regulatory-frameworks.md) — the architecture that made consolidation work
- [Prototype One Instance Before Scaling to N](prototype-one-instance-before-scaling-to-n.md) — the phased SOC 2 build that preceded consolidation

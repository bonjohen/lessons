---
title: "Canonical Model as Single Source of Truth"
summary: "When a system must produce multiple visual representations of the same architecture, build a single normalized graph model and derive all outputs from it. Renderers that read the same model cannot drift from each other; renderers that maintain their own state always will."
date: 2026-05-13
lesson_type: implementation
tags: [data-modeling, ai]
---
# Canonical Model as Single Source of Truth

## The Lesson

When a system must produce multiple visual representations of the same architecture, build a single normalized graph model and derive all outputs from it. Renderers that read the same model cannot drift from each other; renderers that maintain their own state always will.

## Context

An architecture visualization platform needed to produce Mermaid diagrams (for markdown embedding), Graphviz DOT (for dense dependency graphs), and React Flow interactive views — all depicting the same enterprise system with 83 entities and 83 relationships across 21 entity types. The system also needed to support regeneration as source documents evolved, meaning outputs could never be hand-edited.

## What Happened

1. Phase 1 built a Pydantic-based canonical knowledge model: `Entity` (with typed IDs, properties, tags), `Relationship` (with typed edges and metadata), and `KnowledgeGraph` (with add/remove/query helpers). This was the foundation — no rendering existed yet.
2. Phase 2 populated the model with a real-world enterprise architecture (six-layer GTM system) as YAML files. The model was validated by loading it through the schema and running 37 graph-query tests.
3. Phase 3 built a Mermaid renderer. It consumed `KnowledgeGraph` + `DiagramConfig` and emitted Mermaid syntax. The renderer never touched storage directly.
4. Phase 6 added a Graphviz renderer and React Flow frontend. Both consumed the same `KnowledgeGraph` through the same `Renderer` ABC and `filter_graph` helper. The Graphviz renderer was written in under an hour because the model, filtering, and grouping logic already existed.
5. Adding the `format` query parameter to the API was a 30-line change — the endpoint just picked a different renderer instance. No data transformation was needed.

## Key Insights

- **The model must exist before any renderer.** Building the canonical model first (Phase 1) and populating it with real data (Phase 2) before writing a single renderer (Phase 3) forced the model to be complete and self-sufficient. Had a renderer been built first, the model would have been shaped by that renderer's limitations.
- **Renderer independence is enforced by the ABC.** The abstract `Renderer.render(graph, config) -> str` contract means every renderer receives the same inputs. There is no renderer-specific data path or storage query. This made it trivial to add Graphviz months after Mermaid — no model changes required.
- **Filtering belongs to the base, not the renderers.** The `filter_graph()` method lives on the `Renderer` ABC, not on individual renderers. Entity type filters, relationship type filters, tag filters, and exclusion lists work identically across Mermaid, Graphviz, and any future renderer.
- **DiagramConfig is the single control surface.** One configuration object (`DiagramConfig`) controls what a diagram shows — which entity types, which relationships, grouping, direction, style overrides. This object is renderer-agnostic, so the same preset config produces a Mermaid flowchart or a Graphviz DOT graph depending only on the `format` parameter.
- **Regeneration is free when outputs derive from model.** Because no output is hand-edited (the PDR explicitly forbids it), re-running the renderer after model changes produces updated diagrams automatically. This is only possible because the model is the sole source of truth.

## Applicability

This pattern applies to any system that produces multiple representations of the same data: documentation generators, API schema tools (OpenAPI → client SDKs → docs), dashboard systems, or reporting pipelines. It does NOT apply when the representations are fundamentally different data (e.g., a user profile page vs. an analytics dashboard — those are different views of different models, not the same model rendered differently).

## Related Lessons

- [Multi-Renderer Architecture with Shared Style Palettes](multi-renderer-shared-style-palettes.md) — the visual consistency corollary to this structural pattern
- [Preset Configs vs. Custom Configs](preset-vs-custom-diagram-configs.md) — how the DiagramConfig control surface serves both quick and advanced use cases

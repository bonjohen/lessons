# Multi-Renderer Architecture with Shared Style Palettes

## The Lesson

When building multiple rendering backends for the same data model, define the visual language (colors, shape semantics, edge style categories) once and map it to each renderer's syntax independently. Visual consistency across output formats is easy to lose when renderers are built in isolation; a shared palette prevents it.

## Context

A diagram platform supported three rendering backends — Mermaid (markdown-embeddable), Graphviz (dense DOT graphs), and React Flow (interactive browser canvas) — all depicting the same knowledge graph of 83 entities across 21 types. Each renderer has its own syntax for shapes, colors, and edge styles. Without coordination, an "agent" node could be blue in Mermaid, green in Graphviz, and gray in React Flow.

## What Happened

1. Phase 3 built the Mermaid renderer with an explicit style module: `ENTITY_COLORS` (21 entity types → hex colors), `NODE_SHAPES` (entity type → Mermaid bracket syntax), `EDGE_STYLES` (17 relationship types → line styles: solid for data flow, dotted for governance, thick for structural).
2. Phase 6 built the Graphviz renderer. Rather than designing a new palette, the `renderers/graphviz/styles.py` module was written to match the Mermaid palette: same hex colors, same semantic shape mappings (agent = rounded/oval, policy = hexagon, data_store = cylinder, approval_gate = diamond), same edge style categories (data = solid, governance = dotted, structural = bold).
3. The React Flow frontend's `styles.ts` exported the same `ENTITY_COLORS` map as a TypeScript object. Custom node components used these colors for background fills. The color you see on an agent node in the browser is the same `#4A90D9` used in Mermaid's `classDef` and Graphviz's `fillcolor`.
4. Edge style semantics were preserved conceptually but adapted to each renderer's capabilities: Mermaid uses `-.->` for dotted, Graphviz uses `style="dotted"`, React Flow uses stroke color. The *meaning* (dotted = governance) is consistent even though the *syntax* differs.

## Key Insights

- **Define the palette at the domain level, not the renderer level.** "Agents are blue (#4A90D9)" is a domain decision. "Blue in Mermaid is `classDef agent fill:#4A90D9`" is a renderer mapping. Separating these two concerns means adding a new renderer requires only the mapping, not re-deciding the palette.
- **Shape semantics matter more than shape identity.** Mermaid's "stadium" shape and Graphviz's "oval" shape look different, but both convey "active actor." The semantic mapping (agent = rounded shape that suggests activity) is more important than pixel-identical rendering across formats.
- **Edge style categories reduce cognitive load.** Four categories — solid (data flow), dotted (governance), bold (structural), dashed (evidence/reference) — are enough to distinguish relationship types visually. Mapping 17 relationship types to 17 distinct styles would be unreadable.
- **Three separate style files is better than one shared abstraction.** Each renderer's style module (`mermaid/styles.py`, `graphviz/styles.py`, `frontend/styles.ts`) is self-contained and uses its renderer's native types. A shared "abstract style" layer would add indirection without reducing the per-renderer mapping work, since each renderer's syntax is fundamentally different.
- **Colors in hex are the universal interchange format.** Hex color strings (`#4A90D9`) work in Mermaid CSS, Graphviz attributes, React inline styles, and Tailwind arbitrary values. No conversion needed — just copy the hex string.

## Examples

**Same entity, three renderers:**

Mermaid:
```
classDef agent fill:#4A90D9,stroke:#333,color:#fff
node_id(["Agent Label"])
class node_id agent
```

Graphviz:
```dot
node_id [label="Agent Label", shape="oval", fillcolor="#4A90D9", fontcolor="#FFFFFF"];
```

React Flow (TypeScript):
```tsx
<div style={{ backgroundColor: "#4A90D9" }}>
  <div className="text-white">Agent Label</div>
</div>
```

All three produce a blue node with white text labeled "Agent Label."

## Applicability

This pattern applies to any system rendering the same data across multiple visual formats: charting libraries (SVG + Canvas + PDF), design systems (web + native + email), reporting tools (HTML + PDF + PowerPoint). It does NOT apply when the different formats serve fundamentally different audiences who need different visual languages (e.g., a technical architecture diagram vs. an executive summary — those may intentionally use different palettes).

## Related Lessons

- [Canonical Model as Single Source of Truth](canonical-model-single-source-of-truth.md) — the data consistency that visual consistency depends on

# Preset Configs vs. Custom Configs for Diagram Generation

## The Lesson

When building a query or configuration system, provide a registry of named presets for the common cases and a full custom endpoint for everything else. Presets give users instant value without learning the schema; the custom path preserves full flexibility for power users.

## Context

A diagram platform needed to serve both quick "show me the architecture overview" requests and specific "show me only agents and tools with `uses` relationships, laid out left-to-right" requests. The underlying model had 21 entity types and 17 relationship types, making the full configuration space large. Most users would only ever need 5-6 standard views.

## What Happened

1. The `DiagramConfig` model was designed first with full expressiveness: entity type filters, relationship type filters, tag filters, grouping, direction, style overrides, and exclusion lists.
2. Six preset configurations were registered in a `PRESET_CONFIGS` dictionary: `architecture_overview`, `data_flow`, `trust_boundaries`, `evidence_lineage`, `tool_map`, `policy_map`. Each preset is a `DiagramConfig` instance with meaningful filters and titles pre-filled.
3. The API exposed three diagram endpoints: `GET /presets` (list what's available), `GET /presets/{name}` (render a preset), and `POST /diagrams` (render with a custom `DiagramConfig` body).
4. The frontend's preset selector dropdown maps directly to the `GET /presets/{name}` endpoint — one click, one diagram. Power users can hit the POST endpoint with curl or the Swagger UI.
5. When the Graphviz renderer was added, the same preset configs worked without modification — a `format` query parameter was the only addition needed.

## Key Insights

- **Presets are just named instances of the full config.** There is no separate "preset schema" vs. "custom schema." A preset is literally a `DiagramConfig` stored in a dictionary. This means presets and custom configs share validation, rendering, and export logic with zero duplication.
- **The registry pattern makes presets discoverable.** The `PRESET_CONFIGS` dictionary is iterable, so the `GET /presets` endpoint auto-generates the list. Adding a new preset is one function call (`_register("name", DiagramConfig(...))`), not a new endpoint or route.
- **Presets document the model's interesting views.** The six presets are not arbitrary — they represent the views that matter for the enterprise architecture domain (architecture overview, data flow, trust boundaries, etc.). They serve as documentation of what the model contains, not just shortcuts.
- **Custom configs should accept the full schema, not a subset.** Early designs considered a "simplified" custom config with fewer fields. This was rejected because it would create a capability gap between presets and custom queries. Instead, the POST endpoint accepts the exact same `DiagramConfig` that presets use.

## Examples

**Preset usage** (zero learning curve):
```bash
curl http://localhost:8019/projects/myproject/diagrams/presets/architecture_overview
```

**Custom usage** (full control):
```bash
curl -X POST http://localhost:8019/projects/myproject/diagrams \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Agent-Tool Access",
    "direction": "LR",
    "entity_filter": ["agent", "tool"],
    "relationship_filter": ["uses"]
  }'
```

Both use the same renderer, the same filtering logic, and the same response schema.

## Applicability

This pattern applies to any system with a query or configuration surface: search engines (saved searches vs. advanced query), dashboard tools (preset dashboards vs. custom widgets), report generators, CI pipeline configurations. It does NOT apply when the "common" and "custom" paths have fundamentally different execution models — in that case, a unified config object won't work cleanly.

## Related Lessons

- [Canonical Model as Single Source of Truth](canonical-model-single-source-of-truth.md) — the model that makes both preset and custom configs possible

# Rule-Based Extraction Before LLM Extraction

## The Lesson

When building an entity extraction pipeline, implement rule-based heuristics first and defer LLM-assisted extraction until the deterministic baseline is tested and measured. The rule-based layer gives you a reproducible, cost-free, fast foundation that LLM extraction can extend — not replace.

## Context

An architecture visualization platform needed to extract entities and relationships from Markdown documentation. The source material was semi-structured: headings denoted components, tables listed properties, bold-label lists described behaviors, and directional keywords like "sends to" or "governed by" implied relationships. The project had 83 manually defined entities as ground truth. An LLM could extract more nuanced entities, but each API call costs money and introduces non-determinism.

## What Happened

1. Phase 5 built three extraction components without any LLM calls: a `MarkdownExtractor` (heading parsing, table extraction, bold-label list extraction, keyword-based relationship inference), a `YAMLJSONExtractor` (direct loading of structured definitions), and a `RelationshipInferrer` (co-occurrence, directional keywords, heading nesting).
2. The `MarkdownExtractor` used a 21-keyword-to-EntityType mapping (e.g., "agent" → Agent, "policy" → Policy, "adapter" → Signal) to classify heading-derived entities. Confidence scores were assigned by extraction method: 0.6 for headings, 0.5 for tables, 0.4 for list items.
3. An `EntityResolver` deduplicated extracted entities using token-overlap similarity (Jaccard coefficient at 0.7 threshold), grouped by entity type. It merged properties, averaged confidence scores, and assigned stable IDs in `type.domain.name` format.
4. Jinja2 prompt templates for LLM-assisted extraction were written and committed (`extract_entities.j2`, `extract_relationships.j2`) but deliberately NOT wired into the pipeline. They exist as ready-to-use templates for a future phase.
5. Tests measured extraction coverage: the rule-based pipeline found at least 10% of the 83 manually defined entities from raw documentation alone. This established a measurable baseline that LLM extraction can be compared against.

## Key Insights

- **Deterministic extraction is testable extraction.** The rule-based pipeline produces the same output every time for the same input. This means tests can assert exact entity counts, specific entity IDs, and relationship types. LLM extraction would require fuzzy assertions or golden-file comparison — a fundamentally weaker testing strategy.
- **Cost-free extraction runs in CI.** The 41 extraction tests run in under a second with zero API calls. If LLM extraction had been the baseline, every test run would cost money or require mocking — and mocked LLM responses test the mock, not the extraction.
- **Confidence scores create a natural extension point.** Rule-based extractions carry lower confidence (0.4-0.6) than structured definitions (1.0). When LLM extraction is added, its outputs can carry their own confidence (e.g., 0.7-0.9), and the entity resolver's merge logic already handles mixed-confidence inputs.
- **Templates without wiring is the right staging pattern.** The Jinja2 templates exist in the codebase, are version-controlled, and can be reviewed — but they don't execute. This avoids the "commented-out code" smell while keeping the LLM extraction path visible and ready.
- **Measure coverage against ground truth early.** The 10% coverage threshold is deliberately low — it proves the pipeline works end-to-end, not that it's sufficient. The metric exists so that when LLM extraction is added, the improvement is quantifiable: "rule-based: 10%, rule-based + LLM: 65%."

## Examples

**Rule-based extraction** (deterministic, free, fast):
```python
extractor = MarkdownExtractor()
result = extractor.extract("docs/architecture.md")
# Always returns the same entities for the same doc
# Runs in < 100ms
# Cost: $0.00
```

**LLM extraction** (future, non-deterministic, paid):
```python
# Template exists but is not wired:
# prompts/extract_entities.j2
# Would require: API key, rate limiting, retry logic,
# non-deterministic output handling, cost tracking
```

## Applicability

This pattern applies to any extraction or classification pipeline where determinism and cost matter: document parsing, log analysis, code analysis, data ingestion. It does NOT apply when the source material is genuinely unstructured (e.g., free-form natural language with no headings, tables, or keyword patterns) — in that case, LLM extraction may be the only viable first step.

## Related Lessons

- [Entity ID Stability Through Format Conventions](entity-id-stability-through-format-conventions.md) — the ID format that makes entity resolution possible
- [Canonical Model as Single Source of Truth](canonical-model-single-source-of-truth.md) — the model that extraction populates

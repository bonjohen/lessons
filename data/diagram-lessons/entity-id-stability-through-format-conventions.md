# Entity ID Stability Through Format Conventions

## The Lesson

When building a knowledge graph that must support regeneration, deduplication, and cross-system references, enforce a structured ID format from day one. An ID like `entity_type.domain.name` is simultaneously human-readable, machine-parseable, and stable across re-extraction — properties that free-form or auto-incremented IDs cannot provide.

## Context

An architecture visualization platform ingested enterprise documentation and extracted entities (agents, tools, policies, workflows, etc.) into a canonical graph model. The system needed to support re-extraction as source documents evolved, meaning entities extracted today had to match entities extracted next month. The model held 83 entities across 21 types, with 83 typed relationships referencing entities by ID.

## What Happened

1. The entity ID format `entity_type.domain.name` was defined in Phase 1 as a Pydantic-validated field. A regex validator enforced the three-part dotted structure at schema level — invalid IDs were rejected before reaching storage.
2. Phase 2 manually defined all entities with IDs like `agent.acme.fsi_vertical_agent`, `policy.acme.block_restricted`, `tool.acme.brave_search`. The dotted format made it immediately obvious what type and domain an entity belonged to, even in raw YAML files.
3. Phase 5 built an extraction pipeline that generated *suggested IDs* from extracted entity labels. The entity resolver normalized labels to the `type.domain.name` format, using token overlap (Jaccard similarity at 0.7 threshold) to merge duplicates.
4. Referential integrity checks on relationships (source and target must exist in the graph) caught dangling references early. Because IDs were structured and human-readable, the error messages were immediately actionable: "Source entity not found: `agent.acme.orchestrator`" tells you exactly what's missing.
5. The API used path-based routing for entity IDs (`/entities/{entity_id:path}`) because dotted IDs conflict with URL path segments. This was a minor friction point but was solved once and never revisited.

## Key Insights

- **Structured IDs are self-documenting.** `tool.acme.brave_search` tells you the type, domain, and name without querying the entity. This matters when reading YAML files, debugging relationship errors, or scanning API responses. Auto-incremented IDs (`entity_42`) carry no information.
- **ID stability enables regeneration.** When re-extracting from updated source docs, the entity resolver can match new extractions to existing entities by constructing the same ID from the same label. Without a deterministic ID format, regeneration requires a separate reconciliation step.
- **Deduplication depends on predictable ID structure.** The entity resolver groups by type (first segment), then clusters by name similarity (third segment). This two-level grouping is only possible because the ID format guarantees the type is parseable from the ID string.
- **Validate IDs at the schema boundary, not at usage sites.** The Pydantic validator on the `Entity.id` field means invalid IDs never enter the graph. Every downstream consumer (renderers, API, storage) can trust the format without re-validating.
- **Dotted IDs need URL-encoding awareness.** The one friction point: IDs containing dots look like file extensions or path separators in URLs. FastAPI's `{entity_id:path}` converter handles this, but it's a known gotcha that should be documented upfront.

## Examples

**Good: structured ID**
```yaml
id: agent.acme.fsi_vertical_agent
entity_type: agent
label: FSI Vertical Agent
```
From the ID alone you know: it's an agent, in the acme domain, named fsi_vertical_agent.

**Bad: free-form ID**
```yaml
id: fsi-vertical-agent-1
entity_type: agent
label: FSI Vertical Agent
```
No type, no domain, the `-1` suffix suggests deduplication was done after the fact.

## Applicability

This pattern applies to any system where entities must be referenced across documents, re-extracted from evolving sources, or matched across systems: knowledge graphs, content management systems, configuration management databases, API registries. It does NOT apply to systems where IDs are internal-only and never seen by humans (e.g., database primary keys in a closed system where UUIDs are fine).

## Related Lessons

- [Rule-Based Extraction Before LLM Extraction](rule-based-extraction-before-llm.md) — the extraction pipeline that depends on stable IDs for entity resolution

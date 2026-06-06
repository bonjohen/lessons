---
title: "Config-First Development"
summary: "When building a system that depends on external data sources, templates, or configuration-driven behavior, ship the configuration files before the code that consumes them. This forces you to validate your data model against real requirements before investing in implementation, and it makes each subs..."
date: 2026-06-06
lesson_type: implementation
tags: [data-modeling, pipeline]
---
# Config-First Development

## The Lesson

When building a system that depends on external data sources, templates, or configuration-driven behavior, ship the configuration files before the code that consumes them. This forces you to validate your data model against real requirements before investing in implementation, and it makes each subsequent code phase smaller and more focused.

## Context

GTMLeads is a signal pipeline with 12 data sources, 265 signal templates, and 15 topic packs — all defined in JSON config files that drive adapter queries, scoring weights, and candidate matching. The pipeline code reads these configs at startup and uses them to orchestrate fetches, normalization, and scoring. Both the initial 9-phase build and the later 5-adapter expansion used config-first ordering.

## What Happened

1. In the initial build, Phase 2 shipped `sources.json` (source definitions), `topic-packs.json` (15 topic packs with per-source term lists), and the Pydantic models that validate them — before any service or adapter code existed.
2. Phase 3 shipped all 265 signal templates and query templates — still no pipeline code. Config validation tests (`test_config_validation.py`) ensured every template referenced valid sources, every topic pack had well-formed term lists, and cross-references were consistent.
3. When Phase 4 (scoring engine) began, the scoring weights and source quality scores were already defined in config. The scoring code was pure math applied to values that were already validated.
4. During the adapter expansion, Phase 1 again shipped config first: 5 new sources added to `sources.json`, new query templates, and updated scoring weights in `scoring.py`. The config validation tests caught that two source IDs didn't match the expected pattern before any adapter was written.
5. The config-first approach also made code review faster — reviewers could understand what was being built (the config) before understanding how it was built (the code).

## Key Insights

- **Config is a contract.** A `sources.json` entry that says `"source_id": "edgar", "source_type": "api", "rate_limit_rpm": 10` is a specification that the adapter must satisfy. Writing the spec first forces you to think about rate limits, authentication, and field mappings before coding.
- **Config validation tests are the cheapest tests to write.** A test that loads `sources.json` and checks that every `source_id` appears in the scoring weights dict takes 5 lines of code and catches entire categories of bugs (missing sources, typos in IDs, orphaned configs).
- **Fixing a JSON file is cheaper than refactoring a class.** When the adapter expansion discovered that the config needed a new field for User-Agent requirements (SEC EDGAR requires a contact email), adding it to the JSON was a one-line change. If the adapter had been written first, it would have needed a code change plus a config change plus a test change.
- **Config-first enables parallel work.** Once the config is committed, multiple people (or sessions) can work on different adapters in parallel, because the shared contract is already established. Without it, parallel work risks conflicting assumptions about the data model.

## Applicability

This pattern applies to any system where configuration drives behavior — plugin registries, feature flags, data pipelines, API gateways. It is most valuable when the config is complex (many entries, cross-references) and when multiple code paths consume the same config.

It is less useful for simple key-value configuration (e.g., a port number or log level) where the config and code are trivially coupled.

## Related Lessons

- [Phased Adapter Expansion](phased-adapter-expansion.md) — config-first was Phase 1 of the expansion
- [Four-Level Deduplication](four-level-deduplication.md) — dedup levels were designed during config phase

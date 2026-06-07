---
title: "Scoring Composition"
summary: "When ranking records from heterogeneous sources, decompose the score into independent components with explicit weights, each normalized to 0.0–1.0. This makes the scoring system auditable (you can explain why a record scored high), tunable (change one weight without affecting others), and extensible..."
date: 2026-05-20
lesson_type: algorithms
tags: [database, testing, statistics]
---
# Scoring Composition

## The Lesson

When ranking records from heterogeneous sources, decompose the score into independent components with explicit weights, each normalized to 0.0–1.0. This makes the scoring system auditable (you can explain why a record scored high), tunable (change one weight without affecting others), and extensible (add a new component without rewriting the formula).

## Context

GTMLeads ingests signals from 10+ public APIs and needs to surface the most relevant, trustworthy, and timely signals for human review. A single relevance score isn't enough — a signal from an authoritative source (CISA KEV) published yesterday is more valuable than a tangentially-related GitHub issue from last month, even if the GitHub issue matches more keywords. The scoring system needed to capture multiple quality dimensions and combine them into a single confidence score for ranking.

## What Happened

1. Five scoring components were identified during the design phase: **freshness** (how recent), **source quality** (how authoritative the source is), **relevance** (keyword match ratio), **evidence strength** (template-defined class), and **confidence** (weighted composite).
2. Each component was implemented as a standalone function returning a float in `[0.0, 1.0]`. No component depends on any other component's output.
3. Weights were assigned: freshness 0.3, source quality 0.2, relevance 0.2, evidence strength 0.3. These sum to 1.0, making the composite score also `[0.0, 1.0]`.
4. Freshness uses exponential decay (`e^(-0.012 * days)`), calibrated so 7-day-old signals score ~0.9, 30-day-old ~0.7, and 90-day-old ~0.4. The decay rate was derived from the average of three target points.
5. Source quality is a static lookup table: CISA KEV = 1.0, Federal Register = 0.95, GitHub = 0.8, Reddit = 0.4. Unknown sources default to 0.5.
6. A review-status modifier multiplies the composite: accepted = 1.0, pending = 0.8, rejected = 0.0. This prevents rejected signals from appearing in ranked results.
7. The scoring functions are pure (no database, no I/O). The `ImportRunner` calls them inline during signal ingestion, passing the results into the upsert.

## Key Insights

- **Normalize everything to the same range.** When components use different scales (days vs. count vs. boolean), the weights become meaningless. Normalizing to `[0.0, 1.0]` means `W=0.3` has the same influence regardless of which component it multiplies.
- **Exponential decay is a better time model than linear.** A linear decay treats a 1-day-old signal and a 30-day-old signal as both "recent" if the window is 90 days. Exponential decay gives strong preference to recent signals while still allowing older signals to contribute.
- **Static source quality is good enough to start.** The temptation is to compute source quality dynamically (track accuracy over time, weight by user feedback). A static lookup table based on domain knowledge is 10 lines of code, immediately useful, and easy to update. Dynamic scoring can be layered on later.
- **Pure functions make scoring testable.** Every scoring function can be tested with synthetic inputs — no database, no fixtures, no mocking. The test suite has 145 lines of scoring tests that run in milliseconds.
- **The review modifier is a separate concern.** Mixing review status into the component weights would complicate both the scoring math and the review workflow. Applying it as a post-composite multiplier keeps the scoring and review systems cleanly separated.

## Examples

**Score calculation for a 3-day-old CISA KEV signal matching 2 of 4 keywords:**
```
freshness     = e^(-0.012 * 3)   = 0.965
source_quality = 1.0              (CISA KEV)
relevance     = 2/4              = 0.5
evidence      = 1.0              (high class)

composite = 0.3(0.965) + 0.2(1.0) + 0.2(0.5) + 0.3(1.0)
          = 0.290 + 0.200 + 0.100 + 0.300
          = 0.890

With pending modifier: 0.890 * 0.8 = 0.712
```

## Applicability

This pattern applies to any ranking or prioritization system where multiple quality dimensions must be combined: search relevance, fraud scoring, content moderation queues, alert triage. It works best when the components are conceptually independent and domain experts can reason about the weights.

It is less useful when the interactions between components are complex (e.g., a high relevance score should change the freshness weight). In that case, a learned model or decision tree may be more appropriate than a weighted sum.

## Related Lessons

- [Four-Level Deduplication](four-level-deduplication.md) — dedup runs before scoring; prevents duplicate signals from inflating scores
- [Config-First Development](config-first-development.md) — scoring weights were defined in config before the scoring code

---
title: "Four-Level Deduplication Strategy"
summary: "When deduplicating records from heterogeneous sources with varying ID reliability, use a priority-ordered cascade of match strategies — from strongest (source-native IDs) to weakest (fuzzy metadata). Check each level in order and stop at the first match. This avoids both false negatives (missed dupl..."
date: 2026-06-06
lesson_type: algorithms
tags: [database, pipeline]
---
# Four-Level Deduplication Strategy

## The Lesson

When deduplicating records from heterogeneous sources with varying ID reliability, use a priority-ordered cascade of match strategies — from strongest (source-native IDs) to weakest (fuzzy metadata). Check each level in order and stop at the first match. This avoids both false negatives (missed duplicates) and false positives (incorrectly merged distinct records).

## Context

GTMLeads ingests signals from 10+ API sources (GitHub, SEC EDGAR, NVD, arXiv, Reddit, etc.). Each source has different ID conventions: some provide stable unique identifiers (NVD's CVE IDs, EDGAR's accession numbers), some provide URLs but no IDs, and some provide neither reliably. The pipeline runs repeatedly against the same sources with overlapping queries, so the same signal can arrive multiple times across different runs, templates, and topic packs. Without deduplication, the database would fill with redundant records that pollute scoring and review.

## What Happened

1. The initial design considered a single-level dedup using `(source_id, external_id)`. This worked for sources with strong IDs (NVD, CISA KEV) but failed for sources where the external ID was absent or inconsistent.
2. URL-based dedup was added as a second level for sources like HN Algolia where the canonical URL is the most stable identifier — the same story URL appears across multiple API queries.
3. Content-hash dedup (SHA-256 of normalized text) was added as a third level to catch cases where the same content arrives from different queries against the same source, but with different metadata (e.g., different matched keywords or template assignments).
4. A fuzzy fallback using `(source_id, template_id, topic_pack_id, published_date, title)` was added as the fourth level. This catches near-duplicates where the content differs slightly (e.g., truncation differences across API pagination) but the signal is clearly the same event.
5. The cascade uses short-circuit evaluation: once a match is found at any level, the function returns immediately without checking lower levels. This prevents a weaker match from overriding a stronger one.
6. Reviewed signals (status `accepted` or `rejected`) are never overwritten by re-imports — only pending signals get updated. This preserves human review work.

## Key Insights

- **Not all IDs are created equal.** Some APIs return stable, globally unique identifiers. Others return session-specific IDs, paginated offsets, or nothing at all. Your dedup strategy must handle all of these, not just the best case.
- **Priority ordering prevents false merges.** A content hash match should not override an external ID mismatch. By checking strongest identifiers first and stopping on first match, you avoid merging records that happen to share content but are genuinely distinct (e.g., a CVE advisory republished verbatim by a different organization).
- **Content normalization is critical for hash-based dedup.** The content hash normalizes whitespace (`" ".join(text.lower().split())`) before hashing. Without this, the same text with different line breaks or capitalization would produce different hashes, defeating the purpose.
- **The fuzzy level is a safety net, not a primary strategy.** Level 4 (title + date + metadata) catches the long tail of duplicates that slip through the first three levels. It has the highest false-positive risk, so it requires the most fields to match — five columns must all agree.
- **Protect reviewed records from re-import.** Once a human has accepted or rejected a signal, the pipeline should never silently overwrite that decision with fresh data. The dedup function returns the existing signal's status so the upsert logic can make the right call.

## Examples

**Dedup cascade in practice:**
```
Signal arrives: source=nvd, external_id=CVE-2024-1234
  → Level 1: (nvd, CVE-2024-1234) → MATCH → return existing signal

Signal arrives: source=hn_algolia, external_id=None, url=https://news.ycombinator.com/item?id=12345
  → Level 1: no external_id → skip
  → Level 2: (hn_algolia, https://...) → MATCH → return existing signal

Signal arrives: source=reddit, external_id=None, url=None, text="Large language models are..."
  → Level 1: skip
  → Level 2: skip
  → Level 3: (reddit, sha256("large language models are..."), template_42, T3) → MATCH

Signal arrives: source=openalex, all fields present but no prior record
  → Level 1-4: no match → INSERT new signal
```

## Applicability

This pattern applies to any data ingestion pipeline that receives overlapping data from multiple sources or repeated queries. It is particularly useful when sources have inconsistent ID schemes. It does NOT apply to systems where a single authoritative source controls the ID space — there, simple upsert-by-ID is sufficient and the cascade adds unnecessary complexity.

## Related Lessons

- [Config-First Development](config-first-development.md) — dedup levels were designed during the config phase before adapters existed
- [Scoring Composition](scoring-composition.md) — scoring runs after dedup; duplicate detection prevents score inflation

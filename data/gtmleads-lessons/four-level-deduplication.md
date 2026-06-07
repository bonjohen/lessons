---
title: "Four-Level Deduplication Strategy"
summary: "When deduplicating records from heterogeneous sources with varying ID reliability, use a priority-ordered cascade of match strategies — from strongest (source-native IDs) to weakest (fuzzy metadata). Check each level in order and stop at the first match. This avoids both false negatives (missed dupl..."
date: 2026-05-20
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

## Implementation Guide

### Step 1: Define your match levels by strength

Survey your data sources and identify which identifiers are available. Order them from most reliable to least:

| Level | Match on | Strength | When to use |
|-------|----------|----------|-------------|
| 1 | Source-native ID (e.g. CVE-2024-1234) | Strongest | Source provides stable, globally unique IDs |
| 2 | Canonical URL | Strong | Source provides persistent URLs but no unique IDs |
| 3 | Content hash | Medium | Same text arrives from different queries or metadata contexts |
| 4 | Fuzzy composite (title + date + metadata) | Weakest | Near-duplicates with minor content differences |

Your specific levels will vary — the important thing is the ordering. Add levels as you discover new duplication patterns in production data.

### Step 2: Implement the cascade with short-circuit evaluation

Write a function that checks each level in order and returns on the first match. Use a simple if/elif chain — don't over-abstract this:

```python
import hashlib

def find_duplicate(db, signal: dict) -> dict | None:
    source = signal["source_id"]

    # Level 1: External ID (strongest)
    if signal.get("external_id"):
        match = db.execute(
            "SELECT * FROM signal WHERE source_id = ? AND external_id = ?",
            (source, signal["external_id"])
        ).fetchone()
        if match:
            return match

    # Level 2: Canonical URL
    if signal.get("url"):
        match = db.execute(
            "SELECT * FROM signal WHERE source_id = ? AND url = ?",
            (source, signal["url"])
        ).fetchone()
        if match:
            return match

    # Level 3: Content hash
    text = signal.get("signal_text", "")
    normalized = " ".join(text.lower().split())  # Normalize whitespace
    content_hash = hashlib.sha256(normalized.encode()).hexdigest()
    match = db.execute(
        "SELECT * FROM signal WHERE source_id = ? AND content_hash = ?",
        (source, content_hash)
    ).fetchone()
    if match:
        return match

    # Level 4: Fuzzy composite (weakest — requires ALL fields to match)
    match = db.execute(
        """SELECT * FROM signal
           WHERE source_id = ? AND template_id = ? AND topic_pack_id = ?
             AND published_date = ? AND title = ?""",
        (source, signal["template_id"], signal["topic_pack_id"],
         signal.get("published_date"), signal.get("title"))
    ).fetchone()
    if match:
        return match

    return None  # No duplicate — this is a new record
```

### Step 3: Protect reviewed records from overwrite

When a duplicate is found, check whether the existing record has been reviewed by a human before overwriting:

```python
def upsert_signal(db, signal: dict):
    existing = find_duplicate(db, signal)
    if existing:
        if existing["status"] in ("accepted", "rejected"):
            return existing  # Never overwrite human decisions
        # Update the pending record with fresh data
        db.execute("UPDATE signal SET ... WHERE signal_id = ?", (..., existing["signal_id"]))
        return existing
    # No duplicate — insert new
    db.execute("INSERT INTO signal ...", (...))
```

### Step 4: Store the content hash at write time

Compute and store the normalized content hash when inserting records, so Level 3 lookups are index-based rather than computed on the fly:

```sql
ALTER TABLE signal ADD COLUMN content_hash TEXT;
CREATE INDEX idx_signal_content_hash ON signal(source_id, content_hash);
```

Compute the hash using the same normalization as the dedup function (lowercase, collapsed whitespace) and store it on insert.

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

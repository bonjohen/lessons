---
title: "FTS5 Integration with SQLite"
summary: "SQLite's FTS5 extension provides production-quality full-text search without an external service. The key to making it work reliably is sync triggers (not application-level writes), `rowid`-based joins (not column joins), and treating the FTS table as a read-only projection of the main table."
date: 2026-05-20
lesson_type: implementation
tags: [database, data-modeling, python]
---
# FTS5 Integration with SQLite

## The Lesson

SQLite's FTS5 extension provides production-quality full-text search without an external service. The key to making it work reliably is sync triggers (not application-level writes), `rowid`-based joins (not column joins), and treating the FTS table as a read-only projection of the main table.

## Context

GTMLeads stores signals in an SQLite database (WAL mode, foreign keys enabled) and needs to support keyword search across signal titles, text, matched keywords, and citation text. The alternatives were: (a) add an external search service like Elasticsearch or Meilisearch, (b) use SQL LIKE queries, or (c) use SQLite's built-in FTS5 extension. For a local-first tool with hundreds to low thousands of signals, FTS5 is the right choice — zero operational overhead, instant indexing, and good-enough ranking.

## What Happened

1. An FTS5 virtual table `signal_fts` was created in the migration schema, indexing four columns: `title`, `signal_text`, `matched_keywords`, and `citation_text`.
2. Three triggers (insert, update, delete) were defined in the same migration to keep `signal_fts` in sync with the `signal` table. The application code never writes to `signal_fts` directly.
3. The delete trigger uses FTS5's special delete syntax: `INSERT INTO signal_fts(signal_fts, rowid, ...) VALUES('delete', OLD.rowid, ...)`. This is non-obvious — it looks like an insert but it's actually a delete command using FTS5's content-sync protocol.
4. Search queries join `signal_fts` to `signal` via `rowid`: `JOIN signal_fts ON s.signal_id = signal_fts.rowid WHERE signal_fts MATCH ?`. Using `signal_id` directly in the MATCH query would fail because FTS5 uses `rowid` internally, not named columns.
5. Results are ordered by `rank`, FTS5's built-in BM25-based relevance score. No custom ranking was needed.
6. The search service function is 8 lines of code. The trigger definitions are 14 lines. The total investment for full-text search was ~22 lines of SQL + 8 lines of Python.

## Key Insights

- **Sync triggers are safer than application-level writes.** If the application writes to `signal_fts` directly, every code path that inserts, updates, or deletes a signal must remember to also update the FTS index. Triggers make this impossible to forget.
- **FTS5 delete syntax is a common gotcha.** The delete operation is `INSERT INTO fts_table(fts_table, rowid, ...) VALUES('delete', ...)` — the first column is the table name as a string literal, not data. This is documented but counterintuitive, and getting it wrong corrupts the index silently.
- **Always join on rowid, not on a named column.** FTS5 virtual tables use `rowid` as their internal key. Even if your main table's primary key is `signal_id` and happens to equal `rowid`, query the FTS table via `rowid` explicitly. This avoids subtle bugs if the table is recreated or rowid mapping changes.
- **BM25 ranking is good enough for most use cases.** FTS5's built-in `rank` column implements BM25 scoring. For a human-review queue where users refine results visually, BM25 is sufficient. Custom ranking adds complexity without proportional value.
- **FTS5 is a projection, not a source of truth.** The FTS table can be rebuilt from the main table at any time (`INSERT INTO signal_fts(signal_fts) VALUES('rebuild')`). This means FTS index corruption is recoverable, unlike a separate search service where data loss might be permanent.

## Implementation Guide

### Step 1: Create the FTS5 virtual table

In your schema migration, define an FTS5 virtual table that mirrors the text columns you want searchable. Use `content=''` to create a "contentless" FTS table (it stores only the index, not a copy of the data):

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS signal_fts USING fts5(
    title, signal_text, matched_keywords, citation_text,
    content=''
);
```

Alternatively, omit `content=''` to let FTS5 store its own copy of the data. Contentless tables are smaller but require explicit sync; content tables are larger but self-contained.

### Step 2: Add sync triggers

Create triggers on the main table so every insert, update, and delete is automatically reflected in the FTS index. The application code never writes to the FTS table directly:

```sql
-- Insert trigger
CREATE TRIGGER signal_fts_insert AFTER INSERT ON signal BEGIN
    INSERT INTO signal_fts(rowid, title, signal_text, matched_keywords, citation_text)
    VALUES (NEW.signal_id, NEW.title, NEW.signal_text, NEW.matched_keywords, NEW.citation_text);
END;

-- Delete trigger (uses FTS5's special delete syntax)
CREATE TRIGGER signal_fts_delete BEFORE DELETE ON signal BEGIN
    INSERT INTO signal_fts(signal_fts, rowid, title, signal_text, matched_keywords, citation_text)
    VALUES ('delete', OLD.signal_id, OLD.title, OLD.signal_text, OLD.matched_keywords, OLD.citation_text);
END;

-- Update trigger (delete old, insert new)
CREATE TRIGGER signal_fts_update AFTER UPDATE ON signal BEGIN
    INSERT INTO signal_fts(signal_fts, rowid, title, signal_text, matched_keywords, citation_text)
    VALUES ('delete', OLD.signal_id, OLD.title, OLD.signal_text, OLD.matched_keywords, OLD.citation_text);
    INSERT INTO signal_fts(rowid, title, signal_text, matched_keywords, citation_text)
    VALUES (NEW.signal_id, NEW.title, NEW.signal_text, NEW.matched_keywords, NEW.citation_text);
END;
```

Note the delete syntax: the first column is the FTS table name as a string literal (`'delete'`), not data. This is FTS5's content-sync protocol — getting it wrong silently corrupts the index.

### Step 3: Write the search query

Join the FTS table to the main table using `rowid` and use the `MATCH` operator for queries. FTS5 provides a built-in `rank` column with BM25 relevance scoring:

```python
def search_signals(db, query: str, limit: int = 20) -> list[dict]:
    sql = """
        SELECT s.*, signal_fts.rank
        FROM signal s
        JOIN signal_fts ON s.signal_id = signal_fts.rowid
        WHERE signal_fts MATCH ?
        ORDER BY signal_fts.rank
        LIMIT ?
    """
    return db.execute(sql, (query, limit)).fetchall()
```

Always join on `rowid`, not on a named column. FTS5 uses `rowid` internally as its key.

### Step 4: Handle index recovery

If the FTS index gets corrupted (rare, but possible after crashes or schema changes), rebuild it from the main table:

```sql
INSERT INTO signal_fts(signal_fts) VALUES('rebuild');
```

This repopulates the index from scratch using the sync triggers' source data. Consider adding a `rebuild` command to your maintenance tooling.

## Applicability

This pattern applies to any SQLite-based application that needs keyword search over text columns, up to tens of thousands of records. At that scale, FTS5 query performance is effectively instant (<10ms).

For larger datasets (millions of records), higher query volumes (hundreds of concurrent searches), or advanced features (faceted search, fuzzy matching, typo tolerance), a dedicated search service (Meilisearch, Typesense, Elasticsearch) is the right choice. FTS5 also doesn't support cross-database search — each SQLite database has its own FTS index.

## Related Lessons

- [Nine-Phase Sequential Build](nine-phase-sequential-build.md) — FTS5 was part of Phase 1 (schema), so all later phases could assume search worked

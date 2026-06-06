---
title: "Dev-Prod Schema Parity"
summary: "When you add a database column via direct SQL instead of a migration file, your dev environment won't have it. The code works in production (where you ran the SQL) but crashes in dev (where the column doesn't exist). Always use migration files, even for \"quick\" schema changes."
date: 2026-06-06
lesson_type: architecture
tags: [cloudflare, database, data-modeling, devops]
---
# Dev-Prod Schema Parity

## The Lesson

When you add a database column via direct SQL instead of a migration file, your dev environment won't have it. The code works in production (where you ran the SQL) but crashes in dev (where the column doesn't exist). Always use migration files, even for "quick" schema changes.

## Context

MyReachBand uses Cloudflare D1 with separate databases for dev and prod. Schema changes are managed via migration files in `migrations/`. Both databases should have identical schemas, applied by running `wrangler d1 migrations apply` against each.

## What Happened

1. Needed to add a `share_url` column to the `bracelets` table to store the QR share link.
2. Ran `wrangler d1 execute qr-bracelet --remote --command="ALTER TABLE bracelets ADD COLUMN share_url TEXT"` directly against production. It worked.
3. Later set up the dev environment. Applied all migration files. The dev database didn't have `share_url` because no migration file existed for it.
4. The dashboard query (`SELECT id, share_url, ... FROM bracelets`) crashed in dev with a column-not-found error, surfacing as Cloudflare's generic "Error 1101: Worker threw exception."
5. Fixed by running the same ALTER TABLE against dev, then creating a migration file (`0004_add_share_url.sql`) to prevent it from happening again.
6. The same issue occurred with `band_text` — added to prod via direct SQL, missing in dev until manually synced.

## Key Insights

- **Direct SQL is untraceable.** There's no record that you ran it, no way to replay it, and no way for a new environment to know it happened. Migration files are the source of truth.
- **The crash is never obvious.** D1 doesn't return "column not found" through the Worker — you get Cloudflare's generic 1101 error page. You have to check the Worker logs or add try/catch to surface the real error.
- **"Quick" schema changes are the most dangerous.** Adding a column takes 5 seconds via direct SQL. Creating a migration file takes 30 seconds. The 25-second shortcut costs hours when the dev environment breaks.
- **Check schema parity after creating a new environment.** Run `PRAGMA table_info(tablename)` on both databases and compare. Any difference means a migration is missing.
- **SQLite rejects unknown columns even with zero rows.** Unlike some databases that might silently ignore missing columns on empty tables, SQLite throws an error on `SELECT missing_column FROM table` even if the table has no rows.

## Examples

### Bad: direct SQL with no migration
```bash
# Works in prod, invisible to dev
wrangler d1 execute my-db --remote --command="ALTER TABLE bracelets ADD COLUMN share_url TEXT"
```

### Good: migration file
```bash
# Create migrations/0004_add_share_url.sql containing:
# ALTER TABLE bracelets ADD COLUMN share_url TEXT;

# Apply to both environments
wrangler d1 migrations apply my-db --remote
wrangler d1 migrations apply my-db-dev --remote -e dev
```

### Checking parity
```bash
wrangler d1 execute my-db --remote --command="SELECT name FROM pragma_table_info('bracelets') ORDER BY cid"
wrangler d1 execute my-db-dev --remote --command="SELECT name FROM pragma_table_info('bracelets') ORDER BY cid"
# Compare the two outputs
```

## Applicability

This applies to any system with multiple database environments: dev/staging/prod with SQL databases, DynamoDB tables, Firestore collections. The principle is the same: schema changes must be declarative and replayable, not imperative and one-off.

## Related Lessons

- [Cloudflare D1](cloudflare-d1.md) — the database where this happened
- [Wrangler CLI](wrangler-cli.md) — the tool used for migrations

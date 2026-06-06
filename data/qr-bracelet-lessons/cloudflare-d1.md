---
title: "Cloudflare D1"
summary: "D1 is serverless SQLite hosted by Cloudflare. It gives you a real SQL database accessible only from your Worker — no connection strings, no connection pooling, no database server to manage. For small apps, it eliminates the entire database operations layer."
date: 2026-06-06
lesson_type: implementation
tags: [cloudflare, serverless, database, api, data-modeling]
---
# Cloudflare D1

## The Lesson

D1 is serverless SQLite hosted by Cloudflare. It gives you a real SQL database accessible only from your Worker — no connection strings, no connection pooling, no database server to manage. For small apps, it eliminates the entire database operations layer.

## Context

MyReachBand stores users, bracelets, and verified phone numbers. The data model is relational (users own bracelets, bracelets reference verified phones). D1 was chosen because it's integrated with Workers — no external database service, no network latency to a remote DB, and it's free at low volume.

## What Happened

1. Created the database with `wrangler d1 create qr-bracelet`. This returns a database ID.
2. Added the database ID to `wrangler.toml` as a binding — the Worker accesses it as `env.DB`.
3. Wrote SQL migrations in `migrations/` directory. Applied with `wrangler d1 migrations apply qr-bracelet --remote`.
4. Queries use prepared statements: `env.DB.prepare("SELECT * FROM users WHERE email = ?").bind(email).first()`.
5. Hit a schema divergence bug: added a column to production via direct SQL but forgot to create a migration file. The dev database didn't have the column, causing a crash. Lesson: always use migration files.
6. D1 query latency was 12-18ms warm — fast enough that the entire request (query + render HTML) completes in ~50ms.

## Key Insights

- **It's real SQLite.** Foreign keys, indexes, transactions, `ALTER TABLE` — all standard SQLite. If you know SQL, you know D1.
- **Always use migration files.** Never add columns via direct `wrangler d1 execute` in production. If you do, the dev database won't have them, and your dev environment will crash on queries that reference the missing column.
- **`.first()` returns null, not undefined.** When querying for a single row, `.first()` returns `null` if no match. `.all()` returns `{ results: [] }`.
- **Bindings, not connection strings.** You declare the database in `wrangler.toml` and access it as `env.DB`. No URLs, no passwords, no connection pool configuration.
- **Separate databases per environment.** Create `qr-bracelet` for prod and `qr-bracelet-dev` for dev. Declare each in its own `[env.dev]` block in `wrangler.toml`. Apply the same migrations to both.
- **Free tier covers most small apps.** 5 million reads/day, 100K writes/day. You'd need thousands of active users before hitting limits.

## Examples

### Creating a database and applying migrations
```bash
wrangler d1 create qr-bracelet
# Copy database_id into wrangler.toml

wrangler d1 migrations apply qr-bracelet --remote
```

### wrangler.toml binding
```toml
[[d1_databases]]
binding = "DB"
database_name = "qr-bracelet"
database_id = "73a81521-cdd7-40f3-8453-e358e702e476"
migrations_dir = "migrations"
```

### Query patterns
```javascript
// Single row
const user = await env.DB.prepare("SELECT * FROM users WHERE email = ?").bind(email).first();

// Multiple rows
const { results } = await env.DB.prepare("SELECT * FROM bracelets WHERE user_id = ?").bind(userId).all();

// Insert
await env.DB.prepare("INSERT INTO users (id, email) VALUES (?, ?)").bind(id, email).run();

// Update
const { meta } = await env.DB.prepare("UPDATE users SET phone = ? WHERE id = ?").bind(phone, id).run();
// meta.changes tells you how many rows were affected
```

### Migration file (migrations/0001_create_users.sql)
```sql
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Applicability

D1 is ideal for: apps with simple relational data, low-to-moderate write volume, and where the database and compute are on the same platform. NOT ideal for: high-write-throughput apps, apps needing full-text search, or apps that need database access from outside Workers (though the REST API exists for CLI tools).

## Related Lessons

- [Cloudflare Workers](cloudflare-workers.md) — D1 is accessed exclusively through Workers bindings
- [Dev-Prod Schema Parity](dev-prod-schema-parity.md) — the migration discipline that prevents D1 divergence

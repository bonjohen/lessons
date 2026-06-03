---
phase: deployment
---

# Seed Data Format Mismatch

## The Lesson

When application code wraps stored values in a specific structure (like `{"v": value}` for JSONB), seed migrations must use the same structure. Format mismatches between seed data and application code are invisible until runtime and often survive testing because tests use the application layer, not the raw seed data.

## Context

A medical portal stored configuration in an `app_config` table with a JSONB `value` column. The application's `ConfigService` wrapped all values in `{"v": value}` when writing and unwrapped with `row.value.get("v")` when reading. An Alembic seed migration pre-populated the default AI provider mode.

## What Happened

1. The seed migration inserted `('ai.provider_mode', '"disabled"')` — a bare JSON string.
2. The ConfigService expected `{"v": "disabled"}` and read values with `row.value.get("v")`.
3. Phases 1-6 implemented and tested features. The config service tests created data through the application layer (which used the correct format), so they passed.
4. Phase 7 (acceptance validation) caught the mismatch: a fresh database with only seed data would return `None` from `_get("ai.provider_mode")` because the bare string `"disabled"` has no `.get("v")` method.
5. The fix was one line: change the seed SQL from `'"disabled"'` to `'{"v": "disabled"}'`.

## Key Insights

- **Seed data and application code are a contract.** If the app writes `{"v": X}`, the seed must write `{"v": X}`. This contract is implicit — no type system or schema enforces it.
- **Application-layer tests don't catch seed-layer bugs.** Tests that create data through the service layer bypass the seed migration entirely. The only test that catches seed format issues is a fresh-database integration test that reads seed data through the application.
- **Acceptance validation phases earn their keep.** This bug was found in Phase 7 (validation), not during implementation. Without a dedicated validation phase, the bug would have shipped and manifested only on fresh deployments.
- **JSONB wrapper patterns need documentation.** The `{"v": value}` convention was a design decision in the ConfigService but wasn't documented as a constraint for seed data authors. Conventions that affect multiple code locations need explicit callout.

## Examples

**Wrong (bare JSON string):**
```sql
INSERT INTO app_config (key, value) VALUES ('ai.provider_mode', '"disabled"');
```

**Right (matches application wrapper):**
```sql
INSERT INTO app_config (key, value) VALUES ('ai.provider_mode', '{"v": "disabled"}');
```

## Related Lessons

- [First-User-Is-Admin Bootstrap](first-user-is-admin-bootstrap.md) — another seed data pattern in the same project

---
phase: process
---

# Additive Schema Strategy Across Sprints

## The Lesson

Committing to "all schema changes are additive — no renames, no type changes, no column removals" across sprints simplifies rollback, prevents breaking deployed instances, and makes schema review trivial: if a migration only has `CREATE TABLE` and `ADD COLUMN`, it can't break existing data.

## Context

A medical portal was built in sprints. Sprint 1 created 11 tables (user, role, permission, organization, session, etc.). Sprint 2 needed to add person profiles, patient/provider/staff types, locations, proxy relationships, navigation items, and consent records — touching both new tables and existing ones (organization needed new columns).

## What Happened

1. Sprint 2's PDR explicitly stated: "No Sprint 1 tables are renamed or restructured — all changes are additive."
2. New tables used FKs to existing Sprint 1 tables (`person.user_id → user.id`, `location.organization_id → organization.id`).
3. The `organization` table gained 6 new columns via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — all nullable, so existing rows remained valid.
4. Sprint 1's `final.plan.md` Phase 07 had already verified forward-compatibility: "confirm User, Role, Permission, Organization tables can be extended without breaking existing data."
5. The Sprint 2 migration could be tested by running it against a Sprint 1 database with real data. No data transformation or backfill needed.

## Key Insights

- **Additive-only is a constraint that simplifies everything downstream.** Migration review becomes "does this only add?" instead of "what does this break?" Rollback is "drop the new tables" instead of "reverse the renames and type changes."
- **Nullable new columns are free.** Adding a nullable column to an existing table with data is a metadata-only operation in PostgreSQL — no table rewrite, no locks on large tables, no backfill needed.
- **Forward-compatibility should be verified in the sprint that creates the schema.** Sprint 1 Phase 07 explicitly checked that Sprint 2's planned additions were possible. This caught potential issues before Sprint 2 started.
- **The constraint has a shelf life.** Additive-only works for early sprints. Eventually, a migration will need to rename a column or change a type. The strategy is "additive as long as possible, then do the rename in a well-planned migration with a backfill plan."

## Applicability

Most valuable in early-stage products where the schema is evolving rapidly and deployments may need to roll back. Less relevant for mature products with stable schemas and established migration tooling. Does not apply to schema changes driven by data model corrections (wrong type, wrong normalization) — those require destructive migrations by definition.

## Related Lessons

- [Seed Data Format Mismatch](seed-data-format-mismatch.md) — seed data is another area where additive changes can silently break if the format contract isn't respected

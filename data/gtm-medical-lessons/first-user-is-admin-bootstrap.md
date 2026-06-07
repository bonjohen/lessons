---
date: 2026-06-03
phase: implementation
---

# First-User-Is-Admin Bootstrap

## The Lesson

When a new system needs an initial administrator but has no user management UI yet, making the first OAuth user automatically an admin solves the bootstrap problem without hardcoded credentials or manual database edits.

## Context

A medical portal used Google OAuth for authentication. The system needed an admin role to manage users, configure AI providers, and control access. But the admin management UI didn't exist yet — it was planned for a later phase. Someone had to be admin before the admin tools existed.

## What Happened

1. The AuthService checked `SELECT count(*) FROM user` during OAuth callback.
2. If the count was zero, the new user was assigned the `admin` role. Otherwise, `user` role.
3. The first person to sign in after deployment became the system administrator.
4. No seed data, environment variables, or manual SQL was needed to bootstrap the admin.
5. The pattern was simple enough to implement in the OAuth callback (5 lines) and test with a single unit test.

## Key Insights

- **The pattern is self-documenting.** "First user is admin" is immediately understandable. No README section explaining "run this SQL to create your admin account."
- **It avoids hardcoded credentials entirely.** No default admin password to rotate, no seed migration with a specific email address. The admin identity comes from whoever deploys and logs in first.
- **The race condition is acceptable.** Two users logging in simultaneously when the database is empty could theoretically both get admin. In practice, deployment is done by one person who logs in immediately. The theoretical race was documented as an accepted limitation rather than over-engineered with database locks.
- **It works exactly once.** After the first user exists, the count is never zero again. The check adds negligible overhead to subsequent logins and doesn't need a feature flag or removal.

## Applicability

Works for internal tools, development portals, and small-team products where the deployer is the first admin. Not suitable for multi-tenant SaaS where tenant admins are provisioned programmatically, or for systems requiring auditable admin provisioning workflows.

## Related Lessons

- [Seed Data Format Mismatch](seed-data-format-mismatch.md) — another seed data pattern that caused issues in the same project

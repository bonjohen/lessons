---
title: Dev Port Registry for Multi-Project Work
summary: A centralized port assignment table in shared developer config prevents localhost collisions when running multiple projects simultaneously.
date: 2026-05-11
phase: implementation
lesson_type: process
status: active
tags: [developer-experience, configuration, localhost, multi-project, ports]
---

# Dev Port Registry for Multi-Project Work

## The Lesson

When a developer works across multiple projects that each run local dev servers, port collisions are inevitable unless ports are assigned centrally. A simple table in shared config — not in each project's individual settings — is the cheapest way to prevent "address already in use" errors and the debugging they trigger.

## Context

A single developer maintains seven active projects (lessons, JobClass, Certification, Artemis, portal, mdreader, epstein), each with an Astro or Vite frontend dev server and most with a FastAPI backend. During active development, two or three of these run simultaneously — for example, the lessons hub frontend plus a source project's dev server to test harvesting behavior. Each framework defaults to a well-known port (Astro: 4321, Vite: 5173, FastAPI/Uvicorn: 8000), creating guaranteed collisions.

## What Happened

1. Initially, each project used its framework's default port. Running two Astro projects simultaneously required manually passing `--port` flags or killing the first server.
2. Some projects had their ports configured in `astro.config.mjs` or `uvicorn` launch scripts, but the assignments were made independently — no single source of truth existed for which port belonged to which project.
3. A port collision during a cross-project test session (lessons hub trying to fetch from a source project's dev server) wasted 20 minutes of debugging before the developer realized both were fighting over port 4321.
4. A port registry was added to the global `~/.claude/CLAUDE.md` as a simple markdown table mapping each project to a frontend port (4331–4337) and a backend port (8011–8017). The range was chosen to avoid conflicts with common defaults (3000, 4321, 5173, 8000, 8080).
5. Each project's config was updated to use its assigned ports. The global table ensures that any new project gets the next available slot, and any tool (including AI assistants) configuring a dev server knows which port to use.

## Key Insights

- **The registry belongs in shared config, not in each project.** If each project defines its own port in isolation, there's no collision detection. The value of the registry is the single view across all projects. `~/.claude/CLAUDE.md` works well for this because it's read by every session regardless of which project is active.

- **Use a dedicated range away from framework defaults.** Ports 4331+ for frontends and 8011+ for backends avoid collisions with Astro's default 4321, Vite's 5173, and Uvicorn's 8000. A developer can still spin up a quick prototype on defaults without conflicting with registered projects.

- **Sequential numbering makes the scheme memorable.** `4331/8011` for project A, `4332/8012` for project B — the pattern is trivial to recall. Gaps in backend numbering (e.g., skipping 8016 for a static-only project) break the pattern, so reserve the backend port even if it's unused today.

- **Static-only projects still get a frontend port.** Even projects without a backend (like mdreader) get a frontend port assignment. This prevents them from colliding with other frontends when both are running.

- **The table is also documentation.** New contributors or tools that need to reference a project's dev URL can look it up without reading each project's config files. It answers "what's running on port 8013?" instantly.

## Examples

Port registry table:

| Project       | Frontend | Backend         |
|---------------|----------|-----------------|
| lessons       | 4331     | 8011            |
| JobClass      | 4332     | 8012            |
| Certification | 4333     | 8013            |
| Artemis       | 4334     | 8014            |
| portal        | 4335     | 8015            |
| mdreader      | 4336     | — (static only) |
| epstein       | 4337     | 8017            |

Next available: frontend `4338`, backend `8018`.

## Applicability

This pattern applies whenever one developer (or team on shared machines) runs multiple local services. It scales to ~50 projects before the table becomes unwieldy. Beyond that, consider a port allocation service or Docker Compose with service discovery.

It does NOT apply to:
- Production deployments (use service discovery or container orchestration)
- Teams where each developer works on only one project at a time
- Projects that use random ephemeral ports by design (test harnesses, etc.)

## Related Lessons

- [Skill-Driven Workflow Automation](skill-driven-workflow-automation.md) — The port registry is consumed by skills that configure dev servers, ensuring consistency across automated workflows

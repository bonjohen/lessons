---
title: The Twelve-Factor App as a Deployment Checklist
summary: The twelve-factor methodology provides a concrete checklist for building deployable, scalable web applications — most violations surface as production incidents.
date: 2024-06-01
phase: deployment
lesson_type: architecture
status: active
tags: [twelve-factor, deployment, architecture, cloud, best-practices]
original_source: https://12factor.net/
---

# The Twelve-Factor App as a Deployment Checklist

## The Lesson

The twelve-factor app methodology, originally written by Heroku engineers, is more useful as a deployment checklist than as a design philosophy. Each factor maps to a specific class of production incident that it prevents.

## Why This Matters

Most deployment failures in web applications trace back to violating one or more of the twelve factors — hardcoded config, divergent environments, persistent local state, or processes that assume they're singletons. Treating the factors as a pre-deploy checklist catches these issues before they reach production.

## The Factors as Incident Prevention

### I. Codebase — One codebase tracked in revision control, many deploys

**Violation pattern:** Teams maintain separate codebases for staging and production, or copy-paste code between services instead of extracting shared libraries.

**Incident it prevents:** "Works in staging, breaks in production" caused by code drift between environments.

### II. Dependencies — Explicitly declare and isolate dependencies

**Violation pattern:** Relying on system-installed packages, assuming a specific Python or Node version, or using globally installed CLI tools in build scripts.

**Incident it prevents:** Build failures when moving to a new CI runner or container image. "But it works on my machine."

### III. Config — Store config in the environment

**Violation pattern:** Hardcoded database URLs, API keys in source code, config files checked into version control that differ per environment.

**Incident it prevents:** Deploying to production with staging database credentials. Leaking API keys in public repos.

### IV. Backing Services — Treat backing services as attached resources

**Violation pattern:** Hardcoding `localhost:5432` for the database, assuming Redis is always at a specific IP, or using the filesystem for queues.

**Incident it prevents:** Inability to swap a failing database for a replica, or migrate from self-hosted to managed services without code changes.

### V. Build, Release, Run — Strictly separate build and run stages

**Violation pattern:** Modifying code directly on production servers, or building artifacts that include environment-specific config.

**Incident it prevents:** "Who changed this file on the production server?" — untraceable changes that can't be rolled back.

### VI. Processes — Execute the app as one or more stateless processes

**Violation pattern:** Storing session data in local memory, writing uploaded files to the local filesystem, or caching in process-local variables.

**Incident it prevents:** Load balancer routes a user to a different instance and their session is gone. Scaling horizontally causes data loss.

### VII. Port Binding — Export services via port binding

**Violation pattern:** Deploying into a shared application server (Tomcat, IIS) that manages the HTTP layer.

**Incident it prevents:** Port conflicts, dependency on specific server versions, inability to run the service in a container.

### VIII. Concurrency — Scale out via the process model

**Violation pattern:** Scaling vertically by adding RAM/CPU instead of horizontally by adding instances. Using threads for everything.

**Incident it prevents:** Hitting the ceiling of a single large instance. Cost scaling that's linear instead of elastic.

### IX. Disposability — Maximize robustness with fast startup and graceful shutdown

**Violation pattern:** Services that take 5 minutes to start, or that lose in-flight requests on SIGTERM.

**Incident it prevents:** Slow deploys, lost requests during rolling updates, inability to autoscale quickly.

### X. Dev/Prod Parity — Keep development, staging, and production as similar as possible

**Violation pattern:** Using SQLite in development and PostgreSQL in production. Mocking external services in staging.

**Incident it prevents:** SQL syntax that works in SQLite but fails in PostgreSQL. Mock/production behavior divergence (the exact scenario that led to the "no mocking the database" lesson).

### XI. Logs — Treat logs as event streams

**Violation pattern:** Writing logs to local files, rotating logs manually, or parsing log files on the production server.

**Incident it prevents:** Running out of disk space from log files. Losing log data when a container is replaced.

### XII. Admin Processes — Run admin/management tasks as one-off processes

**Violation pattern:** Running database migrations by SSH-ing into the production server. Using a custom admin panel that bypasses the normal code path.

**Incident it prevents:** Migrations that run against the wrong database. Admin operations that aren't auditable.

## Key Takeaway

The twelve factors aren't aspirational — they're the minimum bar for avoiding the most common classes of deployment incidents. When reviewing a deployment pipeline, run through the list. Each violation is a latent incident.

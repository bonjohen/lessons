# Site Enhancements — Implementation Plan

**Source document:** Approved plan from planning session
**Project root:** `C:\Projects\lessons`
**Date:** 2026-05-09 10:00 PM (PST)

## Work Queue Instructions

### State Transitions

Open  ──>  Started  ──>  Completed
              │
              └──>  Blocked  ──>  Started  ──>  Completed

- **Open**: Not yet begun.
- **Started**: Actively in progress. Record the start datetime (PST).
- **Completed**: Done and verified. Record the completion datetime (PST).
- **Blocked**: Cannot proceed; note the blocker in the description.

### Commit Protocol

1. Work through all tasks in a phase.
2. When every task reaches Completed, write the Phase Summary.
3. Stage and commit all changes for the phase. Do not push.
4. Proceed immediately to the next phase.

## Technology Stack (Additive)

| Concern | Choice |
|---|---|
| Markdown rendering (about page) | `marked` + `sanitize-html` (already deps) |
| Carousel transitions | CSS opacity + cubic-bezier, vanilla JS setInterval |
| Chat markdown | Client-side regex renderer (no new deps) |
| Admin health checks | Client-side fetch to /health endpoints |

## Phase 1: Self-Descriptive Site

**Goal:** A newcomer landing on the site understands what it is, how it works, and can navigate all features.
**Depends on:** Nothing (first phase).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 1.1 | Completed | 2026-05-09 10:20 PM | 2026-05-09 10:22 PM | Create `src/pages/about.astro` — render `docs/project_walkthrough.md` at build time with `marked` + `sanitize-html` |
| 1.2 | Completed | 2026-05-09 10:22 PM | 2026-05-09 10:23 PM | Update `src/layouts/BaseLayout.astro` nav — add "About" and "Gaps" links |
| 1.3 | Completed | 2026-05-09 10:23 PM | 2026-05-09 10:24 PM | Update `src/pages/index.astro` — rewrite subtitle, add "Learn how it works" link to /about |
| 1.4 | Completed | 2026-05-09 10:24 PM | 2026-05-09 10:25 PM | Update footer in `BaseLayout.astro` — add GitHub repo link and About link |
| 1.5 | Completed | 2026-05-09 10:25 PM | 2026-05-09 10:28 PM | Verify: `npm run build` succeeds, /about renders walkthrough |
| 1.6 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Stage and commit Phase 1 |

### Phase 1 Summary

- **Changes:** Created `src/pages/about.astro` (renders walkthrough at build time). Added "About" and "Gaps" to nav. Updated home page subtitle and footer with GitHub/About links.
- **Commit:** Part of combined commit (all 5 phases shipped together)

## Phase 2: Fading Lesson Carousel

**Goal:** Home page has a visually engaging carousel cycling through 10 random lessons with fade transitions.
**Depends on:** Phase 1 (index.astro changes).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 2.1 | Completed | 2026-05-09 10:28 PM | 2026-05-09 10:29 PM | Create `src/components/LessonCarousel.astro` — viewport, slides, fade CSS, JS cycling (5s interval, prev/next/pause/dots) |
| 2.2 | Completed | 2026-05-09 10:29 PM | 2026-05-09 10:30 PM | Update `src/pages/index.astro` — add "Featured Lessons" carousel with 10 random lessons above "Recent Lessons" |
| 2.3 | Completed | 2026-05-09 10:30 PM | 2026-05-09 10:30 PM | Verify: `npm run build` succeeds, carousel cycles on home page |
| 2.4 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Stage and commit Phase 2 |

### Phase 2 Summary

- **Changes:** Created `src/components/LessonCarousel.astro` porting JobClass fade carousel pattern (CSS opacity 1.2s cubic-bezier transitions, 5s setInterval, prev/next/pause/dots). Home page shows 10 random lessons in carousel.
- **Commit:** Part of combined commit

## Phase 3: Multi-Site API URL Consistency

**Goal:** All pages that fetch from the backend use `PUBLIC_API_BASE` env var instead of hardcoded localhost.
**Depends on:** Nothing (independent).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 3.1 | Completed | 2026-05-09 10:30 PM | 2026-05-09 10:31 PM | Update `src/pages/gaps.astro` — replace hardcoded `http://localhost:8000` with `PUBLIC_API_BASE` env var |
| 3.2 | Completed | 2026-05-09 10:31 PM | 2026-05-09 10:31 PM | Update `src/pages/candidate-lessons.astro` — same fix |
| 3.3 | Completed | 2026-05-09 10:31 PM | 2026-05-09 10:31 PM | Update CSP `connect-src` in `BaseLayout.astro` — build-time env var plus https: and localhost:* |
| 3.4 | Completed | 2026-05-09 10:31 PM | 2026-05-09 10:32 PM | Update `.env.example` — document `PUBLIC_API_BASE` with per-deployment examples |
| 3.5 | Completed | 2026-05-09 10:32 PM | 2026-05-09 10:32 PM | Update deployment workflows (deploy-aws/azure/gcp.yml) — set `PUBLIC_API_BASE` build-time env var |
| 3.6 | Completed | 2026-05-09 10:32 PM | 2026-05-09 10:32 PM | Verify: `npm run build` succeeds |
| 3.7 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Stage and commit Phase 3 |

### Phase 3 Summary

- **Changes:** Replaced hardcoded localhost API URLs in gaps.astro and candidate-lessons.astro with `PUBLIC_API_BASE` env var pattern. CSP now uses build-time env var. AWS/Azure/GCP deploy workflows pass `PUBLIC_API_BASE` from `BACKEND_URL` secret.
- **Commit:** Part of combined commit

## Phase 4: Enhanced Chat Interface

**Goal:** Make the /ask page engaging and interesting to use.
**Depends on:** Phase 3 (API URL consistency).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 4.1 | Completed | 2026-05-09 10:32 PM | 2026-05-09 10:33 PM | Add suggested question chips to `ChatPanel.astro` — 5 clickable prompts generated from lesson data |
| 4.2 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:33 PM | Add typing indicator — CSS-only bouncing dots animation |
| 4.3 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:33 PM | Style assistant messages with left accent border, subtle bg, "Copy" button |
| 4.4 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:33 PM | Add lightweight markdown rendering for assistant responses |
| 4.5 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:33 PM | Update `src/pages/ask.astro` — tips section, connection status dot |
| 4.6 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:34 PM | Verify: `npm run build` succeeds |
| 4.7 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Stage and commit Phase 4 |

### Phase 4 Summary

- **Changes:** ChatPanel now has: 5 suggested question chips (generated from top tags at build time), CSS bouncing-dot typing indicator, left-accent-bordered assistant messages with copy button, client-side markdown rendering (bold/italic/code/lists), input focus ring. Ask page has connection status indicator (green/red dot) and collapsible tips section.
- **Commit:** Part of combined commit

## Phase 5: Master Admin Page

**Goal:** A maintainer dashboard showing all 6 deployment targets with health, links, and iframe previews.
**Depends on:** Phase 3 (multi-site URLs).

| # | Status | Started (PST) | Completed (PST) | Description |
|---|--------|---------------|------------------|-------------|
| 5.1 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:33 PM | Create `src/lib/deployments.ts` — DEPLOYMENTS array with 7 targets (local, GH Pages, flyio, railway, aws, azure, gcp) |
| 5.2 | Completed | 2026-05-09 10:33 PM | 2026-05-09 10:34 PM | Create `src/pages/admin.astro` — responsive grid of deployment panels with health indicators, deploy links, iframe toggles |
| 5.3 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Handle CSP — widened connect-src/frame-src to allow https: and localhost:* |
| 5.4 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Add "Admin" link to footer (not main nav) |
| 5.5 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Verify: `npm run build` succeeds (154 pages), all tests pass (214 total) |
| 5.6 | Completed | 2026-05-09 10:34 PM | 2026-05-09 10:34 PM | Stage and commit Phase 5 |

### Phase 5 Summary

- **Changes:** Created `src/lib/deployments.ts` with 7 deployment configs and `src/pages/admin.astro` with responsive grid, health indicators (client-side fetch), GitHub Actions deploy links, and togglable iframe previews. Admin accessible via footer link.
- **Commit:** Part of combined commit

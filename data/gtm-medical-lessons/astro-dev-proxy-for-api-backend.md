---
phase: deployment
---

# Astro Dev Proxy for API Backend

## The Lesson

When running a frontend dev server and a backend API server on different ports, configuring the frontend's dev proxy to forward API requests eliminates CORS issues during development without touching production configuration.

## Context

A medical portal ran an Astro frontend on port 4341 and a FastAPI backend on port 8021. The frontend needed to call `/api/auth/login/google`, `/api/auth/me`, and other backend endpoints. In production, a reverse proxy would route both to the same origin. In development, the two servers are separate processes on different ports.

## What Happened

1. Without a proxy, frontend `fetch('/api/auth/me')` would hit `localhost:4341/api/auth/me` — the Astro server, which has no API routes. Alternatively, using `fetch('http://localhost:8021/api/auth/me')` would trigger CORS errors because the browser enforces same-origin policy.
2. Astro uses Vite under the hood. Vite's dev server supports `server.proxy` configuration.
3. Added proxy config to `astro.config.mjs`: `vite: { server: { proxy: { '/api': 'http://localhost:8021' } } }`.
4. Frontend code uses relative paths (`/api/auth/me`) everywhere. The Vite dev server transparently proxies these to the backend. Production deployment handles routing separately.
5. No CORS headers needed on the backend. No environment-specific fetch URLs in the frontend. The proxy is dev-only configuration.

## Key Insights

- **Relative API paths are the goal.** Frontend code should use `/api/...`, never `http://localhost:8021/api/...`. Relative paths work in both dev (via proxy) and production (via reverse proxy or same origin).
- **The proxy is a dev server concern, not an application concern.** It lives in the build tool config (`astro.config.mjs`), not in application code. It doesn't ship to production.
- **CORS configuration is a code smell in development.** If you're adding CORS headers to make dev work, you're solving the wrong problem. A dev proxy is simpler and doesn't risk shipping permissive CORS to production.
- **This pattern works for any Vite-based framework.** Astro, Vue, React (Vite), SvelteKit — all use Vite and support the same `server.proxy` configuration.

## Examples

```javascript
// astro.config.mjs
export default defineConfig({
  vite: {
    server: {
      proxy: {
        '/api': 'http://localhost:8021',
      },
    },
  },
});
```

## Applicability

Works for any frontend framework with a dev server that supports proxying (Vite, webpack-dev-server, Next.js rewrites). Does not apply to static-only frontends served from CDN without a dev server, or to backends that need CORS for legitimate cross-origin access (e.g., public APIs consumed by third parties).

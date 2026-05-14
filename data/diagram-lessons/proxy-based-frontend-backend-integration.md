# Proxy-Based Frontend-Backend Integration

## The Lesson

In a split-stack project (separate frontend and backend processes on different ports), configure the frontend dev server to proxy API requests to the backend rather than hardcoding backend URLs or relying on CORS alone. The proxy eliminates cross-origin issues during development, keeps the frontend decoupled from deployment topology, and mirrors production behavior where both are typically served from the same origin.

## Context

A diagram platform ran a FastAPI backend on port 8019 and a Vite + React frontend on port 4339. The frontend needed to call 15+ REST endpoints for project management, entity CRUD, diagram rendering, and exports. During development, the browser's same-origin policy would block requests from `localhost:4339` to `localhost:8019` unless CORS headers were configured or a proxy was used.

## What Happened

1. The backend was configured with permissive CORS middleware (`allow_origins=["*"]`) as a safety net for direct browser-to-API access (e.g., Swagger UI at `localhost:8019/docs`).
2. The frontend's `vite.config.ts` was configured with a proxy rule: any request to `/api/*` is rewritten and forwarded to `http://localhost:8019` with the `/api` prefix stripped.
3. The frontend API client (`lib/api.ts`) uses relative URLs with an `/api` prefix: `fetch("/api/projects")`, `fetch("/api/projects/${name}/entities")`. No hardcoded host, port, or protocol.
4. In the browser, the request flow is: `localhost:4339/api/projects` → Vite dev server proxy → `localhost:8019/projects` → FastAPI → response. The browser sees a same-origin response with no CORS involvement.
5. For production deployment, the same relative `/api` URLs would work behind a reverse proxy (nginx, Caddy) that routes `/api/*` to the backend and everything else to the frontend's static build.

## Key Insights

- **Relative URLs are deployment-agnostic.** `fetch("/api/projects")` works identically in development (via Vite proxy), staging (via nginx), and production (via CDN + API gateway). `fetch("http://localhost:8019/projects")` breaks the moment the backend moves.
- **The proxy makes the frontend unaware of the backend's port.** The port mapping (4339 → 8019) lives in `vite.config.ts`, not in application code. Changing the backend port requires editing one config line, not grepping through components.
- **CORS is a fallback, not the primary strategy.** CORS middleware on the backend (`allow_origins=["*"]`) handles edge cases (direct API access from Swagger UI, curl from scripts, other frontends) but the primary frontend never triggers CORS because the proxy makes requests same-origin.
- **The `/api` prefix is a routing convention, not a backend path.** The backend routes are `/projects`, `/projects/{name}/entities`, etc. — no `/api` prefix. The proxy strips it via `rewrite: (path) => path.replace(/^\/api/, "")`. This keeps the backend's URL structure clean while giving the frontend a clear namespace for API vs. static asset requests.
- **Port registries prevent collisions.** When running multiple split-stack projects simultaneously, each project's frontend and backend ports must be unique. A global port registry (frontend 4331-4339, backend 8011-8019 across 9 projects) prevents the "port already in use" debugging spiral.

## Examples

**Vite proxy configuration:**
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 4339,
    proxy: {
      "/api": {
        target: "http://localhost:8019",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

**Frontend API call** (no hardcoded URL):
```typescript
const res = await fetch("/api/projects");
```

**Production nginx equivalent:**
```nginx
location /api/ {
    proxy_pass http://backend:8019/;
}
location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
}
```

## Applicability

This pattern applies to any project with a separate frontend dev server and backend API: React + FastAPI, Vue + Express, Svelte + Go, etc. It does NOT apply to monolithic frameworks where the backend serves the frontend directly (e.g., Django with templates, Rails with ERB) — there, same-origin is already guaranteed by architecture.

## Related Lessons

- [Phased Plan Execution with Row Tracking](phased-plan-execution-with-row-tracking.md) — the build process that produced the frontend and backend in separate phases

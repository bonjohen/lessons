# Cloudflare Workers

## The Lesson

Cloudflare Workers are serverless JavaScript functions that run at the edge — no server to manage, no container to configure. They wake up on each request, execute, and sleep. For small to medium web apps, they replace traditional backend servers entirely.

## Context

MyReachBand needed a backend to serve dynamic HTML pages (bracelet contact pages), handle user authentication, query a database, and call external APIs (Twilio, Google). The entire backend runs as a single Cloudflare Worker — no Express, no Node.js server, no Docker.

## What Happened

1. Started with a feasibility spike to prove Workers could query a database and return HTML within acceptable latency (< 500ms warm, < 3s cold).
2. Cold-start latency was 403ms, warm requests were ~50ms. Well within thresholds.
3. Built the entire app as a single Worker entry point (`src/worker.js`) that routes requests based on URL path parsing.
4. The Worker grew to handle public scan pages, user authentication, OAuth2, admin dashboards, phone verification, and PDF generation — all from one `fetch()` handler.
5. Deployed with `wrangler deploy` — bundles all JS files and uploads in ~3 seconds. No build pipeline, no CI/CD required.
6. Added dev/prod environments via `wrangler.toml` `[env.dev]` blocks — each gets its own Worker name, database, and secrets.

## Key Insights

- **Workers are V8 isolates, not containers.** They start in milliseconds, not seconds. There's no filesystem, no `require('fs')`, no persistent process. Each request is independent.
- **No npm ecosystem by default.** Workers use Web APIs (`fetch`, `crypto.subtle`, `URL`, `Response`). Node.js modules don't work unless they're pure JavaScript with no native dependencies. Libraries like `qrcode` (pure JS) work; libraries like `sharp` (native bindings) don't.
- **Route matching is manual.** There's no Express-style router. You parse `url.pathname`, split it into parts, and match with `if` statements. This is simpler than it sounds for apps with < 50 routes.
- **`wrangler deploy` replaces CI/CD for small projects.** It bundles, uploads, and deploys in one command. The code is live in seconds. For a solo developer, this is dramatically faster than GitHub Actions → build → deploy pipelines.
- **Environment variables are "secrets" or "bindings."** Sensitive values go in `wrangler secret put`. Non-sensitive config goes in `wrangler.toml`. Database connections are "bindings" — declared in the toml, available as `env.DB`.
- **Free tier is generous.** 100,000 requests/day, no cold-start charges. A personal product can run indefinitely at zero cost.

## Examples

### Minimal Worker
```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/hello") {
      return new Response("Hello!", { headers: { "Content-Type": "text/plain" } });
    }
    return new Response("Not found", { status: 404 });
  },
};
```

### Reading from D1 database
```javascript
const row = await env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(userId).first();
if (!row) return new Response("Not found", { status: 404 });
return new Response(JSON.stringify(row), { headers: { "Content-Type": "application/json" } });
```

### Setting a secret
```bash
printf "my-secret-value" | npx wrangler secret put MY_SECRET
# Available in Worker as env.MY_SECRET
```

## Applicability

Workers are ideal for: server-rendered HTML apps, API backends, webhook handlers, and edge-computed pages. They are NOT ideal for: long-running tasks (30s CPU limit), apps that need filesystem access, or apps with heavy native dependencies (image processing, video encoding).

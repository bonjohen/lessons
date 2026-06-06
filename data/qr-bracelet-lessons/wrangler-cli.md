# Wrangler CLI

## The Lesson

Wrangler is the CLI tool that manages the entire Cloudflare Workers lifecycle — creating databases, setting secrets, deploying code, tailing logs, and managing environments. It replaces what would otherwise be a CI/CD pipeline, a deployment script, and a cloud console.

## Context

MyReachBand uses Wrangler for all Cloudflare operations: creating D1 databases, applying migrations, deploying the Worker, setting secrets (Twilio credentials, Google OAuth keys, session secrets), and managing dev/prod environments. No GitHub Actions or other CI/CD tools are involved.

## What Happened

1. Installed Wrangler via `npx wrangler` (no global install needed — runs from the project).
2. Authenticated with `npx wrangler login` — opens a browser for OAuth. The token is stored locally and expires after ~24 hours.
3. Configured `wrangler.toml` with the Worker name, D1 binding, and compatibility date.
4. Learned that `wrangler deploy` bundles all `src/` files and uploads them in ~3 seconds. No build step, no Docker, no artifact management.
5. Hit a critical bug: `echo "value" | wrangler secret put NAME` adds a trailing newline to the secret. Google OAuth broke because the client ID had `\n` appended. Fixed by using `printf` instead of `echo`.
6. Set up dev/prod environments with `[env.dev]` blocks in `wrangler.toml`. Each environment gets separate secrets (`wrangler secret put NAME -e dev`), a separate database, and a separate Worker URL.

## Key Insights

- **Use `printf`, never `echo`, when piping secrets.** `echo` adds a trailing newline that silently breaks API tokens, OAuth client IDs, and any credential that's compared byte-for-byte. `printf "value" | npx wrangler secret put NAME` is safe.
- **OAuth tokens expire.** `wrangler login` tokens last ~24 hours. If you get auth errors the next day, re-run `wrangler login`.
- **`wrangler deploy` is not `git push`.** Deploying to production is a separate action from committing code. Treat production deploys like pushes — require explicit authorization each time.
- **Environments are separate Workers.** `wrangler deploy -e dev` creates a Worker named `{name}-dev`. It has its own URL, its own secrets, and its own database bindings. They share no state.
- **`wrangler tail` shows live logs.** `npx wrangler tail -e dev --format pretty` streams console output and errors from the Worker in real time. Essential for debugging production errors like the 1101 "Worker threw exception" page.
- **Don't let `.env` conflict with Wrangler.** Wrangler auto-reads `.env` files. If your `.env` has `CF_API_TOKEN` or `CLOUDFLARE_API_TOKEN`, Wrangler will use it instead of OAuth — and if it's expired, everything breaks silently.

## Examples

### Common commands
```bash
# Authenticate
npx wrangler login

# Deploy to production
npx wrangler deploy

# Deploy to dev
npx wrangler deploy -e dev

# Set a secret (use printf, not echo!)
printf "my-secret" | npx wrangler secret put SECRET_NAME
printf "my-secret" | npx wrangler secret put SECRET_NAME -e dev

# List secrets
npx wrangler secret list
npx wrangler secret list -e dev

# Create a D1 database
npx wrangler d1 create my-database

# Apply migrations
npx wrangler d1 migrations apply my-database --remote

# Query D1 directly
npx wrangler d1 execute my-database --remote --command="SELECT * FROM users"

# Tail logs
npx wrangler tail -e dev --format pretty
```

### wrangler.toml with environments
```toml
name = "my-app"
main = "src/worker.js"
compatibility_date = "2024-01-01"
workers_dev = false

[[d1_databases]]
binding = "DB"
database_name = "my-app"
database_id = "prod-id-here"
migrations_dir = "migrations"

[env.dev]
name = "my-app-dev"
workers_dev = false

[[env.dev.d1_databases]]
binding = "DB"
database_name = "my-app-dev"
database_id = "dev-id-here"
migrations_dir = "migrations"
```

## Applicability

Wrangler is specific to Cloudflare Workers. The mental model — "CLI deploys code, manages secrets, creates infrastructure" — applies to other serverless CLIs like `vercel`, `netlify`, and `aws sam`.

## Related Lessons

- [Cloudflare Workers](cloudflare-workers.md) — Wrangler deploys and manages Workers
- [Echo vs Printf for Secrets](echo-vs-printf-for-secrets.md) — the newline bug that breaks credentials

---
title: "Echo vs Printf for CLI Secrets"
summary: "When piping a value to a CLI tool that stores secrets, `echo` adds a trailing newline that becomes part of the stored value. This silently breaks any credential that's compared byte-for-byte — OAuth client IDs, API tokens, webhook secrets. Always use `printf` instead."
date: 2026-06-06
lesson_type: implementation
tags: [cloudflare, serverless, authentication, sms, devops]
---
# Echo vs Printf for CLI Secrets

## The Lesson

When piping a value to a CLI tool that stores secrets, `echo` adds a trailing newline that becomes part of the stored value. This silently breaks any credential that's compared byte-for-byte — OAuth client IDs, API tokens, webhook secrets. Always use `printf` instead.

## Context

MyReachBand stores Twilio credentials and Google OAuth keys as Cloudflare Worker secrets via `wrangler secret put`. The secrets are used in HTTP requests where the exact string must match what the remote service expects. A single invisible character at the end breaks the match.

## What Happened

1. Set Google OAuth client ID with `echo "790486..." | npx wrangler secret put GOOGLE_CLIENT_ID`.
2. Google OAuth returned `redirect_uri_mismatch` on every login attempt.
3. Verified the redirect URI was correct in the Google console. Verified the Worker code constructed the URL properly.
4. Spent significant time debugging the OAuth callback handler, adding try/catch blocks, checking state cookies.
5. Eventually realized `echo` adds `\n` to the value. The stored client ID was `790486...\n`, which got URL-encoded into the redirect URI, which didn't match what Google had registered.
6. Fixed with `printf "790486..." | npx wrangler secret put GOOGLE_CLIENT_ID`. No newline, exact match, OAuth worked immediately.

## Key Insights

- **`echo` always adds a newline.** On every platform (bash, zsh, PowerShell), `echo "value"` outputs `value\n`. This is by design — echo is for terminal output, not for piping binary-exact values.
- **`printf` does not add a newline.** `printf "value"` outputs exactly `value`. Use it whenever the trailing bytes matter.
- **The error message won't help you.** Google says `redirect_uri_mismatch`. Twilio says `invalid credentials`. Neither says "your secret has a trailing newline." You have to know to look for it.
- **Secrets can't be read back.** `wrangler secret list` shows names, not values. You can't inspect what was stored to verify it's correct. The only test is whether the integration works.
- **Node.js `process.stdin` is safest.** For maximum reliability: `node -e "process.stdout.write('value')" | npx wrangler secret put NAME`. This guarantees no trailing characters regardless of shell.

## Examples

### Bad
```bash
echo "GOCSPX-abc123" | npx wrangler secret put GOOGLE_CLIENT_SECRET
# Stores: "GOCSPX-abc123\n" — broken
```

### Good
```bash
printf "GOCSPX-abc123" | npx wrangler secret put GOOGLE_CLIENT_SECRET
# Stores: "GOCSPX-abc123" — correct
```

### Safest (Node.js)
```bash
node -e "process.stdout.write('GOCSPX-abc123')" | npx wrangler secret put GOOGLE_CLIENT_SECRET
```

## Applicability

This applies to any CLI that reads secrets from stdin: `wrangler secret put`, `aws ssm put-parameter`, `vault kv put`, `kubectl create secret`. The newline problem is universal. It does NOT apply when the CLI reads from a file or prompts interactively — those typically trim whitespace.

## Related Lessons

- [Wrangler CLI](wrangler-cli.md) — the tool where this bug manifests
- [Google OAuth2](google-oauth2.md) — the integration that broke due to this bug

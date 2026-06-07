---
title: Preflight Gates as Local CI
summary: Run the same checks CI will run before pushing to prevent the most common build failure patterns
date: 2026-05-10
phase: execution
lesson_type: process
status: active
tags: [testing, ci, preflight, lint, automation, workflow]
---

# Preflight Gates as Local CI

## The Lesson

The fastest way to fix a CI failure is to never push it. A local preflight script that mirrors your CI checks — lint, format, tests, script existence, optional dependency detection — catches 90% of build failures before they waste a round-trip to the remote runner. The key insight is that preflight should be identical to CI, not a subset of it.

## Context

Lessons Hub has a CI pipeline that runs on every push: harvest lessons, validate schemas, build the corpus, lint with ruff, run pytest, build the Astro site, and deploy. A CI run takes 3-5 minutes. When it fails, diagnosing the failure from workflow logs, fixing locally, pushing again, and waiting for another run costs 10-15 minutes minimum. The most common failures were entirely preventable: unformatted code, a test that passes locally but fails in CI due to a missing env var, or a workflow referencing a script that was renamed.

## What Happened

1. Repeated CI failures from preventable causes (formatting, import errors, missing scripts) led to the creation of a preflight skill — a single command that runs before every push.
2. The first version just ran `ruff check` and `pytest`. It caught formatting issues but missed the more subtle failures.
3. After a CI failure from a module-level import of `boto3` (not installed in CI), optional dependency detection was added: grep for imports of known-optional packages and verify they're inside function scope, not at module level.
4. After a workflow referenced `scripts/build.sh` which had been renamed to `scripts/build-full.sh`, script existence checking was added: parse workflow YAML files for `run:` commands and verify referenced scripts exist.
5. The mature preflight runs five gates in sequence, stopping at the first failure:
   - **Format:** `ruff format --check` (diff only, no modification)
   - **Lint:** `ruff check` (catches unused imports, undefined names, style violations)
   - **Tests:** `python -m pytest` (fast unit tests only — skip integration markers)
   - **Script audit:** Verify all scripts referenced in `.github/workflows/*.yml` exist
   - **Optional deps:** Scan for module-level imports of cloud SDKs that aren't in base requirements

## Key Insights

- **Preflight must mirror CI exactly, not approximate it.** If CI runs `ruff check --select E,F,W`, preflight must run the same command with the same flags. Divergence between local and CI checks is worse than no preflight at all — it builds false confidence.

- **Stop at first failure.** A developer who sees 47 format errors, 3 lint warnings, and 2 test failures will fix the format errors and forget the rest. Sequential gates with early exit focus attention on one problem at a time.

- **Script existence checks prevent the dumbest CI failures.** Parsing workflow YAML for `run: ./scripts/foo.sh` and checking `[ -f scripts/foo.sh ]` is trivial but catches renames, deletions, and typos that otherwise only surface after a push and 3-minute wait.

- **Optional dependency detection prevents the most confusing CI failures.** `ModuleNotFoundError: No module named 'boto3'` in CI when all tests pass locally is baffling the first time. The pattern: scan Python files for `import boto3` (or azure, google-cloud, etc.) at module level (column 0, not inside a function) and warn.

- **Make it one command.** If preflight requires remembering which checks to run, developers won't run it. A single entry point (`/preflight`, `make preflight`, `npm run preflight`) with no arguments is the only version that gets used consistently.

## Implementation Guide

### Step 1: Inventory your CI checks

Read your CI workflow file and list every check that can run locally. For a typical Python + static site project:

```bash
# Extract run commands from your GitHub Actions workflow
grep "run:" .github/workflows/*.yml
```

Classify each check as **deterministic** (lint, format, unit tests — will produce the same result locally as in CI) or **environment-dependent** (integration tests against a CI database, deployment steps). Preflight only includes the deterministic checks.

### Step 2: Create a preflight script

Write a bash script (or npm script, Makefile target, etc.) that runs each check in sequence with `set -e` so it stops at the first failure:

```bash
#!/bin/bash
set -e

echo "=== Gate 1: Format ==="
ruff format --check src/ tests/

echo "=== Gate 2: Lint ==="
ruff check src/ tests/

echo "=== Gate 3: Tests ==="
python -m pytest tests/ -x --timeout=60

echo "=== PREFLIGHT PASS ==="
```

The flags must match your CI configuration exactly. If CI runs `ruff check --select E,F,W`, preflight must use the same flags.

### Step 3: Add project-specific gates

Beyond the standard lint/format/test gates, add checks for failure patterns specific to your project:

**Script existence audit** (if your CI workflow references shell scripts):
```bash
echo "=== Gate 4: Script Audit ==="
for workflow in .github/workflows/*.yml; do
  grep -oP '(?<=run: \./)\S+' "$workflow" | while read script; do
    [ -f "$script" ] || { echo "FAIL: $workflow references missing $script"; exit 1; }
  done
done
```

**Optional dependency scan** (if your project has lazy-imported packages):
```bash
echo "=== Gate 5: Optional Deps ==="
OPTIONAL="boto3|azure|google.cloud"
if grep -rn "^import \($OPTIONAL\)\|^from \($OPTIONAL\)" src/; then
  echo "FAIL: Module-level import of optional dependency"
  exit 1
fi
```

### Step 4: Make it one command

Register the preflight as a single, argument-free command that developers can run without thinking:

```json
// package.json
{ "scripts": { "preflight": "bash scripts/preflight.sh" } }
```
```makefile
# Makefile
preflight:
	bash scripts/preflight.sh
```

The fewer keystrokes, the more likely it gets used. `npm run preflight` or `make preflight` is the maximum acceptable friction.

### Step 5: Wire preflight into your push workflow

The highest-value integration point is right before `git push`. Options:

- **Git pre-push hook:** Runs automatically on every push. Add to `.git/hooks/pre-push` or use a hook manager like Husky.
- **CI/push skill:** If using an AI assistant, add preflight as a required step in the push workflow so it runs automatically.
- **Manual habit:** Run preflight before pushing. This works for solo developers but doesn't scale to teams.

```bash
# .git/hooks/pre-push (make executable with chmod +x)
#!/bin/bash
echo "Running preflight..."
npm run preflight || { echo "Preflight FAILED — push aborted"; exit 1; }
```

## Examples

### Preflight Script Structure

```bash
#!/bin/bash
set -e

echo "=== Gate 1: Format ==="
ruff format --check backend/ scripts/ tests/

echo "=== Gate 2: Lint ==="
ruff check backend/ scripts/ tests/

echo "=== Gate 3: Tests ==="
python -m pytest tests/ backend/tests/ -x --timeout=60

echo "=== Gate 4: Script Audit ==="
for workflow in .github/workflows/*.yml; do
  grep -oP '(?<=run: \./)\S+' "$workflow" | while read script; do
    if [ ! -f "$script" ]; then
      echo "FAIL: $workflow references $script which does not exist"
      exit 1
    fi
  done
done

echo "=== Gate 5: Optional Deps ==="
# Module-level imports of packages not in base requirements
OPTIONAL="boto3|botocore|azure|google.cloud|openai"
if grep -rn "^import \($OPTIONAL\)\|^from \($OPTIONAL\)" backend/ scripts/; then
  echo "FAIL: Module-level import of optional dependency (move to function scope)"
  exit 1
fi

echo "=== PREFLIGHT PASS ==="
```

### Common CI Failures Prevented

| Failure pattern | Preflight gate | Time saved |
|----------------|----------------|------------|
| `ruff` format check fails | Gate 1: Format | 6-10 min |
| Unused import breaks lint | Gate 2: Lint | 6-10 min |
| Test passes locally, fails in CI (env) | Gate 3: Tests (with CI-like env) | 10-15 min |
| Workflow references deleted script | Gate 4: Script Audit | 10-15 min |
| `ModuleNotFoundError` for optional dep | Gate 5: Optional Deps | 10-15 min |

### Integration with Push Workflow

```
Developer finishes work
    │
    ▼
Run preflight (one command)
    │
    ├── FAIL → Fix the issue, re-run
    │
    └── PASS → Push with confidence
         │
         ▼
    CI runs (mirrors preflight)
         │
         └── Rarely fails (preflight caught it)
```

## Applicability

This pattern works for any project where:
- CI takes more than 60 seconds (local preflight is instant feedback vs minutes of waiting)
- Multiple people push to the same repo (each person's broken push costs everyone's attention)
- The CI pipeline has deterministic checks (lint, format, tests — not flaky integration tests)

Preflight is less valuable when:
- CI is fast (< 30 seconds) — the round-trip cost is low enough that local checks add friction without proportional benefit
- The CI environment is fundamentally different from local (e.g., different OS, different database version) — preflight can't simulate the real thing
- The team already has pre-commit hooks that cover the same checks (don't duplicate)

## Related Lessons

- [Test Pyramid for Static Sites](test-pyramid-for-static-sites.md) — preflight runs the unit layer of the pyramid
- [Mock vs Live Testing Trade-offs](mock-vs-live-testing-trade-offs.md) — preflight skips live tests (fast feedback over completeness)
- [Acceptance Testing with Playwright](acceptance-testing-with-playwright.md) — acceptance tests run post-deploy, not in preflight

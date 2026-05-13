# Preflight Checks Prevent Push-then-Fix Cycles

## The Lesson

Running the same lint, format, and test checks locally before pushing catches failures that would otherwise require a push-fix-push cycle through CI. The cost of a local preflight is seconds; the cost of a CI round-trip is minutes plus noise (failed build notifications, red badges, extra commits). A preflight gate between commit and push eliminates the most common CI failure patterns.

## Context

A project with Python (ruff for lint/format, pytest for tests) and Node.js (Astro build) had CI workflows that ran `ruff check`, `ruff format --check`, `pytest`, and `npm run build`. After completing the implementation and committing the XSS fix, a push was prepared. The push workflow included a preflight step that ran the same checks CI would run, locally, before authorizing the push.

## What Happened

1. The XSS fix was committed and the push workflow began. Before pushing, the preflight skill ran 7 gates: Python lint, Python format, Node lint, Python tests, Node tests, CI script existence, and build smoke test.
2. Gate 1b (Python format) failed: `ruff format --check` reported 2 files would be reformatted — `backend/app/adapters/vector/chromadb.py` and `backend/app/rag/generator.py`.
3. These files had been written during Phase 5 and never reformatted. They passed `ruff check` (lint) but not `ruff format --check` (formatting). The CI workflow ran both, so this would have been a CI failure.
4. The fix was immediate: `ruff format` on the two files, commit the formatting fix, re-run preflight. All 7 gates passed on the second run.
5. Without the preflight gate, the sequence would have been: push → CI fails on format check → read CI logs → run format locally → commit fix → push again. Two pushes, two CI runs, one wasted round-trip.
6. The preflight completed in under 5 seconds. A CI round-trip on this project takes approximately 50 seconds (build job) plus GitHub Actions queue time.

## Key Insights

- **Format checks are the most common preventable CI failure.** Unlike lint errors or test failures, format issues are always auto-fixable and never indicate a real bug. They're pure friction — a preflight gate with `ruff format --check` eliminates them entirely.
- **Preflight must match CI exactly.** The value of a local preflight comes from running the same checks CI runs. If CI runs `ruff check scripts/ backend/` but preflight runs `ruff check .`, they'll diverge. Read the CI workflow files to determine the exact commands and scopes.
- **The gate must block, not warn.** A preflight that prints "format issues found" but still pushes is useless. The push should not proceed until preflight passes. In this project, the push workflow refused to create the push authorization sentinel until preflight returned PASS.
- **Preflight catches local-only state.** The two unformatted files had been committed during Phase 5 — they'd been in the repo for 5 commits without being caught. Tests passed, lint passed, but format didn't. Preflight catches this class of "always been wrong, never noticed" issues.

## Examples

**Preflight output showing failure:**
```
Gate 1: Python lint/format ........... FAIL
  Would reformat: backend/app/adapters/vector/chromadb.py
  Would reformat: backend/app/rag/generator.py
  2 files would be reformatted, 25 files already formatted

Result: FAIL (1 failure, 0 warnings)
```

**Preflight output after fix:**
```
Gate 1: Python lint/format ........... PASS
Gate 3: Python tests ................. PASS (39 passed)
Gate 7: Build smoke test ............. PASS

Result: PASS (0 failures, 0 warnings)
```

## Applicability

This applies to any project with CI checks that can be run locally. It's most valuable when CI is slow (queue times, large test suites) or when the team has a pattern of "fix CI" commits. It does NOT replace CI — CI runs in a clean environment and catches environment-specific issues (missing dependencies, OS differences). Preflight catches the 80% of CI failures that are purely local mistakes.

## Related Lessons

- [CI Dependency Lists Drift from pyproject.toml](ci-dependency-drift.md) — preflight would not catch this particular CI issue (it's about environment divergence, not local checks), illustrating the complementary nature of preflight and CI
- [Structured Code Review as a Phase Gate](structured-review-as-phase-gate.md) — another verification layer, operating at a broader scope

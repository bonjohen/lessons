# CI Dependency Lists Drift from pyproject.toml

## The Lesson

When CI workflows hand-maintain `pip install` commands that duplicate what `pyproject.toml` already declares, the two lists will drift. New dependencies added to `pyproject.toml` will be missing in CI, causing build failures that can't be reproduced locally. The fix is to use `pip install .` so `pyproject.toml` is the single source of truth.

## Context

A Python + Node.js project had two CI workflows (build-deploy and PR-check) and two `pyproject.toml` files (root for pipeline scripts, `backend/` for the FastAPI app). Each workflow had `pip install` commands listing packages by name without version constraints. The root `pyproject.toml` declared the same packages with version constraints. The backend's `pyproject.toml` was not referenced by CI at all — the PR-check workflow had its own inline `pip install fastapi uvicorn pydantic chromadb ollama httpx`.

## What Happened

1. Phase 1 created `pyproject.toml` with `python-frontmatter>=1.1`, `python-slugify>=8.0`, `PyYAML>=6.0` and dev extras for `pytest>=8` and `ruff>=0.11`.
2. Phase 6 created CI workflows. Instead of `pip install .`, the workflows used `pip install python-frontmatter python-slugify PyYAML` — no version constraints, manually duplicated.
3. The PR-check workflow additionally installed backend dependencies inline: `pip install fastapi uvicorn pydantic chromadb ollama httpx` — again without version constraints and without referencing `backend/pyproject.toml`.
4. A structured code review flagged this as finding F-03 (High severity). The workflows would silently break any time a new dependency was added to either `pyproject.toml` — the developer would add it locally, tests would pass, and CI would fail on a missing import.
5. The recommended fix: replace `pip install <list>` with `pip install .` for the root project and `pip install ./backend[dev]` for the backend, making `pyproject.toml` the single source of truth.

## Key Insights

- **Two sources of truth always diverge.** If the same information exists in `pyproject.toml` and in a CI workflow `run:` step, they will drift. The question is not "will they diverge" but "how long until they diverge." This is true for any duplicated declaration: Docker build args, Makefile variables, deployment scripts.
- **Missing version constraints in CI are a time bomb.** `pip install pydantic` installs whatever version is current. If Pydantic releases a breaking change, CI breaks even though the code hasn't changed. `pyproject.toml` with `pydantic>=2` prevents this — but only if CI actually reads it.
- **`pip install .` is always correct for projects with pyproject.toml.** It installs the project and all declared dependencies in one command, respects version constraints, and works identically in CI and locally. The only reason to use `pip install <package>` is when there is no project metadata file.
- **Backend subprojects need explicit installation too.** A monorepo with `backend/pyproject.toml` needs `pip install ./backend` in CI, not a hand-maintained list. The `[dev]` extra installs test dependencies.

## Examples

**Before (fragile):**
```yaml
# build-deploy.yml
- run: pip install python-frontmatter python-slugify PyYAML

# pr-check.yml
- run: pip install python-frontmatter python-slugify PyYAML pytest ruff
- run: |
    pip install fastapi uvicorn pydantic chromadb ollama httpx
    cd backend && pytest tests/
```

**After (single source of truth):**
```yaml
# build-deploy.yml
- run: pip install .

# pr-check.yml
- run: pip install .[dev] ./backend[dev]
```

## Applicability

This applies to any project where CI installs Python dependencies. It also applies analogously to Node.js projects that use `npm install <package>` in CI instead of `npm ci` (which reads `package-lock.json`). It does NOT apply to projects without a `pyproject.toml` or `setup.py` — scripts that are truly standalone may need explicit `pip install` commands.

## Related Lessons

- [Preflight Checks Prevent Push-then-Fix Cycles](preflight-prevents-push-fix-cycles.md) — preflight would not have caught this particular issue (it's a CI-only divergence), but both lessons address the theme of catching problems before they reach CI

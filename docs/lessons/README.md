# Lessons Learned

Standalone learning resources extracted from real project work on Lessons Hub. Each lesson captures a pattern, mistake, or decision and is written so a developer on a completely different project can understand and apply it.

## Architecture & Design

- [Adapter Pattern for Multi-Cloud Portability](adapter-pattern-for-multi-cloud.md) — Abstract base classes with minimal interfaces let the same RAG pipeline run on four cloud providers
- [Lazy Imports for Optional Cloud Dependencies](lazy-imports-for-optional-dependencies.md) — Deferring SDK imports to runtime enables testing without real dependencies
- [RAG Corpus Chunking Strategy](rag-corpus-chunking-strategy.md) — Splitting at H2 headings with stable IDs and content hashes for incremental re-indexing
- [Rule-Based Gap Detection Without ML](rule-based-gap-detection.md) — Seven heuristic rules detect corpus gaps without training data
- [Harvester Design Decisions](harvester-design-decisions.md) — Key choices in building the lesson harvester

## Process & Methodology

- [Five-Stage Design-to-Execution Workflow](five-stage-design-to-execution.md) — Design, PDR, Plan, Execute, Commit with table-driven task tracking
- [Code Review as Requirements Source](code-review-as-requirements-source.md) — Systematic triage turns review findings into a traceable requirements backlog
- [Validation Severity Model](validation-severity-model.md) — Why warnings never fail the build
- [Skill-Driven Workflow Automation](skill-driven-workflow-automation.md) — Composable slash-command skills enforce guardrails and eliminate workflow friction

## Deployment & Infrastructure

- [Phased Multi-Cloud Infrastructure](phased-multi-cloud-infrastructure.md) — Three cloud stacks with OIDC federation, built in isolated phases
- [GitHub Pages Build Pipeline](github-pages-build-pipeline.md) — GitHub Actions workflow for harvest, validate, build, and deploy
- [Static Search with Pagefind](static-search-with-pagefind.md) — Full-text search on a static site with no backend

## Testing

- [Live Infrastructure for Integration Testing](live-infrastructure-for-integration-testing.md) — When local services are already running, skip mocks and test the real pipeline end-to-end
- [Acceptance Testing with Playwright](acceptance-testing-with-playwright.md) — BFS link crawling and smoke tests against live URLs catch broken navigation before users do
- [Test Pyramid for Static Sites](test-pyramid-for-static-sites.md) — Layer unit, integration, and acceptance tests so each catches what the others cannot
- [Mock vs Live Testing Trade-offs](mock-vs-live-testing-trade-offs.md) — Decision framework for when to mock and when to test against real infrastructure
- [Preflight Gates as Local CI](preflight-gates-as-local-ci.md) — Run the same checks CI will run before pushing to prevent common build failures
- [Testing Cross-Repo Content Pipelines](testing-cross-repo-content-pipelines.md) — Validation severity, slug collision detection, and schema enforcement for harvested content

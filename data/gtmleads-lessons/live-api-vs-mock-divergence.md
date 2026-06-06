---
title: "Live API vs Mock Divergence"
summary: "Mock-based tests validate your code's logic, not your assumptions about the external API. When an adapter passes all mock tests but fails against the real API, the bug is almost always in the mock — you encoded incorrect assumptions about field names, response structure, or protocol behavior."
date: 2026-06-06
lesson_type: testing
tags: [testing, api, data-modeling, pipeline, python]
---
# Live API vs Mock Divergence

## The Lesson

Mock-based tests validate your code's logic, not your assumptions about the external API. When an adapter passes all mock tests but fails against the real API, the bug is almost always in the mock — you encoded incorrect assumptions about field names, response structure, or protocol behavior.

## Context

GTMLeads has 10 API adapters that each fetch data from a public source, normalize the response into a common `RawSignal` format, and feed it into a scoring/dedup pipeline. All adapter tests use `respx` (an httpx mock library) to simulate API responses, ensuring the test suite runs without network calls. After the initial adapter expansion shipped with 221 passing tests, live smoke tests against real APIs revealed two failures that the mocks had masked.

## What Happened

1. SEC EDGAR adapter was built against PDR-documented field names: `accessionNo`, `cik`, `companyName`, `formType`, `filedAt`. All mock tests used these field names and passed.
2. Live testing revealed the EDGAR full-text search API actually returns `adsh`, `ciks` (array), `display_names` (array), `form`, and `file_date`. The PDR's field names came from a different EDGAR endpoint (the company search API), not the one the adapter actually calls.
3. arXiv adapter used `http://export.arxiv.org/api/query`. The real API returns a 301 redirect to HTTPS. httpx follows redirects by default, so this worked in production — but added latency and wasted a request. The mock test used the HTTP URL directly and never tested redirect behavior.
4. The fix for EDGAR was to support both field-name conventions in `normalize()` — checking the real API names first, falling back to the PDR-assumed names. This makes the adapter forward-compatible if EDGAR changes its response format again.
5. A new test was added specifically for the live EDGAR response format, using a fixture captured from a real API call.

## Key Insights

- **Mocks encode assumptions, not facts.** When you write `respx.get(url).mock(return_value=Response(200, json={"accessionNo": ...}))`, you are asserting that the real API returns `accessionNo`. If that assertion is wrong, the mock silently confirms your mistake.
- **Capture real responses as golden fixtures.** The fix included adding a test with an actual EDGAR response payload. This single fixture is worth more than any number of hand-crafted mocks because it encodes what the API actually returns, not what you think it returns.
- **Protocol-level details slip through mocks.** The arXiv HTTP→HTTPS redirect was invisible to mock tests because respx intercepts at the transport layer, never making a real connection. Redirect behavior, TLS certificate issues, and content encoding are all in this blind spot.
- **Support both old and new field names when feasible.** The EDGAR fix didn't rip out the old field names — it added the new ones with priority. This is cheap defensive coding: if the API has multiple endpoints or changes its format, the adapter degrades gracefully instead of breaking.
- **One live request per adapter during development is sufficient.** You don't need a full integration test suite against live APIs. A single request, captured and examined, would have caught both bugs before they were committed.

## Examples

**Before (SEC EDGAR normalize — PDR field names only):**
```python
accession = (raw_payload.get("accessionNo") or "").replace("-", "")
cik = raw_payload.get("cik", "")
company = raw_payload.get("companyName") or "Unknown"
```

**After (dual-convention support):**
```python
accession = raw_payload.get("adsh") or raw_payload.get("accessionNo") or ""
ciks = raw_payload.get("ciks") or []
cik = ciks[0] if ciks else raw_payload.get("cik", "")
display_names = raw_payload.get("display_names") or []
company = display_names[0] if display_names else raw_payload.get("companyName") or "Unknown"
```

## Applicability

This lesson applies to any system that integrates with third-party APIs using mock-based testing. It is especially relevant when the API documentation is incomplete, when the adapter was built from docs rather than from observed responses, or when the API has multiple endpoints with subtly different response formats.

It does NOT apply to internal service-to-service mocks where you control both sides and the contract is enforced by shared types or schema validation.

## Related Lessons

- [Phased Adapter Expansion](phased-adapter-expansion.md) — the broader process that surfaced these bugs
- [Base Adapter ABC Pattern](base-adapter-abc-pattern.md) — the normalize() contract where the field-name bug lives

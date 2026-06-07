---
title: "Base Adapter ABC Pattern"
summary: "When integrating with multiple external APIs that share a common pipeline contract, define an abstract base class that handles cross-cutting concerns (rate limiting, timeouts, credential redaction, error classification) and requires subclasses to implement only the source-specific logic (`fetch` and..."
date: 2026-05-20
lesson_type: architecture
tags: [authentication, pipeline, python]
---
# Base Adapter ABC Pattern

## The Lesson

When integrating with multiple external APIs that share a common pipeline contract, define an abstract base class that handles cross-cutting concerns (rate limiting, timeouts, credential redaction, error classification) and requires subclasses to implement only the source-specific logic (`fetch` and `normalize`). This reduces each new adapter to ~60-140 lines of domain logic and eliminates entire categories of bugs.

## Context

GTMLeads integrates with 10 public APIs (GitHub, Federal Register, NVD, CISA KEV, OpenAlex, SEC EDGAR, arXiv, HN Algolia, Semantic Scholar, Reddit). Each API has different authentication, rate limits, response formats, and error conventions. The pipeline runner needs to call each adapter identically: fetch raw results, normalize to a common format, score, dedup, and store. Without a shared contract, each adapter would need its own rate-limiting logic, timeout handling, and error recovery — multiplying bugs by the number of adapters.

## What Happened

1. `BaseAdapter` was defined as an ABC with two abstract methods: `fetch()` (returns raw API payloads) and `normalize()` (converts one raw payload to a `RawSignal` dataclass).
2. The base class implements `safe_request()` — a wrapper around httpx that handles rate throttling (token-bucket based on `rate_limit_rpm`), request timeouts, credential redaction in log messages, and error classification (429 → backoff, 5xx → skip, 4xx → raise).
3. `RawSignal` is a dataclass with optional fields for every piece of data the pipeline might need: `external_id`, `canonical_url`, `title`, `published_date`, `signal_text`, `raw_payload`, `matched_keywords`. Adapters populate what they can and leave the rest as `None`.
4. The smallest adapter (Semantic Scholar) is 65 lines. The largest (Reddit, with OAuth) is 138 lines. Without the base class, each would need an additional ~90 lines of boilerplate for throttling, timeouts, and error handling.
5. The `ImportRunner` orchestrator treats all adapters identically — it calls `adapter.fetch()`, iterates results, calls `adapter.normalize()`, and feeds `RawSignal` objects into scoring and dedup. It never inspects which adapter it's talking to.
6. Credential redaction in `safe_request()` uses regex patterns to strip tokens, API keys, and GitHub PATs from any string before it reaches the log. This prevents accidental credential leakage even if an adapter passes credentials in URL parameters.

## Key Insights

- **Two methods is the right contract size.** `fetch()` handles API-specific query construction and pagination. `normalize()` handles response parsing. Everything else is shared. Three or more abstract methods would split the domain logic unnaturally; one method would force fetch+normalize into a single function.
- **Rate limiting belongs in the base, not the subclass.** Every adapter needs rate limiting, and every adapter gets it wrong in a slightly different way if left to implement it. A single `_throttle()` method with a configurable `rate_limit_rpm` class variable is correct for all 10 adapters.
- **Credential redaction is too important to delegate.** If each adapter is responsible for redacting its own credentials from logs, one will forget. Centralizing it in `safe_request()` means every HTTP request through the pipeline is automatically redacted.
- **Optional fields on the intermediate representation are better than required fields.** Not every API provides a `canonical_url` or `published_date`. Making these optional on `RawSignal` means adapters don't need to fabricate data, and downstream code (scoring, dedup) can handle `None` gracefully.
- **Error classification at the base level standardizes retry behavior.** The base class distinguishes between retryable errors (429, 5xx, timeouts → return `None`, skip this request) and permanent errors (4xx → raise, stop the run). Adapters never need to think about this.

## Examples

**Adding a new adapter (minimal):**
```python
class NewSourceAdapter(BaseAdapter):
    source_id = "new_source"
    display_name = "New Source"
    rate_limit_rpm = 30

    async def fetch(self, client, query, *, result_limit=25, lookback_days=30, **kw):
        resp = await self.safe_request(client, "GET", f"https://api.example.com/search?q={query}")
        return resp.json()["results"] if resp else []

    def normalize(self, raw_payload, **kw):
        return RawSignal(
            external_id=raw_payload["id"],
            title=raw_payload["title"],
            signal_text=raw_payload["abstract"],
            published_date=raw_payload.get("date"),
        )
```

Register in `__init__.py`:
```python
register_adapter("new_source", NewSourceAdapter)
```

## Applicability

This pattern applies to any system that integrates with multiple external APIs sharing a common downstream pipeline. It works best when the APIs differ in surface details (auth, response format, pagination) but share a common semantic contract (fetch records → normalize → process).

It is NOT suitable when adapters have fundamentally different interaction models (e.g., mixing REST APIs with WebSocket streams or message queues). In that case, the ABC would either be too generic to be useful or would force unnatural implementations.

## Related Lessons

- [Phased Adapter Expansion](phased-adapter-expansion.md) — the ABC enabled safe 4-phase expansion
- [Live API vs Mock Divergence](live-api-vs-mock-divergence.md) — bugs in normalize() that the ABC contract alone can't prevent

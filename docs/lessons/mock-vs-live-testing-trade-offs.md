---
title: Mock vs Live Testing Trade-offs
summary: A decision framework for when to mock dependencies and when to test against real infrastructure
date: 2026-05-10
phase: execution
lesson_type: process
status: active
tags: [testing, mocks, integration, decision-framework, cloud, adapters]
---

# Mock vs Live Testing Trade-offs

## The Lesson

Mocks prove your code calls the right functions in the right order; live tests prove your system actually works. Neither is universally better — the decision depends on what failure class you're trying to catch, how stable the dependency is, and whether the dependency is available in your test environment.

## Context

Lessons Hub V2 has a backend with multiple adapter layers: LLM adapters (Ollama, AWS Bedrock, Azure OpenAI, GCP Vertex), vector adapters (ChromaDB, OpenSearch, Azure AI Search, GCP Vector Search), and service integrations (GitHub API for discovery, file system for gap storage). Each adapter has a different availability profile in CI vs local dev vs production. The testing strategy needed a principled way to decide: mock it or run it live?

## What Happened

1. The backend started with 100% mocked tests — every adapter interaction used `unittest.mock.patch` or injected fake implementations. This gave fast, deterministic tests that ran anywhere.
2. When the Ollama adapter was tested live for the first time, it revealed that the prompt template produced responses the citation extractor couldn't parse. The mock had been returning hand-crafted "ideal" responses that never existed in practice.
3. A team elsewhere lost a quarter to a similar issue: mocked database tests passed, but the actual migration failed in production. The mock perfectly simulated the old schema while the real database had moved on.
4. Cloud SDK adapters (Bedrock, Azure OpenAI, Vertex AI) presented the opposite problem — live testing required cloud credentials, network access, and billable API calls. Mocking was the only practical option for CI.
5. A hybrid pattern emerged using `sys.modules.setdefault()`: cloud SDKs are stubbed at the module level so adapter initialization code runs without the actual SDK, while local services (Ollama, ChromaDB) are tested live when available and skipped otherwise.

## Key Insights

- **Mocks mask integration bugs by definition.** A mock returns what you tell it to return, not what the real system returns. If your understanding of the real system's behavior is wrong, the mock encodes that wrong understanding as a passing test.

- **Live tests are only better when the live system is stable and representative.** Testing against a production database is live testing, but it's also dangerous and non-deterministic. The sweet spot is local infrastructure that matches production behavior (Ollama running the same model, ChromaDB with the same embedding dimensions).

- **The decision framework has three axes:**

  | Factor | Mock | Live |
  |--------|------|------|
  | Dependency available in CI? | Yes (always) | Only if self-hosted |
  | Dependency behavior well-understood? | Assumes yes | Validates understanding |
  | Dependency costs money per call? | Free | Billable |
  | Failure mode is data-format mismatch? | Won't catch it | Will catch it |
  | Failure mode is logic error? | Will catch it | Will catch it (slower) |

- **`sys.modules.setdefault()` enables testing adapter initialization without SDKs.**
  ```python
  # In test setup — stub the SDK module before the adapter imports it
  import sys
  fake_boto3 = type(sys)('boto3')
  fake_boto3.client = lambda *a, **kw: MockClient()
  sys.modules.setdefault('boto3', fake_boto3)
  ```
  This is better than `@patch('boto3.client')` because it lets the adapter's import-time code run normally — catching import errors, attribute access patterns, and initialization logic that `@patch` would skip.

- **Use skip markers, not conditional mocks, for unavailable services.**
  ```python
  import pytest
  
  def ollama_available():
      try:
          import httpx
          r = httpx.get("http://localhost:11434/api/tags", timeout=2)
          return r.status_code == 200
      except:
          return False
  
  requires_ollama = pytest.mark.skipif(
      not ollama_available(), reason="Ollama not running"
  )
  ```
  This keeps the test suite green in CI (where Ollama isn't available) without hiding the tests behind mocks that weaken them.

## Examples

### When to Mock

- **Cloud SDKs in CI:** `boto3`, `azure-ai-inference`, `google-cloud-aiplatform` — billable, require credentials, slow. Mock the client, test the adapter logic.
- **External APIs with rate limits:** GitHub API for discovery scoring. Mock the response JSON, test the scoring algorithm.
- **Deterministic assertion needs:** When you need to assert that a specific prompt was sent to the LLM with specific parameters, a mock captures the call; a live test only shows the output.

### When to Go Live

- **Local services already running:** Ollama, ChromaDB, PostgreSQL, Redis. If it's running, test against it — the feedback is richer and the cost is zero.
- **Data format validation:** Does the embeddings API return 768-dimensional vectors or 1024? Does the chat API return a string or a message object? Live calls answer definitively.
- **End-to-end pipeline verification:** The full RAG pipeline (embed → retrieve → generate → cite) has emergent behavior that no combination of mocked units can replicate.

### The Hybrid Pattern

```python
class TestBedrockAdapter:
    """Tests run without boto3 installed — adapter init still works."""
    
    @pytest.fixture(autouse=True)
    def stub_boto3(self):
        fake = type(sys)('boto3')
        fake.client = lambda service, **kw: self.mock_client
        sys.modules.setdefault('boto3', fake)
        yield
        # Don't remove — other tests may have imported it
    
    def test_adapter_initializes(self):
        from backend.adapters.aws import BedrockAdapter
        adapter = BedrockAdapter(model_id="anthropic.claude-3-sonnet")
        assert adapter.model_id == "anthropic.claude-3-sonnet"
    
    def test_generate_calls_invoke_model(self):
        # Mock at the method level, not the module level
        self.mock_client.invoke_model.return_value = {...}
        ...
```

## Applicability

This framework applies whenever you have:
- Dependencies with different availability profiles (local vs cloud vs third-party)
- Adapters or abstraction layers over external services
- A CI environment that can't (or shouldn't) reach all production dependencies

It does NOT apply to:
- Pure logic functions with no external dependencies (just unit test them)
- UI testing (use acceptance tests instead — mocking a browser makes no sense)
- Performance testing (mocks don't have meaningful latency characteristics)

## Related Lessons

- [Live Infrastructure for Integration Testing](live-infrastructure-for-integration-testing.md) — the "go live" approach in detail
- [Adapter Pattern for Multi-Cloud](adapter-pattern-for-multi-cloud.md) — the architecture that makes this mock/live split clean
- [Test Pyramid for Static Sites](test-pyramid-for-static-sites.md) — where mock vs live fits in the overall strategy

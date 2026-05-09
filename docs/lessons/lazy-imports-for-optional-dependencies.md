---
title: Lazy Imports for Optional Cloud Dependencies
summary: Deferring cloud SDK imports to runtime lets the same codebase run with or without any given SDK installed, and enables testing without real dependencies.
date: 2026-05-09
phase: implementation
lesson_type: architecture
status: active
tags: [python, imports, cloud, testing, dependency-management]
---

# Lazy Imports for Optional Cloud Dependencies

## The Lesson

When a Python application supports multiple cloud providers as optional backends, move cloud SDK imports inside the class constructor rather than placing them at module level. This lets the application load without any cloud SDK installed, and lets tests mock the SDK by injecting into `sys.modules` before the class is instantiated.

## Context

A RAG chatbot backend needed to support four LLM providers (Ollama, AWS Bedrock, Azure OpenAI, GCP Vertex AI) and four vector stores (ChromaDB, OpenSearch, Azure AI Search, Vertex Vector Search). Only one pair is active at runtime, determined by deployment target. The local development stack (Ollama + ChromaDB) requires zero cloud credentials. CI tests must validate all adapter code without installing any cloud SDK — the SDKs are large, have native dependencies, and some require platform-specific binaries.

## What Happened

1. Initial adapter implementations used standard top-of-file imports (`import boto3`, `from openai import AzureOpenAI`). This meant importing the adapter module at all required the SDK to be installed.
2. The dependency injection layer (`_deps.py`) imports all adapter modules to dispatch based on a deployment profile. With module-level imports, starting the backend with `DEPLOYMENT_PROFILE=local` would fail if `boto3` wasn't installed — even though Bedrock was never used.
3. Moved all cloud SDK imports inside each adapter's `__init__` method. The module can now be imported freely; the `ImportError` only fires if someone actually instantiates the cloud adapter without the SDK.
4. Tests initially used `@patch("app.adapters.llm.bedrock_adapter.boto3")` to mock the SDK. This broke because with lazy imports, `boto3` is not a module-level attribute — `patch` couldn't find it.
5. Switched tests to `sys.modules.setdefault("boto3", mock_boto3)` before importing the adapter class. When the adapter's `__init__` runs `import boto3`, Python finds the mock in `sys.modules` and returns it. No SDK installation needed.
6. Azure adapters required mocking every level of the namespace hierarchy separately (`azure`, `azure.core`, `azure.core.credentials`, `azure.search`, `azure.search.documents`, etc.) — 9 entries for two Azure adapters.

## Key Insights

- **Lazy imports turn hard dependencies into soft ones.** A module-level `import boto3` makes boto3 a hard dependency of the entire application. Moving it into `__init__` makes it a dependency of only the code path that actually uses Bedrock. The rest of the application is unaffected.

- **`sys.modules.setdefault()` is the correct mock pattern for lazy imports.** `unittest.mock.patch` targets module-level attributes. When the import happens inside a function, there's no attribute to patch. Pre-populating `sys.modules` intercepts Python's import machinery at the right layer.

- **Nested package namespaces must be mocked at every level.** `from azure.search.documents import SearchClient` triggers imports of `azure`, `azure.search`, and `azure.search.documents` in sequence. Missing any level causes `ModuleNotFoundError`. The AWS SDK (`boto3`) is a flat namespace and needs only one mock entry; the Azure SDK needed nine.

- **Order matters: mock before import.** The `sys.modules.setdefault()` calls must execute before the adapter class is imported. In test files, this means the mock setup is at module scope (before the `from app.adapters... import` line), with `# noqa: E402` on the deferred import.

- **No error handling needed in the adapter.** If someone configures `DEPLOYMENT_PROFILE=aws` without installing boto3, the `ImportError` from `__init__` is exactly the right error — clear, immediate, and actionable. Wrapping it in a try/except would obscure the problem.

## Examples

**Module-level import (breaks without SDK):**
```python
import boto3  # Fails here if boto3 not installed

class BedrockAdapter(LLMAdapter):
    def __init__(self):
        self._client = boto3.client("bedrock-runtime")
```

**Lazy import (only fails when instantiated):**
```python
class BedrockAdapter(LLMAdapter):
    def __init__(self):
        import boto3  # Only fails if this class is actually used
        self._client = boto3.client("bedrock-runtime")
```

**Test mocking pattern:**
```python
import sys
from unittest.mock import MagicMock

mock_boto3 = MagicMock()
sys.modules.setdefault("boto3", mock_boto3)

from app.adapters.llm.bedrock_adapter import BedrockAdapter  # noqa: E402
```

## Applicability

This pattern works well when:
- An application supports multiple backends where only one is active at runtime
- Dependencies are large or platform-specific (cloud SDKs, ML frameworks, database drivers)
- CI environments shouldn't need every possible dependency installed

It does **not** apply when:
- The dependency is always required (just import it normally)
- The import is needed for type checking — use `TYPE_CHECKING` blocks instead
- The dependency is small and has no side effects at import time

## Related Lessons

- [Adapter Pattern for Multi-Cloud Portability](adapter-pattern-for-multi-cloud.md) — the architectural pattern that makes lazy imports necessary

"""Azure OpenAI LLM adapter for embedding + chat."""

from __future__ import annotations

import os

from .base import LLMAdapter

DEFAULT_EMBED_DEPLOYMENT = "text-embedding-3-small"
DEFAULT_CHAT_DEPLOYMENT = "gpt-4o-mini"
DEFAULT_API_VERSION = "2024-06-01"


class AzureOpenAIAdapter(LLMAdapter):
    """Azure OpenAI-backed LLM for embeddings and chat."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        embed_deployment: str | None = None,
        chat_deployment: str | None = None,
        api_version: str | None = None,
    ):
        self._endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self._api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY", "")
        self._embed_deployment = embed_deployment or os.getenv(
            "AZURE_OPENAI_EMBED_DEPLOYMENT", DEFAULT_EMBED_DEPLOYMENT
        )
        self._chat_deployment = chat_deployment or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", DEFAULT_CHAT_DEPLOYMENT)
        self._api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION)

        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            azure_endpoint=self._endpoint,
            api_key=self._api_key,
            api_version=self._api_version,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via Azure OpenAI."""
        response = self._client.embeddings.create(
            model=self._embed_deployment,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def chat(self, messages: list[dict]) -> str:
        """Send chat via Azure OpenAI and return the assistant response."""
        response = self._client.chat.completions.create(
            model=self._chat_deployment,
            messages=messages,
            max_tokens=2048,
        )
        return response.choices[0].message.content

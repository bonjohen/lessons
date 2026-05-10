"""OpenAI LLM adapter for embedding + chat (direct API, not Azure-wrapped)."""

from __future__ import annotations

import os

from .base import LLMAdapter

DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_CHAT_MODEL = "gpt-4o-mini"


class OpenAIAdapter(LLMAdapter):
    """OpenAI-backed LLM for embeddings and chat."""

    def __init__(
        self,
        api_key: str | None = None,
        embed_model: str | None = None,
        chat_model: str | None = None,
    ):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._embed_model = embed_model or os.getenv("OPENAI_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self._chat_model = chat_model or os.getenv("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL)

        from openai import OpenAI

        self._client = OpenAI(api_key=self._api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via OpenAI."""
        response = self._client.embeddings.create(
            model=self._embed_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def chat(self, messages: list[dict]) -> str:
        """Send chat via OpenAI and return the assistant response."""
        response = self._client.chat.completions.create(
            model=self._chat_model,
            messages=messages,
            max_tokens=2048,
        )
        return response.choices[0].message.content

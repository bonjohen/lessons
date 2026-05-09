"""Ollama LLM adapter for local development."""

import ollama

from .base import LLMAdapter

DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_CHAT_MODEL = "llama3.1:8b"


class OllamaAdapter(LLMAdapter):
    """Ollama-backed LLM for embeddings and chat."""

    def __init__(
        self,
        embed_model: str = DEFAULT_EMBED_MODEL,
        chat_model: str = DEFAULT_CHAT_MODEL,
        host: str | None = None,
    ):
        self._embed_model = embed_model
        self._chat_model = chat_model
        self._client = ollama.Client(host=host) if host else ollama.Client()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via Ollama."""
        embeddings = []
        for text in texts:
            response = self._client.embed(model=self._embed_model, input=text)
            embeddings.append(response["embeddings"][0])
        return embeddings

    def chat(self, messages: list[dict]) -> str:
        """Send chat via Ollama and return the assistant response."""
        response = self._client.chat(
            model=self._chat_model,
            messages=messages,
        )
        return response["message"]["content"]

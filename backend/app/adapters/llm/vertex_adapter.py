"""Google Vertex AI LLM adapter for embedding + chat."""

from __future__ import annotations

import os

from .base import LLMAdapter

DEFAULT_EMBED_MODEL = "text-embedding-004"
DEFAULT_CHAT_MODEL = "gemini-1.5-flash-001"


class VertexAIAdapter(LLMAdapter):
    """Vertex AI-backed LLM for embeddings and chat."""

    def __init__(
        self,
        project: str | None = None,
        location: str | None = None,
        embed_model: str | None = None,
        chat_model: str | None = None,
    ):
        self._project = project or os.getenv("GCP_PROJECT_ID", "")
        self._location = location or os.getenv("GCP_LOCATION", "us-central1")
        self._embed_model_name = embed_model or os.getenv("VERTEX_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self._chat_model_name = chat_model or os.getenv("VERTEX_CHAT_MODEL", DEFAULT_CHAT_MODEL)

        import vertexai
        from vertexai.generative_models import GenerativeModel
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(project=self._project, location=self._location)

        self._embed_model = TextEmbeddingModel.from_pretrained(self._embed_model_name)
        self._chat_model = GenerativeModel(self._chat_model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via Vertex AI."""
        embeddings = self._embed_model.get_embeddings(texts)
        return [e.values for e in embeddings]

    def chat(self, messages: list[dict]) -> str:
        """Send chat via Vertex AI Gemini and return the response."""
        # Build prompt from messages
        system_text = ""
        user_parts = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                user_parts.append(msg["content"])

        prompt = ""
        if system_text:
            prompt = f"System: {system_text}\n\n"
        prompt += "\n".join(user_parts)

        response = self._chat_model.generate_content(prompt)
        return response.text

"""Abstract LLM adapter."""

from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """Interface for LLM backends (embedding + chat)."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """Send chat messages and return the assistant response."""
        ...

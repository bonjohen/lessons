"""Abstract vector store adapter."""

from abc import ABC, abstractmethod


class VectorAdapter(ABC):
    """Interface for vector store backends."""

    @abstractmethod
    def index_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Index chunks with their embeddings. Returns count indexed."""
        ...

    @abstractmethod
    def query(self, embedding: list[float], top_k: int = 8, filters: dict | None = None) -> list[dict]:
        """Query for similar chunks. Returns list of {chunk_id, chunk, score}."""
        ...

    @abstractmethod
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return number of indexed chunks."""
        ...

"""Vertex AI Vector Search adapter for GCP deployment."""

from __future__ import annotations

import os

from .base import VectorAdapter

INDEX_NAME = "lessons_chunks"


class VertexVectorSearchAdapter(VectorAdapter):
    """Vertex AI Vector Search-backed vector store.

    Uses a local JSON file as a staging area and batch-imports to
    Vertex AI Vector Search index. For query, uses the deployed index endpoint.
    """

    def __init__(
        self,
        project: str | None = None,
        location: str | None = None,
        index_id: str | None = None,
        index_endpoint_id: str | None = None,
        deployed_index_id: str | None = None,
    ):
        self._project = project or os.getenv("GCP_PROJECT_ID", "")
        self._location = location or os.getenv("GCP_LOCATION", "us-central1")
        self._index_id = index_id or os.getenv("VERTEX_INDEX_ID", "")
        self._index_endpoint_id = index_endpoint_id or os.getenv("VERTEX_INDEX_ENDPOINT_ID", "")
        self._deployed_index_id = deployed_index_id or os.getenv("VERTEX_DEPLOYED_INDEX_ID", INDEX_NAME)

        from google.cloud import aiplatform

        aiplatform.init(project=self._project, location=self._location)
        self._aiplatform = aiplatform

        self._chunks_store: dict[str, dict] = {}

    def index_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Index chunks — stores metadata locally and upserts vectors to Vertex."""
        if not chunks:
            return 0

        datapoints = []
        for chunk, embedding in zip(chunks, embeddings):
            self._chunks_store[chunk["chunk_id"]] = chunk
            datapoints.append(
                self._aiplatform.MatchingEngineIndexEndpoint.MatchNeighbor(
                    id=chunk["chunk_id"],
                    feature_vector=embedding,
                )
            )

        if self._index_id:
            index = self._aiplatform.MatchingEngineIndex(self._index_id)
            index.upsert_datapoints(
                datapoints=[
                    {"datapoint_id": chunk["chunk_id"], "feature_vector": emb} for chunk, emb in zip(chunks, embeddings)
                ]
            )

        return len(chunks)

    def query(
        self,
        embedding: list[float],
        top_k: int = 8,
        filters: dict | None = None,
    ) -> list[dict]:
        """Query Vertex AI Vector Search for similar chunks."""
        if not self._index_endpoint_id:
            return []

        endpoint = self._aiplatform.MatchingEngineIndexEndpoint(self._index_endpoint_id)
        response = endpoint.find_neighbors(
            deployed_index_id=self._deployed_index_id,
            queries=[embedding],
            num_neighbors=top_k,
        )

        items = []
        if response and response[0]:
            for neighbor in response[0]:
                chunk_id = neighbor.id
                chunk_data = self._chunks_store.get(chunk_id, {})
                items.append(
                    {
                        "chunk_id": chunk_id,
                        "chunk_text": chunk_data.get("chunk_text", ""),
                        "similarity_score": round(neighbor.distance, 4),
                        "lesson_id": chunk_data.get("lesson_id", ""),
                        "title": chunk_data.get("title", ""),
                        "heading_path": chunk_data.get("heading_path", ""),
                        "tags": chunk_data.get("tags", []),
                        "lesson_url": chunk_data.get("lesson_url", ""),
                        "repo_id": chunk_data.get("repo_id", ""),
                    }
                )

        return items

    def delete_collection(self) -> None:
        """Clear the local chunk store."""
        self._chunks_store.clear()

    def count(self) -> int:
        """Return number of locally stored chunks."""
        return len(self._chunks_store)

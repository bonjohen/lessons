"""Azure AI Search vector store adapter."""

from __future__ import annotations

import os

from .base import VectorAdapter

INDEX_NAME = "lessons-chunks"
EMBEDDING_DIM = 768


class AzureSearchAdapter(VectorAdapter):
    """Azure AI Search-backed vector store."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        index_name: str | None = None,
    ):
        self._index_name = index_name or os.getenv("AZURE_SEARCH_INDEX", INDEX_NAME)
        self._endpoint = endpoint or os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self._api_key = api_key or os.getenv("AZURE_SEARCH_API_KEY", "")

        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            HnswAlgorithmConfiguration,
            SearchField,
            SearchFieldDataType,
            SearchIndex,
            VectorSearch,
            VectorSearchProfile,
        )

        credential = AzureKeyCredential(self._api_key)

        # Create index if needed
        index_client = SearchIndexClient(endpoint=self._endpoint, credential=credential)
        self._ensure_index(
            index_client,
            SearchIndex,
            SearchField,
            SearchFieldDataType,
            VectorSearch,
            VectorSearchProfile,
            HnswAlgorithmConfiguration,
        )

        self._client = SearchClient(
            endpoint=self._endpoint,
            index_name=self._index_name,
            credential=credential,
        )
        self._index_client = index_client

    def _ensure_index(
        self,
        index_client,
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        VectorSearch,
        VectorSearchProfile,
        HnswAlgorithmConfiguration,
    ):
        """Create the search index if it doesn't exist."""
        try:
            index_client.get_index(self._index_name)
        except Exception:
            fields = [
                SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True),
                SearchField(name="chunk_text", type=SearchFieldDataType.String, searchable=True),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=EMBEDDING_DIM,
                    vector_search_profile_name="default",
                ),
                SearchField(name="lesson_id", type=SearchFieldDataType.String, filterable=True),
                SearchField(name="repo_id", type=SearchFieldDataType.String, filterable=True),
                SearchField(name="title", type=SearchFieldDataType.String, searchable=True),
                SearchField(name="summary", type=SearchFieldDataType.String, searchable=True),
                SearchField(name="heading_path", type=SearchFieldDataType.String),
                SearchField(name="lesson_url", type=SearchFieldDataType.String),
                SearchField(
                    name="tags",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    filterable=True,
                ),
                SearchField(name="chunk_index", type=SearchFieldDataType.Int32),
            ]

            vector_search = VectorSearch(
                profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw")],
                algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            )

            index = SearchIndex(
                name=self._index_name,
                fields=fields,
                vector_search=vector_search,
            )
            index_client.create_index(index)

    def index_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Index chunks with embeddings into Azure AI Search."""
        if not chunks:
            return 0

        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            documents.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "chunk_text": chunk["chunk_text"],
                    "embedding": embedding,
                    "lesson_id": chunk["lesson_id"],
                    "repo_id": chunk["repo_id"],
                    "title": chunk["title"],
                    "summary": chunk.get("summary", ""),
                    "heading_path": chunk["heading_path"],
                    "lesson_url": chunk["lesson_url"],
                    "tags": chunk.get("tags", []),
                    "chunk_index": chunk["chunk_index"],
                }
            )

        # Upload in batches of 1000
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            self._client.upload_documents(documents=batch)

        return len(documents)

    def query(
        self,
        embedding: list[float],
        top_k: int = 8,
        filters: dict | None = None,
    ) -> list[dict]:
        """Query Azure AI Search for similar chunks."""
        from azure.search.documents.models import VectorizedQuery

        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )

        filter_str = None
        if filters:
            parts = []
            if filters.get("repo"):
                parts.append(f"repo_id eq '{filters['repo']}'")
            if filters.get("lesson_type"):
                parts.append(f"lesson_type eq '{filters['lesson_type']}'")
            if parts:
                filter_str = " and ".join(parts)

        results = self._client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filter_str,
            top=top_k,
        )

        items = []
        for result in results:
            items.append(
                {
                    "chunk_id": result["chunk_id"],
                    "chunk_text": result["chunk_text"],
                    "similarity_score": round(result.get("@search.score", 0.0), 4),
                    "lesson_id": result.get("lesson_id", ""),
                    "title": result.get("title", ""),
                    "heading_path": result.get("heading_path", ""),
                    "tags": result.get("tags", []),
                    "lesson_url": result.get("lesson_url", ""),
                    "repo_id": result.get("repo_id", ""),
                }
            )

        return items

    def delete_collection(self) -> None:
        """Delete and recreate the Azure AI Search index."""
        try:
            self._index_client.delete_index(self._index_name)
        except Exception:
            pass

    def count(self) -> int:
        """Return number of indexed documents."""
        return self._client.get_document_count()

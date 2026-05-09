"""OpenSearch Serverless vector store adapter for AWS deployment."""

from __future__ import annotations

import os

from .base import VectorAdapter

INDEX_NAME = "lessons-chunks"
EMBEDDING_DIM = 768


class OpenSearchAdapter(VectorAdapter):
    """OpenSearch Serverless-backed vector store."""

    def __init__(
        self,
        endpoint: str | None = None,
        region: str | None = None,
        index_name: str | None = None,
    ):
        self._index_name = index_name or os.getenv("OPENSEARCH_INDEX", INDEX_NAME)
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._endpoint = endpoint or os.getenv("OPENSEARCH_ENDPOINT", "")

        import boto3
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth

        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self._region,
            "aoss",
            session_token=credentials.token,
        )

        self._client = OpenSearch(
            hosts=[{"host": self._endpoint, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

        self._ensure_index()

    def _ensure_index(self) -> None:
        """Create the index if it doesn't exist."""
        if not self._client.indices.exists(self._index_name):
            body = {
                "settings": {
                    "index.knn": True,
                },
                "mappings": {
                    "properties": {
                        "chunk_id": {"type": "keyword"},
                        "chunk_text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": EMBEDDING_DIM,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                            },
                        },
                        "lesson_id": {"type": "keyword"},
                        "repo_id": {"type": "keyword"},
                        "title": {"type": "text"},
                        "summary": {"type": "text"},
                        "heading_path": {"type": "keyword"},
                        "lesson_url": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "chunk_index": {"type": "integer"},
                    }
                },
            }
            self._client.indices.create(self._index_name, body=body)

    def index_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Index chunks with embeddings into OpenSearch."""
        if not chunks:
            return 0

        for chunk, embedding in zip(chunks, embeddings):
            doc = {
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
            self._client.index(
                index=self._index_name,
                id=chunk["chunk_id"],
                body=doc,
            )

        self._client.indices.refresh(self._index_name)
        return len(chunks)

    def query(
        self,
        embedding: list[float],
        top_k: int = 8,
        filters: dict | None = None,
    ) -> list[dict]:
        """Query OpenSearch for similar chunks."""
        knn_query: dict = {
            "knn": {
                "embedding": {
                    "vector": embedding,
                    "k": top_k,
                }
            }
        }

        if filters:
            filter_clauses = []
            if filters.get("repo"):
                filter_clauses.append({"term": {"repo_id": filters["repo"]}})
            if filters.get("lesson_type"):
                filter_clauses.append({"term": {"lesson_type": filters["lesson_type"]}})
            if filter_clauses:
                knn_query["knn"]["embedding"]["filter"] = {"bool": {"must": filter_clauses}}

        body = {"size": top_k, "query": knn_query}
        response = self._client.search(index=self._index_name, body=body)

        items = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            items.append(
                {
                    "chunk_id": source["chunk_id"],
                    "chunk_text": source["chunk_text"],
                    "similarity_score": round(hit["_score"], 4),
                    "lesson_id": source.get("lesson_id", ""),
                    "title": source.get("title", ""),
                    "heading_path": source.get("heading_path", ""),
                    "tags": source.get("tags", []),
                    "lesson_url": source.get("lesson_url", ""),
                    "repo_id": source.get("repo_id", ""),
                }
            )

        return items

    def delete_collection(self) -> None:
        """Delete and recreate the OpenSearch index."""
        if self._client.indices.exists(self._index_name):
            self._client.indices.delete(self._index_name)
        self._ensure_index()

    def count(self) -> int:
        """Return number of indexed documents."""
        if not self._client.indices.exists(self._index_name):
            return 0
        result = self._client.count(index=self._index_name)
        return result["count"]

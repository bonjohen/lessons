"""ChromaDB vector store adapter for local development."""

from pathlib import Path

import chromadb

from .base import VectorAdapter

DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "chromadb"
COLLECTION_NAME = "lessons_chunks"


class ChromaDBAdapter(VectorAdapter):
    """ChromaDB-backed vector store."""

    def __init__(self, persist_dir: Path | str | None = None):
        self._persist_dir = Path(persist_dir) if persist_dir else DEFAULT_PERSIST_DIR
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def index_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Index chunks with embeddings into ChromaDB."""
        if not chunks:
            return 0

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["chunk_text"] for c in chunks]
        metadatas = [
            {
                "lesson_id": c["lesson_id"],
                "repo_id": c["repo_id"],
                "title": c["title"],
                "summary": c.get("summary", ""),
                "heading_path": c["heading_path"],
                "lesson_url": c["lesson_url"],
                "tags": ",".join(c.get("tags", [])),
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ]

        # Upsert in batches of 500 (ChromaDB limit)
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self._collection.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end],
            )

        return len(ids)

    def query(self, embedding: list[float], top_k: int = 8, filters: dict | None = None) -> list[dict]:
        """Query ChromaDB for similar chunks."""
        where = None
        if filters:
            conditions = []
            if filters.get("repo"):
                conditions.append({"repo_id": {"$eq": filters["repo"]}})
            if filters.get("lesson_type"):
                conditions.append({"lesson_type": {"$eq": filters["lesson_type"]}})
            if len(conditions) == 1:
                where = conditions[0]
            elif len(conditions) > 1:
                where = {"$and": conditions}

        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self._collection.count() or 1),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns cosine distance; convert to similarity
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1.0 - distance

                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                document = results["documents"][0][i] if results["documents"] else ""

                items.append({
                    "chunk_id": chunk_id,
                    "chunk_text": document,
                    "similarity_score": round(similarity, 4),
                    "lesson_id": metadata.get("lesson_id", ""),
                    "title": metadata.get("title", ""),
                    "heading_path": metadata.get("heading_path", ""),
                    "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                    "lesson_url": metadata.get("lesson_url", ""),
                    "repo_id": metadata.get("repo_id", ""),
                })

        return items

    def delete_collection(self) -> None:
        """Delete the ChromaDB collection."""
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Return number of indexed chunks."""
        return self._collection.count()

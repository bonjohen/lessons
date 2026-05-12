"""Embed RAG corpus — generate embeddings and index into vector store.

Reads data/rag-chunks.json, embeds each chunk via the LLM adapter,
and indexes into ChromaDB. Supports incremental re-indexing: only
embeds chunks that are new or changed since the last run.
"""

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = PROJECT_ROOT / "data" / "rag-chunks.json"
HASH_CACHE_PATH = PROJECT_ROOT / "data" / "embed-hashes.json"

# Add backend to path for adapter imports
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.adapters.llm.ollama_adapter import OllamaAdapter  # noqa: E402
from app.adapters.vector.chromadb_adapter import ChromaDBAdapter  # noqa: E402


def _content_hash(chunk: dict) -> str:
    """Compute a hash of the chunk content for change detection."""
    return hashlib.md5(chunk["chunk_text"].encode("utf-8")).hexdigest()


def _load_hash_cache() -> dict[str, str]:
    """Load previously saved chunk_id → content_hash map."""
    if HASH_CACHE_PATH.exists():
        with open(HASH_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_hash_cache(hashes: dict[str, str]) -> None:
    """Save chunk_id → content_hash map."""
    HASH_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HASH_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)


def main():
    if not CHUNKS_PATH.exists():
        print(
            f"ERROR: {CHUNKS_PATH} not found. Run 'npm run corpus' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    llm = OllamaAdapter()
    vector = ChromaDBAdapter()

    # Build current hash map
    current_hashes = {c["chunk_id"]: _content_hash(c) for c in chunks}
    current_ids = set(current_hashes.keys())

    # Load previous hash map
    previous_hashes = _load_hash_cache()
    existing_ids = vector.get_all_ids()

    # Determine what changed
    new_ids = current_ids - existing_ids
    deleted_ids = existing_ids - current_ids
    possibly_changed = current_ids & existing_ids
    updated_ids = {
        cid
        for cid in possibly_changed
        if current_hashes.get(cid) != previous_hashes.get(cid)
    }
    unchanged_ids = possibly_changed - updated_ids

    to_embed = [c for c in chunks if c["chunk_id"] in (new_ids | updated_ids)]

    print(
        f"Incremental embed: {len(new_ids)} new, {len(updated_ids)} updated, "
        f"{len(unchanged_ids)} unchanged, {len(deleted_ids)} to delete"
    )

    # Delete removed chunks
    if deleted_ids:
        vector.delete_chunks(list(deleted_ids))
        print(f"  Deleted {len(deleted_ids)} stale chunks")

    # Embed and index new/changed chunks
    if to_embed:
        batch_size = 50
        total_indexed = 0
        for i in range(0, len(to_embed), batch_size):
            batch = to_embed[i : i + batch_size]
            texts = [c["chunk_text"] for c in batch]
            print(
                f"  Embedding batch {i // batch_size + 1}/{(len(to_embed) - 1) // batch_size + 1}..."
            )
            embeddings = llm.embed(texts)
            indexed = vector.index_chunks(batch, embeddings)
            total_indexed += indexed
        print(f"  Embedded {total_indexed} chunks")
    else:
        print("  No chunks to embed")

    # Save updated hash cache
    _save_hash_cache(current_hashes)

    print("\nEmbedding complete:")
    print(f"  Vector store count: {vector.count()}")


if __name__ == "__main__":
    main()

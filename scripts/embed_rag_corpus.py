"""Embed RAG corpus — generate embeddings and index into vector store.

Reads data/rag-chunks.json, embeds each chunk via the LLM adapter,
and indexes into ChromaDB.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = PROJECT_ROOT / "data" / "rag-chunks.json"

# Add backend to path for adapter imports
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.adapters.llm.ollama_adapter import OllamaAdapter  # noqa: E402
from app.adapters.vector.chromadb_adapter import ChromaDBAdapter  # noqa: E402


def main():
    if not CHUNKS_PATH.exists():
        print(f"ERROR: {CHUNKS_PATH} not found. Run 'npm run corpus' first.", file=sys.stderr)
        sys.exit(1)

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Embedding {len(chunks)} chunks...")

    llm = OllamaAdapter()
    vector = ChromaDBAdapter()

    # Delete existing collection for clean re-index
    vector.delete_collection()

    # Embed and index in batches
    batch_size = 50
    total_indexed = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["chunk_text"] for c in batch]

        print(f"  Embedding batch {i // batch_size + 1}/{(len(chunks) - 1) // batch_size + 1}...")
        embeddings = llm.embed(texts)

        indexed = vector.index_chunks(batch, embeddings)
        total_indexed += indexed

    print(f"\nEmbedding complete:")
    print(f"  Chunks embedded: {total_indexed}")
    print(f"  Vector store count: {vector.count()}")


if __name__ == "__main__":
    main()

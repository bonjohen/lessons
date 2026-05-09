"""Validate RAG corpus — check chunk schema, unique IDs, and lesson references.

Reads data/rag-chunks.json and src/content/generated/lessons.json,
validates structural integrity of the corpus.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = PROJECT_ROOT / "data" / "rag-chunks.json"
LESSONS_PATH = PROJECT_ROOT / "src" / "content" / "generated" / "lessons.json"

REQUIRED_CHUNK_FIELDS = {
    "chunk_id", "lesson_id", "repo_id", "title", "chunk_index",
    "heading_path", "chunk_text", "token_count", "content_hash",
}

errors = 0
warnings = 0


def error(msg: str):
    global errors
    errors += 1
    print(f"  ERROR: {msg}", file=sys.stderr)


def warn(msg: str):
    global warnings
    warnings += 1
    print(f"  WARNING: {msg}", file=sys.stderr)


def main():
    global errors, warnings

    print("Validating RAG corpus...")

    if not CHUNKS_PATH.exists():
        error(f"Chunks file not found: {CHUNKS_PATH}")
        return False

    if not LESSONS_PATH.exists():
        error(f"Lessons file not found: {LESSONS_PATH}")
        return False

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    with open(LESSONS_PATH, encoding="utf-8") as f:
        lessons = json.load(f)

    lesson_ids = {l["id"] for l in lessons}

    if not isinstance(chunks, list):
        error("Chunks file is not a JSON array")
        return False

    if not chunks:
        error("Chunks file is empty")
        return False

    # Check unique IDs
    seen_ids = set()
    for chunk in chunks:
        cid = chunk.get("chunk_id", "")
        if cid in seen_ids:
            error(f"Duplicate chunk_id: {cid}")
        seen_ids.add(cid)

    # Check each chunk
    for chunk in chunks:
        cid = chunk.get("chunk_id", "unknown")

        # Required fields
        missing = REQUIRED_CHUNK_FIELDS - set(chunk.keys())
        if missing:
            error(f"Chunk {cid} missing fields: {sorted(missing)}")
            continue

        # Lesson ID resolves
        if chunk["lesson_id"] not in lesson_ids:
            error(f"Chunk {cid} references unknown lesson_id: {chunk['lesson_id']}")

        # Non-empty text
        if not chunk["chunk_text"].strip():
            error(f"Chunk {cid} has empty chunk_text")

        # Reasonable token count
        if chunk["token_count"] <= 0:
            warn(f"Chunk {cid} has token_count={chunk['token_count']}")

        if chunk["token_count"] > 5000:
            warn(f"Chunk {cid} has very high token_count={chunk['token_count']}")

    print(f"\n  Chunks validated: {len(chunks)}")
    print(f"  Unique lesson IDs referenced: {len({c['lesson_id'] for c in chunks})}")
    print(f"  Errors: {errors}")
    print(f"  Warnings: {warnings}")

    if errors > 0:
        print("\nFAILED.", file=sys.stderr)
        return False

    print("\nPASSED.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

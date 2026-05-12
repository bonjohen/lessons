"""Build RAG corpus — chunk lessons by heading for vector retrieval.

Reads src/content/generated/lessons.json, splits each lesson's markdown
content into chunks by H2 headings, and writes:
  - data/rag-chunks.json   (list of chunk records)
  - data/rag-manifest.json (corpus metadata)
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LESSONS_JSON = PROJECT_ROOT / "src" / "content" / "generated" / "lessons.json"
CHUNKS_OUTPUT = PROJECT_ROOT / "data" / "rag-chunks.json"
MANIFEST_OUTPUT = PROJECT_ROOT / "data" / "rag-manifest.json"


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 tokens per word."""
    return max(1, int(len(text.split()) * 1.33))


def content_hash(text: str) -> str:
    """SHA-256 hash of chunk text for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def chunk_by_heading(content: str, lesson_id: str, lesson_meta: dict) -> list[dict]:
    """Split markdown content into chunks by H2 headings.

    Each chunk includes the heading and all content up to the next H2.
    Content before the first H2 becomes chunk 0 (the intro).
    """
    lines = content.split("\n")
    chunks = []
    current_heading = "Introduction"
    current_lines: list[str] = []
    heading_path = lesson_meta.get("title", "")

    def flush_chunk():
        text = "\n".join(current_lines).strip()
        if not text:
            return
        chunk_index = len(chunks)
        full_heading = (
            f"{heading_path} > {current_heading}"
            if current_heading != "Introduction"
            else heading_path
        )
        lesson_url = f"/lessons/{lesson_id}"

        chunks.append(
            {
                "chunk_id": f"{lesson_id}-{chunk_index}",
                "lesson_id": lesson_id,
                "repo_id": lesson_meta.get("repo_id", ""),
                "title": lesson_meta.get("title", ""),
                "summary": lesson_meta.get("summary", ""),
                "lesson_url": lesson_url,
                "chunk_index": chunk_index,
                "heading_path": full_heading,
                "chunk_text": text,
                "token_count": estimate_tokens(text),
                "tags": lesson_meta.get("tags", []),
                "content_hash": content_hash(text),
                "lesson_type": lesson_meta.get("lesson_type", ""),
                "phase": lesson_meta.get("phase", ""),
                "status": lesson_meta.get("status", ""),
                "embedding_model": "",
                "indexed_at": "",
            }
        )

    for line in lines:
        h2_match = re.match(r"^##\s+(.+)$", line.strip())
        if h2_match:
            flush_chunk()
            current_heading = h2_match.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_chunk()
    return chunks


def build_corpus(lessons_path: Path = LESSONS_JSON) -> tuple[list[dict], dict]:
    """Build RAG chunks from lessons.json.

    Returns (chunks, manifest).
    """
    with open(lessons_path, encoding="utf-8") as f:
        lessons = json.load(f)

    all_chunks = []
    skipped = 0

    for lesson in lessons:
        content = lesson.get("content", "").strip()
        if not content:
            skipped += 1
            continue

        meta = {
            "title": lesson.get("title", ""),
            "summary": lesson.get("summary", ""),
            "repo_id": lesson.get("repo_id", ""),
            "tags": lesson.get("tags", []),
            "lesson_type": lesson.get("lesson_type", ""),
            "phase": lesson.get("phase", ""),
            "status": lesson.get("status", ""),
        }

        chunks = chunk_by_heading(content, lesson["id"], meta)
        all_chunks.extend(chunks)

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(lessons_path),
        "total_lessons": len(lessons),
        "lessons_skipped": skipped,
        "lessons_chunked": len(lessons) - skipped,
        "total_chunks": len(all_chunks),
        "avg_tokens_per_chunk": (
            round(sum(c["token_count"] for c in all_chunks) / len(all_chunks))
            if all_chunks
            else 0
        ),
    }

    return all_chunks, manifest


def main():
    if not LESSONS_JSON.exists():
        print(
            f"ERROR: {LESSONS_JSON} not found. Run 'npm run harvest' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Building RAG corpus...")
    chunks, manifest = build_corpus()

    CHUNKS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(CHUNKS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    with open(MANIFEST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  Lessons processed: {manifest['lessons_chunked']}")
    print(f"  Chunks generated:  {manifest['total_chunks']}")
    print(f"  Avg tokens/chunk:  {manifest['avg_tokens_per_chunk']}")
    print(f"  Output: {CHUNKS_OUTPUT}")
    print(f"  Manifest: {MANIFEST_OUTPUT}")


if __name__ == "__main__":
    main()

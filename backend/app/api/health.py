"""Health check endpoint."""

from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAG_CHUNKS_PATH = PROJECT_ROOT / "data" / "rag-chunks.json"
RAG_MANIFEST_PATH = PROJECT_ROOT / "data" / "rag-manifest.json"


@router.get("/health")
async def health():
    """Return backend health status."""
    corpus_exists = RAG_CHUNKS_PATH.exists()
    manifest_exists = RAG_MANIFEST_PATH.exists()

    chunk_count = 0
    if corpus_exists:
        import json

        with open(RAG_CHUNKS_PATH, encoding="utf-8") as f:
            chunks = json.load(f)
            chunk_count = len(chunks)

    return {
        "status": "ok",
        "version": "2.0.0",
        "deployment_profile": "local",
        "corpus_status": {
            "chunks_file": corpus_exists,
            "manifest_file": manifest_exists,
            "chunk_count": chunk_count,
        },
    }

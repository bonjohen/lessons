"""Gaps API — create, list, and manage corpus gap records."""

from fastapi import APIRouter, HTTPException, Query

from app.api._deps import get_gap_store
from app.models.schemas import GapRecord

router = APIRouter()


@router.get("/api/gaps")
async def list_gaps(
    status: str | None = Query(None, description="Filter by status"),
    has_candidates: bool | None = Query(None, description="Filter by whether gap has candidates"),
):
    """List corpus gaps with optional filters."""
    store = get_gap_store()
    gaps = store.list_gaps(status=status, has_candidates=has_candidates)
    return {"gaps": gaps, "total": len(gaps)}


@router.get("/api/gaps/{gap_id}")
async def get_gap(gap_id: str):
    """Get a single gap by ID."""
    store = get_gap_store()
    gap = store.get_gap(gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail=f"Gap {gap_id} not found")
    return gap


@router.post("/api/gaps")
async def create_gap(gap: GapRecord):
    """Create or update a corpus gap."""
    store = get_gap_store()
    stored = store.create_or_update(gap.model_dump())
    return stored


@router.patch("/api/gaps/{gap_id}/status")
async def update_gap_status(gap_id: str, status: str = Query(...)):
    """Update a gap's status."""
    store = get_gap_store()
    result = store.update_status(gap_id, status)
    if result is None:
        raise HTTPException(status_code=400, detail=f"Invalid status or gap {gap_id} not found")
    return result

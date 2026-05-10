"""JSON-backed gap storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

DEFAULT_GAPS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "gaps" / "corpus-gaps.json"

# Valid status transitions
VALID_STATUSES = {
    "open",
    "searching",
    "candidates_found",
    "lessons_staged",
    "owner_coordination_needed",
    "resolved",
    "closed_no_action",
}


class GapStore:
    """JSON-backed CRUD for corpus gap records."""

    def __init__(self, path: Path | None = None):
        self._path = path or DEFAULT_GAPS_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(self._path.with_suffix(".lock"))

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        with open(self._path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, gaps: list[dict]):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(gaps, f, indent=2, ensure_ascii=False)

    def list_gaps(self, status: str | None = None, has_candidates: bool | None = None) -> list[dict]:
        """List gaps, optionally filtered."""
        gaps = self._load()
        if status:
            gaps = [g for g in gaps if g.get("status") == status]
        if has_candidates is True:
            gaps = [g for g in gaps if g.get("candidate_repo_ids")]
        elif has_candidates is False:
            gaps = [g for g in gaps if not g.get("candidate_repo_ids")]
        return gaps

    def get_gap(self, gap_id: str) -> dict | None:
        """Get a single gap by ID."""
        for gap in self._load():
            if gap.get("gap_id") == gap_id:
                return gap
        return None

    def create_or_update(self, gap: dict) -> dict:
        """Create a new gap or update an existing one with the same normalized_topic.

        If a gap with a similar topic exists, merge the trigger query and update.
        """
        with self._lock:
            gaps = self._load()
            gap_id = gap["gap_id"]

            # Check for existing gap with same ID
            for i, existing in enumerate(gaps):
                if existing["gap_id"] == gap_id:
                    # Update existing
                    existing["updated_date"] = datetime.now(timezone.utc).isoformat()
                    if gap["trigger_query"] != existing.get("trigger_query"):
                        # Append new trigger query to notes
                        existing.setdefault("additional_queries", [])
                        existing["additional_queries"].append(gap["trigger_query"])
                    # Update retrieval summary with latest
                    existing["retrieval_summary"] = gap.get("retrieval_summary", existing.get("retrieval_summary", ""))
                    existing["confidence_score"] = gap.get("confidence_score", existing.get("confidence_score", 0))
                    gaps[i] = existing
                    self._save(gaps)
                    return existing

            # Create new
            gaps.append(gap)
            self._save(gaps)
            return gap

    def update_status(self, gap_id: str, status: str) -> dict | None:
        """Update a gap's status."""
        if status not in VALID_STATUSES:
            return None

        with self._lock:
            gaps = self._load()
            for i, gap in enumerate(gaps):
                if gap["gap_id"] == gap_id:
                    gap["status"] = status
                    gap["updated_date"] = datetime.now(timezone.utc).isoformat()
                    gaps[i] = gap
                    self._save(gaps)
                    return gap
        return None

    def count(self) -> int:
        return len(self._load())

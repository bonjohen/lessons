"""JSON-backed gap storage."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock
from pydantic import ValidationError

from app.models.schemas import GapRecord

logger = logging.getLogger(__name__)

DEFAULT_GAPS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "gaps" / "corpus-gaps.json"
DEFAULT_REVIEW_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "review" / "gaps"

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

    def __init__(self, path: Path | None = None, review_dir: Path | None = None):
        self._path = path or DEFAULT_GAPS_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(self._path.with_suffix(".lock"))
        self._review_dir = review_dir or DEFAULT_REVIEW_DIR
        self._review_dir.mkdir(parents=True, exist_ok=True)

    def _write_review_md(self, gap: dict) -> None:
        """Write a human-readable markdown summary for review."""
        gap_id = gap.get("gap_id", "unknown")
        review_file = self._review_dir / f"{gap_id}.md"
        lines = [
            "---",
            f"gap_id: {gap_id}",
            f"status: {gap.get('status', 'open')}",
            f"created: {gap.get('created_date', '')}",
            f"updated: {gap.get('updated_date', '')}",
            f"confidence: {gap.get('confidence_score', 0)}",
            f"gap_type: {gap.get('gap_type', 'missing_topic')}",
            "---",
            "",
            f"# Gap: {gap.get('normalized_topic', gap_id)}",
            "",
            f"**Trigger query:** {gap.get('trigger_query', '')}",
            "",
            f"**Retrieval summary:** {gap.get('retrieval_summary', 'N/A')}",
            "",
        ]
        concepts = gap.get("missing_concepts", [])
        if concepts:
            lines.append("**Missing concepts:** " + ", ".join(concepts))
            lines.append("")
        queries = gap.get("suggested_github_queries", [])
        if queries:
            lines.append("**Suggested GitHub queries:**")
            for q in queries:
                lines.append(f"- {q}")
            lines.append("")
        best = gap.get("best_matching_lessons", [])
        if best:
            lines.append("**Best matching lessons:** " + ", ".join(best))
            lines.append("")
        review_file.write_text("\n".join(lines), encoding="utf-8")

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        with open(self._path, encoding="utf-8") as f:
            raw = json.load(f)
        valid = []
        for item in raw:
            try:
                GapRecord.model_validate(item)
                valid.append(item)
            except ValidationError as e:
                logger.warning("Skipping invalid gap record %s: %s", item.get("gap_id", "?"), e)
        return valid

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
                    self._write_review_md(existing)
                    return existing

            # Create new
            gaps.append(gap)
            self._save(gaps)
            self._write_review_md(gap)
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
                    self._write_review_md(gap)
                    return gap
        return None

    def count(self) -> int:
        return len(self._load())

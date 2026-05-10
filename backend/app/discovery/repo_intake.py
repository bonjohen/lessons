"""Repository intake — clone/pull external candidates into workspace."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from pydantic import ValidationError

from app.models.schemas import CandidateRepo

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXTERNAL_WORKSPACE = PROJECT_ROOT / ".external" / "repos"
CANDIDATE_REPOS_PATH = PROJECT_ROOT / "data" / "external" / "candidate-repos.json"

CLONE_TIMEOUT_SECONDS = int(os.environ.get("CLONE_TIMEOUT_SECONDS", "60"))


def clone_or_pull(owner: str, repo_name: str, clone_url: str) -> Path | None:
    """Clone or pull a repo into the external workspace.

    Returns the repo directory path, or None if the operation times out.
    """
    repo_dir = EXTERNAL_WORKSPACE / owner / repo_name
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    try:
        if (repo_dir / ".git").exists():
            logger.info("Pulling %s/%s", owner, repo_name)
            subprocess.run(
                ["git", "-C", str(repo_dir), "pull", "--ff-only"],
                capture_output=True,
                timeout=CLONE_TIMEOUT_SECONDS,
            )
        else:
            logger.info("Cloning %s/%s (depth=1, timeout=%ds)", owner, repo_name, CLONE_TIMEOUT_SECONDS)
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(repo_dir)],
                capture_output=True,
                timeout=CLONE_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired:
        logger.error("Clone/pull timed out for %s/%s after %ds", owner, repo_name, CLONE_TIMEOUT_SECONDS)
        return None

    return repo_dir


def save_candidate_repo(candidate: dict):
    """Save a candidate repo record to candidate-repos.json."""
    CANDIDATE_REPOS_PATH.parent.mkdir(parents=True, exist_ok=True)

    repos = []
    if CANDIDATE_REPOS_PATH.exists():
        with open(CANDIDATE_REPOS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            try:
                CandidateRepo.model_validate(item)
                repos.append(item)
            except ValidationError as e:
                logger.warning("Skipping invalid candidate repo %s: %s", item.get("candidate_repo_id", "?"), e)

    # Update or append
    existing_idx = next(
        (i for i, r in enumerate(repos) if r["candidate_repo_id"] == candidate["candidate_repo_id"]), None
    )
    if existing_idx is not None:
        repos[existing_idx] = candidate
    else:
        repos.append(candidate)

    with open(CANDIDATE_REPOS_PATH, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)


def build_candidate_record(repo: dict, gap: dict, score: float, reasons: list[str]) -> dict:
    """Build a candidate repo record from search result + scoring."""
    cid = f"candidate_{repo['owner']}_{repo['repo_name']}".replace("-", "_").replace(".", "_")
    return {
        "candidate_repo_id": cid,
        "gap_id": gap.get("gap_id", ""),
        "github_url": repo["github_url"],
        "owner": repo["owner"],
        "repo_name": repo["repo_name"],
        "description": repo.get("description", ""),
        "primary_language": repo.get("primary_language", ""),
        "stars": repo.get("stars", 0),
        "last_updated": repo.get("last_updated", ""),
        "license": repo.get("license", ""),
        "clone_url": repo.get("clone_url", ""),
        "local_path": str(EXTERNAL_WORKSPACE / repo["owner"] / repo["repo_name"]),
        "score": score,
        "score_reasons": reasons,
        "harvest_status": "pending",
        "candidate_lesson_paths": [],
        "todo_ids": [],
    }

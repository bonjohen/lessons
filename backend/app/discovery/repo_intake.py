"""Repository intake — clone/pull external candidates into workspace."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXTERNAL_WORKSPACE = PROJECT_ROOT / ".external" / "repos"
CANDIDATE_REPOS_PATH = PROJECT_ROOT / "data" / "external" / "candidate-repos.json"


def clone_or_pull(owner: str, repo_name: str, clone_url: str) -> Path:
    """Clone or pull a repo into the external workspace."""
    repo_dir = EXTERNAL_WORKSPACE / owner / repo_name
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    if (repo_dir / ".git").exists():
        subprocess.run(["git", "-C", str(repo_dir), "pull", "--ff-only"], capture_output=True, timeout=60)
    else:
        subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(repo_dir)],
            capture_output=True, timeout=120,
        )

    return repo_dir


def save_candidate_repo(candidate: dict):
    """Save a candidate repo record to candidate-repos.json."""
    CANDIDATE_REPOS_PATH.parent.mkdir(parents=True, exist_ok=True)

    repos = []
    if CANDIDATE_REPOS_PATH.exists():
        with open(CANDIDATE_REPOS_PATH, encoding="utf-8") as f:
            repos = json.load(f)

    # Update or append
    existing_idx = next((i for i, r in enumerate(repos) if r["candidate_repo_id"] == candidate["candidate_repo_id"]), None)
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

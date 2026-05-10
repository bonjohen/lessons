"""GitHub discovery API — search repos, harvest candidates."""

import os
import re

from fastapi import APIRouter, HTTPException

from app.api._deps import get_gap_store
from app.discovery.candidate_scorer import score_candidate
from app.discovery.github_search import GitHubSearcher
from app.discovery.lesson_extractor import detect_extractable_content, generate_candidate_lesson
from app.discovery.repo_intake import build_candidate_record, clone_or_pull, save_candidate_repo
from app.discovery.todo_writer import create_todo

router = APIRouter()

_OWNER_REPO_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


def _check_discovery_enabled():
    """Raise 403 if GitHub discovery is disabled (default)."""
    enabled = os.environ.get("GITHUB_DISCOVERY_ENABLED", "false").lower()
    if enabled not in ("true", "1", "yes"):
        raise HTTPException(
            status_code=403,
            detail="GitHub discovery is disabled. Set GITHUB_DISCOVERY_ENABLED=true to enable.",
        )


def _validate_owner_repo(owner: str, repo_name: str):
    """Validate owner and repo_name against safe pattern."""
    if not _OWNER_REPO_RE.match(owner):
        raise HTTPException(status_code=422, detail=f"Invalid owner: {owner!r}")
    if not _OWNER_REPO_RE.match(repo_name):
        raise HTTPException(status_code=422, detail=f"Invalid repo_name: {repo_name!r}")


@router.post("/github/search")
async def search_github(
    gap_id: str,
    max_results: int = 20,
    languages: list[str] | None = None,
    min_stars: int = 0,
):
    """Search GitHub for repos relevant to a corpus gap."""
    _check_discovery_enabled()

    store = get_gap_store()
    gap = store.get_gap(gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail=f"Gap {gap_id} not found")

    queries = gap.get("suggested_github_queries", [])
    if not queries:
        raise HTTPException(status_code=400, detail="Gap has no suggested search queries")

    searcher = GitHubSearcher()
    search_result = searcher.search_repos(queries, languages=languages, min_stars=min_stars, max_results=max_results)

    # Score candidates
    candidates = []
    for repo in search_result["repos"]:
        score, reasons = score_candidate(repo, gap)
        candidates.append(
            {
                **repo,
                "score": score,
                "score_reasons": reasons,
            }
        )

    # Sort by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Update gap status
    store.update_status(gap_id, "searching")

    return {"gap_id": gap_id, "candidates": candidates}


@router.post("/github/harvest-candidate")
async def harvest_candidate(
    gap_id: str,
    owner: str,
    repo_name: str,
):
    """Clone a candidate repo, extract lessons, create TODOs.

    clone_url and github_url are derived from owner/repo_name for safety.
    """
    _check_discovery_enabled()
    _validate_owner_repo(owner, repo_name)

    store = get_gap_store()
    gap = store.get_gap(gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail=f"Gap {gap_id} not found")

    # Derive URLs from validated owner/repo_name
    github_url = f"https://github.com/{owner}/{repo_name}"
    clone_url = f"https://github.com/{owner}/{repo_name}.git"

    # Build candidate record
    repo_info = {
        "github_url": github_url,
        "owner": owner,
        "repo_name": repo_name,
        "clone_url": clone_url,
    }
    candidate = build_candidate_record(repo_info, gap, score=0.0, reasons=[])

    # Clone/pull
    repo_dir = clone_or_pull(owner, repo_name, clone_url)
    if repo_dir is None:
        raise HTTPException(status_code=504, detail=f"Clone timed out for {owner}/{repo_name}")

    # Detect extractable content
    content_files = detect_extractable_content(repo_dir)

    # Generate candidate lesson
    lesson_path = generate_candidate_lesson(repo_dir, candidate, gap, content_files)

    staged_lessons = []
    todo_ids = []

    if lesson_path:
        lesson_rel = str(lesson_path)
        staged_lessons.append(lesson_rel)

        # Create coordination TODO
        todo = create_todo(candidate, lesson_rel, gap_id=gap_id)
        todo_ids.append(todo["todo_id"])

        # Update candidate record
        candidate["harvest_status"] = "staged"
        candidate["candidate_lesson_paths"] = staged_lessons
        candidate["todo_ids"] = todo_ids
    else:
        candidate["harvest_status"] = "failed"

    save_candidate_repo(candidate)

    # Update gap status
    store.update_status(gap_id, "lessons_staged" if staged_lessons else "candidates_found")

    return {
        "candidate_repo_id": candidate["candidate_repo_id"],
        "staged_lessons": staged_lessons,
        "todos": todo_ids,
    }

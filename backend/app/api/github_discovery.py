"""GitHub discovery API — search repos, harvest candidates."""

from fastapi import APIRouter, HTTPException

from app.api._deps import get_gap_store
from app.discovery.candidate_scorer import score_candidate
from app.discovery.github_search import GitHubSearcher
from app.discovery.lesson_extractor import detect_extractable_content, generate_candidate_lesson
from app.discovery.repo_intake import build_candidate_record, clone_or_pull, save_candidate_repo
from app.discovery.todo_writer import create_todo

router = APIRouter()


@router.post("/api/github/search")
async def search_github(
    gap_id: str,
    max_results: int = 20,
    languages: list[str] | None = None,
    min_stars: int = 0,
):
    """Search GitHub for repos relevant to a corpus gap."""
    store = get_gap_store()
    gap = store.get_gap(gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail=f"Gap {gap_id} not found")

    queries = gap.get("suggested_github_queries", [])
    if not queries:
        raise HTTPException(status_code=400, detail="Gap has no suggested search queries")

    searcher = GitHubSearcher()
    results = searcher.search_repos(queries, languages=languages, min_stars=min_stars, max_results=max_results)

    # Score candidates
    candidates = []
    for repo in results:
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


@router.post("/api/github/harvest-candidate")
async def harvest_candidate(
    gap_id: str,
    github_url: str,
    owner: str,
    repo_name: str,
    clone_url: str,
):
    """Clone a candidate repo, extract lessons, create TODOs."""
    store = get_gap_store()
    gap = store.get_gap(gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail=f"Gap {gap_id} not found")

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

"""TODO writer — create coordination TODOs for external lessons."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock
from pydantic import ValidationError

from app.models.schemas import TodoRecord

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TODOS_PATH = PROJECT_ROOT / "data" / "todos" / "todos.json"
REVIEW_TODOS_DIR = PROJECT_ROOT / "docs" / "review" / "todos"


def create_todo(
    candidate: dict,
    lesson_path: str,
    gap_id: str = "",
) -> dict:
    """Create a coordination TODO for an external candidate lesson."""
    owner = candidate["owner"]
    repo_name = candidate["repo_name"]
    github_url = candidate["github_url"]

    todo_id = f"todo_{owner}_{repo_name}".replace("-", "_").replace(".", "_")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    todo = {
        "todo_id": todo_id,
        "title": f"Coordinate with owner for candidate lesson from {owner}/{repo_name}",
        "notes": (
            "Review generated lesson, verify attribution, and decide whether to contact "
            "the source project owner about contributing or referencing the lesson."
        ),
        "status": "open",
        "priority": 2,
        "severity": 2,
        "created_date": today,
        "due_date": "",
        "completion_date": "",
        "source_gap_id": gap_id,
        "source_project_url": github_url,
        "candidate_lesson_path": lesson_path,
    }

    _save_todo(todo)
    _write_review_md(todo)
    return todo


def _write_review_md(todo: dict) -> None:
    """Write a human-readable markdown summary for review."""
    REVIEW_TODOS_DIR.mkdir(parents=True, exist_ok=True)
    todo_id = todo.get("todo_id", "unknown")
    review_file = REVIEW_TODOS_DIR / f"{todo_id}.md"
    lines = [
        "---",
        f"todo_id: {todo_id}",
        f"status: {todo.get('status', 'open')}",
        f"priority: {todo.get('priority', 3)}",
        f"severity: {todo.get('severity', 3)}",
        f"created: {todo.get('created_date', '')}",
        f"source_project_url: {todo.get('source_project_url', '')}",
        f"candidate_lesson_path: {todo.get('candidate_lesson_path', '')}",
        "---",
        "",
        f"# {todo.get('title', todo_id)}",
        "",
        todo.get("notes", ""),
        "",
    ]
    review_file.write_text("\n".join(lines), encoding="utf-8")


def _save_todo(todo: dict):
    """Append or update a TODO in the todos file."""
    TODOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(TODOS_PATH.with_suffix(".lock"))

    with lock:
        todos = []
        if TODOS_PATH.exists():
            with open(TODOS_PATH, encoding="utf-8") as f:
                todos = json.load(f)

        existing_idx = next((i for i, t in enumerate(todos) if t["todo_id"] == todo["todo_id"]), None)
        if existing_idx is not None:
            todos[existing_idx] = todo
        else:
            todos.append(todo)

        with open(TODOS_PATH, "w", encoding="utf-8") as f:
            json.dump(todos, f, indent=2, ensure_ascii=False)


def list_todos() -> list[dict]:
    """List all TODOs."""
    if not TODOS_PATH.exists():
        return []
    with open(TODOS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    valid = []
    for item in raw:
        try:
            TodoRecord.model_validate(item)
            valid.append(item)
        except ValidationError as e:
            logger.warning("Skipping invalid todo record %s: %s", item.get("todo_id", "?"), e)
    return valid

"""TODO writer — create coordination TODOs for external lessons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TODOS_PATH = PROJECT_ROOT / "data" / "todos" / "todos.json"


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
            f"Review generated lesson, verify attribution, and decide whether to contact "
            f"the source project owner about contributing or referencing the lesson."
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
    return todo


def _save_todo(todo: dict):
    """Append or update a TODO in the todos file."""
    TODOS_PATH.parent.mkdir(parents=True, exist_ok=True)

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
        return json.load(f)

"""TODOs API — list coordination TODOs."""

from fastapi import APIRouter

from app.discovery.todo_writer import list_todos

router = APIRouter()


@router.get("/api/todos")
async def get_todos():
    """List all coordination TODOs."""
    todos = list_todos()
    return {"todos": todos, "total": len(todos)}

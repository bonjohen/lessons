"""Lessons Hub RAG backend — FastAPI application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.gaps import router as gaps_router
from app.api.github_discovery import router as discovery_router
from app.api.health import router as health_router
from app.api.retrieve import router as retrieve_router
from app.api.todos import router as todos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    yield


app = FastAPI(
    title="Lessons Hub RAG API",
    version="2.0.0",
    lifespan=lifespan,
)

_DEFAULT_ORIGINS = [
    "http://localhost:4321",
    "http://localhost:3000",
    "http://127.0.0.1:4321",
    "http://127.0.0.1:3000",
]
_cors_env = os.environ.get("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] if _cors_env else _DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(retrieve_router)
app.include_router(gaps_router)
app.include_router(discovery_router)
app.include_router(todos_router)

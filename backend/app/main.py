"""Lessons Hub RAG backend — FastAPI application."""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.gaps import router as gaps_router
from app.api.github_discovery import router as discovery_router
from app.api.health import router as health_router
from app.api.retrieve import router as retrieve_router
from app.api.todos import router as todos_router
from app.metrics import METRICS_AVAILABLE, request_duration_seconds, requests_total


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    from app.logging_config import configure_logging

    configure_logging()
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


# --- Metrics middleware ---


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if not METRICS_AVAILABLE:
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    requests_total.labels(method=request.method, path=path, status=response.status_code).inc()
    request_duration_seconds.labels(method=request.method, path=path).observe(duration)
    return response


# --- Metrics endpoint ---


@app.get("/metrics")
async def metrics_endpoint():
    if not METRICS_AVAILABLE:
        return Response(content="prometheus_client not installed", status_code=404)
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# --- Routers ---

app.include_router(health_router)

_api_routers = [chat_router, retrieve_router, gaps_router, discovery_router, todos_router]
for _router in _api_routers:
    app.include_router(_router, prefix="/api")
    app.include_router(_router, prefix="/api/v1")

"""Pydantic models for the Lessons Hub RAG API."""

from __future__ import annotations

from pydantic import BaseModel, Field

# --- RAG Chunk ---


class ChunkRecord(BaseModel):
    """A single RAG chunk derived from a lesson."""

    chunk_id: str
    lesson_id: str
    repo_id: str
    title: str
    summary: str
    lesson_url: str
    chunk_index: int
    heading_path: str
    chunk_text: str
    token_count: int
    tags: list[str] = Field(default_factory=list)
    content_hash: str
    embedding_model: str = ""
    indexed_at: str = ""


# --- Chat ---


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str
    top_k: int = 8
    filters: ChatFilters | None = None


class ChatFilters(BaseModel):
    """Optional filters for chat retrieval."""

    repo: str | None = None
    tags: list[str] = Field(default_factory=list)
    lesson_type: str | None = None


class RelevantLesson(BaseModel):
    """A lesson cited in a chat response."""

    lesson_id: str
    title: str
    repo_name: str
    similarity_score: float
    lesson_url: str


class ChatResponse(BaseModel):
    """Chat response with answer and relevant lessons."""

    answer: str
    relevant_lessons: list[RelevantLesson] = Field(default_factory=list)
    gap_detected: bool = False
    gap_id: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)


# --- Retrieve ---


class RetrieveRequest(BaseModel):
    """Retrieve request — returns chunks without generation."""

    query: str
    top_k: int = 8
    filters: ChatFilters | None = None


class RetrieveResponse(BaseModel):
    """Retrieve response — ranked chunks."""

    query: str
    chunks: list[ChunkResult] = Field(default_factory=list)


class ChunkResult(BaseModel):
    """A single chunk result from retrieval."""

    chunk_id: str
    lesson_id: str
    title: str
    heading_path: str
    chunk_text: str
    similarity_score: float
    tags: list[str] = Field(default_factory=list)


# --- Corpus Gap ---


class GapRecord(BaseModel):
    """A corpus gap — topic the lessons cannot answer well."""

    gap_id: str
    created_date: str = ""
    updated_date: str = ""
    status: str = "open"
    trigger_query: str
    normalized_topic: str
    missing_concepts: list[str] = Field(default_factory=list)
    retrieval_summary: str = ""
    best_matching_lessons: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    suggested_github_queries: list[str] = Field(default_factory=list)
    candidate_repo_ids: list[str] = Field(default_factory=list)
    todo_ids: list[str] = Field(default_factory=list)
    resolution_notes: str = ""
    gap_type: str = "missing_topic"


# --- Candidate Repository ---


class CandidateRepo(BaseModel):
    """An external repo discovered via GitHub search."""

    candidate_repo_id: str
    gap_id: str
    github_url: str
    owner: str
    repo_name: str
    description: str = ""
    primary_language: str = ""
    stars: int = 0
    last_updated: str = ""
    license: str = ""
    clone_url: str = ""
    local_path: str = ""
    score: float = 0.0
    score_reasons: list[str] = Field(default_factory=list)
    harvest_status: str = "pending"
    candidate_lesson_paths: list[str] = Field(default_factory=list)
    todo_ids: list[str] = Field(default_factory=list)


# --- TODO ---


class TodoRecord(BaseModel):
    """A coordination TODO for external lesson handling."""

    todo_id: str
    title: str
    notes: str = ""
    status: str = "open"
    priority: int = 3
    severity: int = 3
    created_date: str = ""
    due_date: str = ""
    completion_date: str = ""
    source_gap_id: str = ""
    source_project_url: str = ""
    candidate_lesson_path: str = ""

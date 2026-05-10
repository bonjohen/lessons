"""Tests for chat and retrieve endpoints with mocked adapters."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_generator(answer="Test answer", lessons=None):
    """Create a mock generator that returns a fixed response."""
    gen = MagicMock()
    gen.generate.return_value = {
        "answer": answer,
        "relevant_lessons": lessons
        or [
            {
                "lesson_id": "test-lesson-1",
                "title": "Test Lesson",
                "repo_name": "test-repo",
                "similarity_score": 0.85,
                "lesson_url": "/lessons/test-lesson-1",
            }
        ],
        "chunks": [],
    }
    return gen


def _mock_retriever(chunks=None):
    """Create a mock retriever that returns fixed chunks."""
    ret = MagicMock()
    ret.retrieve.return_value = chunks or [
        {
            "chunk_id": "test-lesson-1-0",
            "lesson_id": "test-lesson-1",
            "title": "Test Lesson",
            "heading_path": "Test > Section",
            "chunk_text": "Some lesson content",
            "similarity_score": 0.85,
            "tags": ["testing"],
        }
    ]
    return ret


class TestChatEndpoint:
    def test_chat_with_mock(self):
        with patch("app.api._deps._generator", _mock_generator()):
            response = client.post("/api/chat", json={"message": "How do I test?"})
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test answer"
            assert len(data["relevant_lessons"]) == 1
            assert data["relevant_lessons"][0]["title"] == "Test Lesson"

    def test_chat_includes_lesson_url(self):
        with patch("app.api._deps._generator", _mock_generator()):
            response = client.post("/api/chat", json={"message": "question"})
            data = response.json()
            assert data["relevant_lessons"][0]["lesson_url"] == "/lessons/test-lesson-1"

    def test_chat_no_backend(self):
        with (
            patch("app.api._deps._generator", None),
            patch("app.api._deps._retriever", None),
            patch("app.api._deps._init"),
        ):
            response = client.post("/api/chat", json={"message": "question"})
            assert response.status_code == 200
            data = response.json()
            assert "not initialized" in data["answer"]


class TestRetrieveEndpoint:
    def test_retrieve_with_mock(self):
        with patch("app.api._deps._retriever", _mock_retriever()):
            response = client.post("/api/retrieve", json={"query": "testing"})
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "testing"
            assert len(data["chunks"]) == 1
            assert data["chunks"][0]["chunk_id"] == "test-lesson-1-0"

    def test_retrieve_no_backend(self):
        with (
            patch("app.api._deps._retriever", None),
            patch("app.api._deps._generator", None),
            patch("app.api._deps._init"),
        ):
            response = client.post("/api/retrieve", json={"query": "testing"})
            assert response.status_code == 200
            data = response.json()
            assert data["chunks"] == []

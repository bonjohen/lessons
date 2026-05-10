"""Tests for Prometheus metrics endpoint and API v1 versioned routes."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMetricsEndpoint:
    def test_metrics_endpoint_responds(self):
        """Returns 200 with metrics when prometheus_client is installed, 404 otherwise."""
        from app.metrics import METRICS_AVAILABLE

        response = client.get("/metrics")
        if METRICS_AVAILABLE:
            assert response.status_code == 200
            assert b"requests_total" in response.content
            assert b"request_duration_seconds" in response.content
        else:
            assert response.status_code == 404


class TestAPIVersioning:
    def _mock_generator(self):
        gen = MagicMock()
        gen.generate.return_value = {
            "answer": "versioned answer",
            "relevant_lessons": [
                {
                    "lesson_id": "v1-lesson",
                    "title": "V1 Lesson",
                    "repo_name": "test-repo",
                    "similarity_score": 0.9,
                    "lesson_url": "/lessons/v1-lesson",
                }
            ],
            "chunks": [],
        }
        return gen

    def test_v1_chat_returns_same_schema(self):
        mock_gen = self._mock_generator()
        with patch("app.api.chat.get_generator", return_value=mock_gen):
            response = client.post("/api/v1/chat", json={"message": "test question"})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "relevant_lessons" in data

    def test_v1_chat_matches_unversioned(self):
        mock_gen = self._mock_generator()
        with patch("app.api.chat.get_generator", return_value=mock_gen):
            v1 = client.post("/api/v1/chat", json={"message": "test"})
            unversioned = client.post("/api/chat", json={"message": "test"})
        assert v1.status_code == unversioned.status_code
        assert set(v1.json().keys()) == set(unversioned.json().keys())

    def test_v1_health_not_mounted(self):
        """Health is not under /api, so /api/v1/health should 404."""
        response = client.get("/api/v1/health")
        assert response.status_code in (404, 405)

    def test_v1_gaps_accessible(self):
        response = client.get("/api/v1/gaps")
        assert response.status_code == 200

"""Tests for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_has_version():
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "2.0.0"


def test_health_has_status():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_has_corpus_status():
    response = client.get("/health")
    data = response.json()
    assert "corpus_status" in data
    cs = data["corpus_status"]
    assert "chunks_file" in cs
    assert "chunk_count" in cs


def test_health_has_deployment_profile():
    response = client.get("/health")
    data = response.json()
    assert data["deployment_profile"] == "local"

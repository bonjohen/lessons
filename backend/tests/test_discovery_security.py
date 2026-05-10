"""Tests for GitHub discovery security hardening."""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestDiscoveryGating:
    """GITHUB_DISCOVERY_ENABLED flag controls access."""

    def test_search_disabled_by_default(self):
        """Search returns 403 when GITHUB_DISCOVERY_ENABLED is not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITHUB_DISCOVERY_ENABLED", None)
            resp = client.post("/api/github/search", params={"gap_id": "gap_test"})
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_harvest_disabled_by_default(self):
        """Harvest returns 403 when GITHUB_DISCOVERY_ENABLED is not set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GITHUB_DISCOVERY_ENABLED", None)
            resp = client.post(
                "/api/github/harvest-candidate",
                params={"gap_id": "g", "owner": "a", "repo_name": "b"},
            )
        assert resp.status_code == 403

    def test_search_enabled_when_flag_set(self):
        """Search proceeds (404 for missing gap) when enabled."""
        with patch.dict(os.environ, {"GITHUB_DISCOVERY_ENABLED": "true"}):
            resp = client.post("/api/github/search", params={"gap_id": "nonexistent"})
        # 404 means it passed the gate and tried to find the gap
        assert resp.status_code == 404


class TestOwnerRepoValidation:
    """Input validation for owner and repo_name."""

    def test_invalid_owner_rejected(self):
        """Owner with special chars returns 422."""
        with patch.dict(os.environ, {"GITHUB_DISCOVERY_ENABLED": "true"}):
            resp = client.post(
                "/api/github/harvest-candidate",
                params={"gap_id": "g", "owner": "../etc", "repo_name": "repo"},
            )
        assert resp.status_code == 422
        assert "owner" in resp.json()["detail"].lower()

    def test_invalid_repo_name_rejected(self):
        """Repo name with path traversal returns 422."""
        with patch.dict(os.environ, {"GITHUB_DISCOVERY_ENABLED": "true"}):
            resp = client.post(
                "/api/github/harvest-candidate",
                params={"gap_id": "g", "owner": "valid", "repo_name": "../../bad"},
            )
        assert resp.status_code == 422
        assert "repo_name" in resp.json()["detail"].lower()

    def test_valid_owner_repo_accepted(self):
        """Valid owner/repo passes validation (404 for missing gap)."""
        with patch.dict(os.environ, {"GITHUB_DISCOVERY_ENABLED": "true"}):
            resp = client.post(
                "/api/github/harvest-candidate",
                params={"gap_id": "g", "owner": "valid-owner", "repo_name": "my.repo_1"},
            )
        # 404 means it passed validation and tried to find the gap
        assert resp.status_code == 404


class TestCloneUrlAllowlist:
    """repo_intake only allows https://github.com/ clone URLs."""

    def test_non_github_url_rejected(self):
        from app.discovery.repo_intake import clone_or_pull

        with patch("app.discovery.repo_intake.subprocess.run") as mock_run:
            result = clone_or_pull("owner", "repo", "https://evil.com/owner/repo.git")

        assert result is None
        mock_run.assert_not_called()

    def test_github_url_accepted(self):
        from app.discovery.repo_intake import clone_or_pull

        with patch("app.discovery.repo_intake.subprocess.run"):
            result = clone_or_pull("owner", "repo", "https://github.com/owner/repo.git")

        # Returns a Path (not None) — the clone was attempted
        assert result is not None

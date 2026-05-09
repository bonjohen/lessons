"""Tests for repo config parsing and validation."""

import tempfile
from pathlib import Path

import yaml
import pytest


def write_repos_yml(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "repos.yml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


def validate_repo_entry(repo: dict) -> list[str]:
    """Simplified repo validation matching harvester logic."""
    import re
    errors = []
    required = {"id", "name", "owner", "repo", "branch", "lessons_path"}
    missing = required - set(repo.keys())
    if missing:
        errors.append(f"missing fields: {missing}")
    rid = repo.get("id", "")
    if rid and not re.match(r"^[a-z0-9][a-z0-9-]*$", rid):
        errors.append(f"invalid ID format: {rid}")
    return errors


class TestRepoConfig:
    def test_valid_config(self):
        repo = {
            "id": "my-project",
            "name": "My Project",
            "owner": "user",
            "repo": "my-project",
            "branch": "main",
            "lessons_path": "docs/lessons",
        }
        assert validate_repo_entry(repo) == []

    def test_duplicate_repo_id(self):
        repos = [
            {"id": "proj", "name": "P1", "owner": "u", "repo": "p1", "branch": "main", "lessons_path": "docs/lessons"},
            {"id": "proj", "name": "P2", "owner": "u", "repo": "p2", "branch": "main", "lessons_path": "docs/lessons"},
        ]
        seen = set()
        dupes = []
        for r in repos:
            if r["id"] in seen:
                dupes.append(r["id"])
            seen.add(r["id"])
        assert dupes == ["proj"]

    def test_missing_required_field(self):
        repo = {
            "id": "test",
            "name": "Test",
            # missing owner, repo, branch, lessons_path
        }
        errors = validate_repo_entry(repo)
        assert len(errors) == 1
        assert "missing fields" in errors[0]

    def test_invalid_id_format(self):
        repo = {
            "id": "Bad_ID",
            "name": "Test",
            "owner": "u",
            "repo": "r",
            "branch": "main",
            "lessons_path": "docs/lessons",
        }
        errors = validate_repo_entry(repo)
        assert any("invalid ID format" in e for e in errors)

    def test_valid_id_formats(self):
        for rid in ["myproject", "my-project", "project123", "a"]:
            repo = {
                "id": rid, "name": "T", "owner": "u", "repo": "r",
                "branch": "main", "lessons_path": "docs/lessons",
            }
            assert validate_repo_entry(repo) == [], f"ID '{rid}' should be valid"

    def test_repos_yml_structure(self, tmp_path):
        data = {"repos": [
            {"id": "test", "name": "Test", "owner": "u", "repo": "r", "branch": "main", "lessons_path": "docs/lessons"},
        ]}
        p = write_repos_yml(tmp_path, data)
        loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert "repos" in loaded
        assert isinstance(loaded["repos"], list)
        assert len(loaded["repos"]) == 1

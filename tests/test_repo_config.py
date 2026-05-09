"""Tests for repo config parsing and validation."""

from pathlib import Path

import yaml
import pytest

from lesson_core import validate_repo_entry, find_duplicate_ids


def _make_repo(**overrides) -> dict:
    base = {
        "id": "my-project",
        "name": "My Project",
        "owner": "user",
        "repo": "my-project",
        "branch": "main",
        "lessons_path": "docs/lessons",
    }
    base.update(overrides)
    return base


class TestRepoConfig:
    def test_valid_config(self):
        assert validate_repo_entry(_make_repo()) == []

    def test_duplicate_repo_id(self):
        repos = [_make_repo(id="proj"), _make_repo(id="proj")]
        assert find_duplicate_ids(repos) == ["proj"]

    def test_no_duplicates(self):
        repos = [_make_repo(id="a"), _make_repo(id="b")]
        assert find_duplicate_ids(repos) == []

    def test_missing_required_field(self):
        repo = {"id": "test", "name": "Test"}
        errors = validate_repo_entry(repo)
        assert len(errors) == 1
        assert "missing fields" in errors[0]

    def test_invalid_id_format(self):
        errors = validate_repo_entry(_make_repo(id="Bad_ID"))
        assert any("invalid ID format" in e for e in errors)

    def test_valid_id_formats(self):
        for rid in ["myproject", "my-project", "project123", "a"]:
            assert validate_repo_entry(_make_repo(id=rid)) == [], f"ID '{rid}' should be valid"

    def test_non_dict_entry(self):
        errors = validate_repo_entry("not-a-dict")
        assert any("not a dict" in e for e in errors)

    def test_repos_yml_structure(self, tmp_path):
        data = {"repos": [_make_repo()]}
        p = tmp_path / "repos.yml"
        p.write_text(yaml.dump(data), encoding="utf-8")
        loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert "repos" in loaded
        assert isinstance(loaded["repos"], list)
        assert len(loaded["repos"]) == 1

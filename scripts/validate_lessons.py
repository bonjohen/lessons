#!/usr/bin/env python3
"""Validate harvested lesson data against PDR requirements."""

import json
import sys
from pathlib import Path

import yaml

from lesson_core import (
    REQUIRED_REPO_FIELDS,
    REPO_ID_PATTERN,
    validate_repo_entry,
    find_duplicate_ids,
    validate_lesson_record,
)

ROOT = Path(__file__).resolve().parent.parent
REPOS_YML = ROOT / "data" / "repos.yml"
GENERATED_DIR = ROOT / "src" / "content" / "generated"

error_count = 0
warning_count = 0
info_count = 0


def log_error(msg: str) -> None:
    global error_count
    error_count += 1
    print(f"  ERROR: {msg}", file=sys.stderr)


def log_warning(msg: str) -> None:
    global warning_count
    warning_count += 1
    print(f"  WARNING: {msg}", file=sys.stderr)


def log_info(msg: str) -> None:
    global info_count
    info_count += 1
    print(f"  INFO: {msg}", file=sys.stderr)


def load_json(filename: str) -> list | None:
    path = GENERATED_DIR / filename
    if not path.exists():
        log_error(f"Required generated file missing: {filename}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            log_error(f"Generated file must be a JSON array: {filename}")
            return None
        return data
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in {filename}: {e}")
        return None


def validate_repos_yml() -> bool:
    """Validate the repo registry file."""
    if not REPOS_YML.exists():
        log_error(f"Missing {REPOS_YML}")
        return False

    try:
        with open(REPOS_YML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        log_error(f"Invalid YAML in repos.yml: {e}")
        return False

    if not isinstance(data, dict) or "repos" not in data:
        log_error("repos.yml must contain a top-level 'repos' list")
        return False

    repos = data["repos"]
    if not isinstance(repos, list):
        log_error("repos.yml 'repos' must be a list")
        return False

    for repo in repos:
        entry_errors = validate_repo_entry(repo)
        for msg in entry_errors:
            log_error(f"Repo '{repo.get('id', '?') if isinstance(repo, dict) else '?'}': {msg}")

    dupes = find_duplicate_ids(repos if all(isinstance(r, dict) for r in repos) else [r for r in repos if isinstance(r, dict)])
    for dup in dupes:
        log_error(f"Duplicate repo ID: {dup}")

    return True


def validate_lessons(lessons: list) -> None:
    """Validate lesson records."""
    dupes = find_duplicate_ids(lessons)
    for dup in dupes:
        log_error(f"Duplicate lesson ID: {dup}")

    for lesson in lessons:
        errs, warns = validate_lesson_record(lesson)
        for msg in errs:
            log_error(msg)
        for msg in warns:
            log_warning(msg)


def main() -> int:
    print("Lessons Hub Validator")
    print("=" * 40)

    # Validate repos.yml
    print("\nValidating repos.yml...")
    validate_repos_yml()

    # Check required generated files exist and are valid JSON
    print("\nValidating generated files...")
    lessons = load_json("lessons.json")
    repos = load_json("repos.json")
    load_json("tags.json")
    load_json("phases.json")
    load_json("lesson_types.json")

    # Validate lesson records
    if lessons is not None:
        print(f"\nValidating {len(lessons)} lesson(s)...")
        validate_lessons(lessons)

    if repos is not None:
        log_info(f"{len(repos)} repo(s) in repos.json")

    # Summary
    print("\n" + "=" * 40)
    print("Validation Summary")
    print(f"  Errors:   {error_count}")
    print(f"  Warnings: {warning_count}")
    print(f"  Info:     {info_count}")
    print("=" * 40)

    if error_count > 0:
        print("\nFAILED: validation errors found.")
        return 1

    print("\nPASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate harvested lesson data against PDR requirements."""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REPOS_YML = ROOT / "data" / "repos.yml"
GENERATED_DIR = ROOT / "src" / "content" / "generated"

REQUIRED_GENERATED_FILES = [
    "lessons.json",
    "repos.json",
    "tags.json",
    "phases.json",
    "lesson_types.json",
]

REQUIRED_REPO_FIELDS = {"id", "name", "owner", "repo", "branch", "lessons_path"}

VALID_LESSON_TYPES = {
    "architecture", "implementation", "testing", "deployment", "debugging",
    "data-design", "ai-assisted-development", "documentation", "maintenance",
    "process", "other",
}

VALID_STATUSES = {"active", "superseded", "draft", "deprecated"}

error_count = 0
warning_count = 0
info_count = 0


def log_error(msg: str) -> None:
    global error_count
    error_count += 1
    print(f"  ERROR: {msg}")


def log_warning(msg: str) -> None:
    global warning_count
    warning_count += 1
    print(f"  WARNING: {msg}")


def log_info(msg: str) -> None:
    global info_count
    info_count += 1
    print(f"  INFO: {msg}")


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

    seen_ids = set()
    for repo in repos:
        if not isinstance(repo, dict):
            log_error(f"Invalid repo entry: {repo}")
            continue

        missing = REQUIRED_REPO_FIELDS - set(repo.keys())
        if missing:
            log_error(f"Repo '{repo.get('id', '?')}' missing fields: {missing}")

        rid = repo.get("id", "")
        if rid and not re.match(r"^[a-z0-9][a-z0-9-]*$", rid):
            log_error(f"Invalid repo ID format: {rid}")

        if rid in seen_ids:
            log_error(f"Duplicate repo ID: {rid}")
        elif rid:
            seen_ids.add(rid)

    return True


def validate_lessons(lessons: list) -> None:
    """Validate lesson records."""
    seen_ids = set()

    for lesson in lessons:
        lid = lesson.get("id", "")

        # Hard errors
        if lid in seen_ids:
            log_error(f"Duplicate lesson ID: {lid}")
        elif lid:
            seen_ids.add(lid)

        if not lesson.get("content", "").strip():
            log_error(f"Empty lesson content: {lid}")

        if not lesson.get("title"):
            log_error(f"Missing title: {lid}")

        # Warnings for missing recommended fields
        if not lesson.get("summary"):
            log_warning(f"Missing summary: {lid}")

        if not lesson.get("date"):
            log_warning(f"Missing date: {lid}")

        if not lesson.get("tags"):
            log_warning(f"Missing tags: {lid}")

        if not lesson.get("phase"):
            log_warning(f"Missing phase: {lid}")

        lt = lesson.get("lesson_type")
        if not lt:
            log_warning(f"Missing lesson_type: {lid}")
        elif lt not in VALID_LESSON_TYPES:
            log_warning(f"Unknown lesson_type '{lt}': {lid}")

        status = lesson.get("status")
        if status and status not in VALID_STATUSES:
            log_warning(f"Unknown status '{status}': {lid}")

        # Tag normalization check
        for tag in lesson.get("tags", []):
            if tag != tag.lower() or " " in tag:
                log_warning(f"Non-normalized tag '{tag}': {lid}")

        # Short content
        wc = lesson.get("word_count", 0)
        if 0 < wc < 50:
            log_warning(f"Short content ({wc} words): {lid}")


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

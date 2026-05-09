"""Shared pure functions for harvesting and validating lessons.

This module contains all logic that can be tested without side effects:
tag normalization, slug generation, title extraction, field validation,
and controlled vocabulary definitions.
"""

import re
from datetime import datetime
from pathlib import Path

import frontmatter
from slugify import slugify

# --- Controlled vocabularies ---

REQUIRED_REPO_FIELDS = {"id", "name", "owner", "repo", "branch", "lessons_path"}

VALID_LESSON_TYPES = {
    "architecture", "implementation", "testing", "deployment", "debugging",
    "data-design", "ai-assisted-development", "documentation", "maintenance",
    "process", "other",
}

VALID_STATUSES = {"active", "superseded", "draft", "deprecated"}

REPO_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

MIN_CONTENT_WORDS = 50
READING_WPM = 200


# --- Tag normalization ---

def normalize_tags(tags) -> list[str]:
    """Normalize tags: lowercase, trim, hyphens for spaces, dedup.

    Accepts None, a list of strings, or a comma-separated string.
    Non-string elements are coerced to str.
    """
    if not tags:
        return []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    seen = set()
    result = []
    for tag in tags:
        if not isinstance(tag, str):
            tag = str(tag)
        normalized = slugify(tag.strip())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


# --- Slug generation ---

def make_slug(post: frontmatter.Post, filepath: Path, lessons_root: Path) -> str:
    """Generate slug from frontmatter slug, or path relative to lessons root.

    When lessons live in subdirectories (e.g. block1/index.md, block2/index.md),
    the subdirectory is included in the slug to avoid collisions.
    """
    if post.get("slug"):
        return slugify(post["slug"])
    try:
        rel = filepath.relative_to(lessons_root).with_suffix("")
        parts = rel.parts
        return slugify("-".join(parts))
    except ValueError:
        return slugify(filepath.stem)


# --- Title extraction ---

def extract_title(post: frontmatter.Post, filepath: Path) -> tuple[str, bool]:
    """Extract title from frontmatter, first H1, or filename.

    Returns (title, inferred) where inferred=True means it came from the filename.
    """
    if post.get("title"):
        title = post["title"]
        if isinstance(title, list):
            title = title[0] if title else ""
        return str(title), False

    for line in post.content.split("\n"):
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip(), False

    title = filepath.stem.replace("-", " ").replace("_", " ").title()
    return title, True


# --- Repo config validation ---

def validate_repo_entry(repo: dict) -> list[str]:
    """Validate a single repo config entry. Returns list of error strings."""
    errors = []

    if not isinstance(repo, dict):
        return [f"Invalid repo entry (not a dict): {repo}"]

    missing = REQUIRED_REPO_FIELDS - set(repo.keys())
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")

    rid = repo.get("id", "")
    if rid and not REPO_ID_PATTERN.match(rid):
        errors.append(f"invalid ID format: {rid}")

    return errors


def find_duplicate_ids(items: list[dict], key: str = "id") -> list[str]:
    """Find duplicate values for a given key in a list of dicts."""
    seen = set()
    dupes = []
    for item in items:
        val = item.get(key, "")
        if val in seen:
            dupes.append(val)
        elif val:
            seen.add(val)
    return dupes


# --- Lesson record validation ---

def validate_lesson_record(lesson: dict) -> tuple[list[str], list[str]]:
    """Validate a single lesson record.

    Returns (errors, warnings) as lists of message strings.
    """
    errors = []
    warnings = []
    lid = lesson.get("id", "<no-id>")

    # Hard errors
    if not lesson.get("content", "").strip():
        errors.append(f"Empty lesson content: {lid}")

    if not lesson.get("title"):
        errors.append(f"Missing title: {lid}")

    # Warnings for missing recommended fields
    if not lesson.get("summary"):
        warnings.append(f"Missing summary: {lid}")

    if not lesson.get("date"):
        warnings.append(f"Missing date: {lid}")

    if not lesson.get("tags"):
        warnings.append(f"Missing tags: {lid}")

    if not lesson.get("phase"):
        warnings.append(f"Missing phase: {lid}")

    lt = lesson.get("lesson_type")
    if not lt:
        warnings.append(f"Missing lesson_type: {lid}")
    elif lt not in VALID_LESSON_TYPES:
        warnings.append(f"Unknown lesson_type '{lt}': {lid}")

    status = lesson.get("status")
    if status and status not in VALID_STATUSES:
        warnings.append(f"Unknown status '{status}': {lid}")

    # Tag normalization check
    for tag in lesson.get("tags", []):
        if tag != tag.lower() or " " in tag:
            warnings.append(f"Non-normalized tag '{tag}': {lid}")

    # Short content
    wc = lesson.get("word_count", 0)
    if 0 < wc < MIN_CONTENT_WORDS:
        warnings.append(f"Short content ({wc} words): {lid}")

    return errors, warnings


# --- Lesson parsing helpers ---

def coerce_date(val) -> str | None:
    """Convert a date value to ISO string or None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    return str(val)


def build_source_url(repo: dict, rel_path) -> str:
    """Build the GitHub source URL for a lesson file."""
    return (
        f"https://github.com/{repo['owner']}/{repo['repo']}"
        f"/blob/{repo['branch']}/{repo['lessons_path']}/{rel_path}"
    )


def compute_reading_time(word_count: int) -> int:
    """Compute reading time in minutes from word count."""
    return max(1, round(word_count / READING_WPM))

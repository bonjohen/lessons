"""Shared pure functions for harvesting and validating lessons.

This module contains all logic that can be tested without side effects:
tag normalization, slug generation, title extraction, field validation,
controlled vocabulary definitions, and shared logging.
"""

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import frontmatter
from slugify import slugify

# --- Controlled vocabularies ---

REQUIRED_REPO_FIELDS = {"id", "name", "owner", "repo", "branch", "lessons_path"}

VALID_LESSON_TYPES = {
    "architecture",
    "implementation",
    "testing",
    "deployment",
    "debugging",
    "data-design",
    "ai-assisted-development",
    "documentation",
    "maintenance",
    "process",
    "other",
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


def infer_summary(content: str) -> str:
    """Extract summary from '## The Lesson' section, or first non-heading paragraph."""
    # Try "## The Lesson" section first
    m = re.search(
        r"^##\s+The\s+Lesson\s*\n+(.*?)(?=\n##\s|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if m:
        text = m.group(1).strip()
        # Take first paragraph only
        text = text.split("\n\n")[0].replace("\n", " ").strip()
        if len(text) > 20:
            return text[:300].rstrip() + ("..." if len(text) > 300 else "")

    # Fallback: first non-heading, non-empty paragraph
    for para in re.split(r"\n{2,}", content):
        para = para.strip()
        if para and not para.startswith("#"):
            text = para.replace("\n", " ").strip()
            if len(text) > 20:
                return text[:300].rstrip() + ("..." if len(text) > 300 else "")
    return ""


# Tag inference keyword map: tag -> list of patterns to match in content
_TAG_KEYWORDS: list[tuple[str, list[str]]] = [
    ("cloudflare", [r"\bcloudflare\b", r"\bworkers?\b.*\bcloudflare\b"]),
    ("serverless", [r"\bserverless\b", r"\bcloudflare workers?\b", r"\blambda\b"]),
    ("database", [r"\bsqlite\b", r"\bpostgres", r"\bdatabase\b", r"\bsql\b"]),
    ("authentication", [r"\boauth\b", r"\bauth\b.*\bflow\b", r"\blogin\b"]),
    ("security", [r"\bxss\b", r"\bcsp\b", r"\bsecurity\b", r"\binjection\b"]),
    ("testing", [r"\btest(s|ing)?\b.*\b(suite|framework|pass|fail)\b"]),
    ("deployment", [r"\bdeploy(ment|ing|ed)?\b", r"\bci/cd\b", r"\bgithub actions\b"]),
    ("api", [r"\brest\s*api\b", r"\bapi\s+(endpoint|route|call)\b"]),
    ("pdf", [r"\bpdf\b.*\bgenerat", r"\bjspdf\b"]),
    ("sms", [r"\btwilio\b", r"\bsms\b", r"\bverif(y|ication)\b.*\bphone\b"]),
    ("frontend", [r"\bclient.side\b", r"\bbrowser\b.*\b(render|generat)"]),
    ("data-modeling", [r"\bschema\b", r"\bmigration\b", r"\bdata\s*model\b"]),
    ("devops", [r"\bwrangler\b", r"\bcli\b.*\bdeploy\b"]),
    ("pipeline", [r"\bpipeline\b", r"\bharvest\b", r"\betl\b"]),
    ("python", [r"\bpython\b", r"\bpytest\b", r"\bfastapi\b"]),
    ("javascript", [r"\bjavascript\b", r"\bnode\.?js\b", r"\btypescript\b"]),
    ("astro", [r"\bastro\b"]),
    ("docker", [r"\bdocker\b", r"\bcontainer\b"]),
    ("cloud", [r"\baws\b", r"\bazure\b", r"\bgcp\b", r"\bbedrock\b"]),
    ("ai", [r"\bllm\b", r"\brag\b", r"\bembedding\b", r"\bmachine learning\b"]),
    ("git", [r"\bgit\s+(push|pull|commit|branch|rebase)\b"]),
    ("statistics", [r"\bbayesian\b", r"\bchi.squared\b", r"\bborda\b", r"\bkrippendorff\b", r"\belo\s+rating\b", r"\bbradley.terry\b", r"\bscoring\b.*\b(composite|heterogeneous)\b", r"\bbaseline\b", r"\bbias\s+detect", r"\bheuristic\b.*\bscor"]),
    ("architecture", [r"\bstate\s+machine\b", r"\bpermission\b.*\b(union|role)\b", r"\barchitect\b"]),
    ("ui", [r"\bdrag.and.drop\b", r"\binteraction\b.*\b(pattern|design)\b", r"\bui\s+state\b"]),
]


def infer_tags(title: str, content: str, max_tags: int = 5) -> list[str]:
    """Infer tags from title and content using keyword matching."""
    text = (title + "\n" + content).lower()
    matched: list[str] = []
    for tag, patterns in _TAG_KEYWORDS:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched.append(tag)
                break
        if len(matched) >= max_tags:
            break
    return matched


def infer_date_from_file(filepath: "Path") -> str | None:
    """Infer date from git last-commit time, falling back to file mtime."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", "--", str(filepath.name)],
            cwd=str(filepath.parent),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split(" ")[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        mtime = filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
        return None


def build_source_url(repo: dict, rel_path) -> str:
    """Build the GitHub source URL for a lesson file."""
    return (
        f"https://github.com/{repo['owner']}/{repo['repo']}"
        f"/blob/{repo['branch']}/{repo['lessons_path']}/{rel_path}"
    )


def compute_reading_time(word_count: int) -> int:
    """Compute reading time in minutes from word count."""
    return max(1, round(word_count / READING_WPM))


# --- Shared logging ---


@dataclass
class LogStats:
    """Tracks counts for structured log output."""

    errors: int = 0
    warnings: int = 0
    infos: int = 0
    messages: list[str] = field(default_factory=list)


_log_stats = LogStats()


def log_error(msg: str) -> None:
    """Log an error to stderr and track the count."""
    _log_stats.errors += 1
    _log_stats.messages.append(f"[ERROR] {msg}")
    print(f"  [ERROR] {msg}", file=sys.stderr)


def log_warning(msg: str) -> None:
    """Log a warning to stderr and track the count."""
    _log_stats.warnings += 1
    _log_stats.messages.append(f"[WARNING] {msg}")
    print(f"  [WARNING] {msg}", file=sys.stderr)


def log_info(msg: str) -> None:
    """Log an info message to stderr and track the count."""
    _log_stats.infos += 1
    _log_stats.messages.append(f"[INFO] {msg}")
    print(f"  [INFO] {msg}", file=sys.stderr)


def get_log_stats() -> LogStats:
    """Return the current log stats."""
    return _log_stats


def reset_log_stats() -> None:
    """Reset all log counters and messages."""
    _log_stats.errors = 0
    _log_stats.warnings = 0
    _log_stats.infos = 0
    _log_stats.messages.clear()

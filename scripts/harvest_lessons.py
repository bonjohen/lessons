#!/usr/bin/env python3
"""Harvest lessons from source repositories defined in data/repos.yml."""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import frontmatter
import yaml

from lesson_core import (
    REQUIRED_REPO_FIELDS,
    REPO_ID_PATTERN,
    normalize_tags,
    make_slug,
    extract_title,
    coerce_date,
    build_source_url,
    compute_reading_time,
    get_log_stats,
    log_error,
    log_warning,
    reset_log_stats,
)

ROOT = Path(__file__).resolve().parent.parent
REPOS_YML = ROOT / "data" / "repos.yml"
TMP_DIR = ROOT / "tmp" / "repos"
GENERATED_DIR = ROOT / "src" / "content" / "generated"
EXPORTS_DIR = ROOT / "public" / "exports"


# Rules checked against title only (high confidence)
_TITLE_RULES: list[tuple[str, list[str]]] = [
    (
        "deployment",
        [
            r"\bdeploy",
            r"\bci[/-]cd\b",
            r"\bgithub actions\b",
            r"\bdocker\b",
            r"\bcontainer\b",
            r"\boidc\b",
            r"\brelease artifact",
            r"\bci\b.*\bportab",
        ],
    ),
    (
        "security",
        [
            r"\bcsp\b",
            r"\bxss\b",
            r"\bpii\b",
            r"\bsanitiz",
            r"\binjection\b",
            r"\bentity encod",
        ],
    ),
    (
        "data-engineering",
        [
            r"\bduckdb\b",
            r"\betl\b",
            r"\bmigration\b",
            r"\bdata quality\b",
            r"\bpyarrow\b",
            r"\bsurrogate key\b",
            r"\bidempotent\b",
            r"\bvintage\b",
            r"\bbatch\b.*\b(?:db|insert|operat)",
            r"\bpipeline\b",
        ],
    ),
    (
        "algorithms",
        [
            r"\balgorithm\b",
            r"\bbayesian\b",
            r"\belo\b",
            r"\bchi-squared\b",
            r"\bmmr\b",
            r"\bhungarian\b",
            r"\bcluster(?:ing)?\b",
            r"\bembedding\b",
            r"\bsimilarity\b",
            r"\bk-means\b",
            r"\bborda\b",
            r"\bbradley-terry\b",
            r"\bkrippendorff",
            r"\bsigmoid\b",
            r"\bcalibrat",
            r"\bscoring\b",
            r"\bdiversity.(?:aware|select)",
            r"\bdedup(?:licat)?",
        ],
    ),
    (
        "testing",
        [
            r"\btest",
            r"\bvalidat",
            r"\bmock\b",
            r"\bfixture\b",
            r"\btdd\b",
            r"\bcoverage\b",
        ],
    ),
    (
        "architecture",
        [
            r"\badapter\b",
            r"\bdesign system\b",
            r"\bschema\b",
            r"\btaxonomy\b",
            r"\bprovider.agnostic\b",
            r"\blazy import",
            r"\bdimensional\b",
            r"\babstraction\b",
        ],
    ),
    (
        "process",
        [
            r"\bphased\b",
            r"\bplanning\b",
            r"\baudit\b",
            r"\blessons learned\b",
            r"\bdesign.first\b",
            r"\bremediat",
            r"\bcode review\b",
            r"\bautonomous execution\b",
        ],
    ),
    (
        "frontend",
        [
            r"\bspa\b",
            r"\bcss\b",
            r"\bjavascript\b",
            r"\bdrag.and.drop\b",
            r"\bdesign tokens?\b",
            r"\bstatic site\b",
            r"\bvanilla js\b",
            r"\blocalstorage\b",
            r"\bfetch shim\b",
        ],
    ),
]

# Fallback rules checked against full content (lower confidence, stricter patterns)
_CONTENT_RULES: list[tuple[str, list[str]]] = [
    (
        "deployment",
        [
            r"\bgithub actions\b",
            r"\bdocker(?:file)?\b",
            r"\bci[/-]cd\b",
        ],
    ),
    (
        "data-engineering",
        [
            r"\bduckdb\b",
            r"\bpyarrow\b",
            r"\b(?:bulk|batch) insert\b",
        ],
    ),
    (
        "algorithms",
        [
            r"## (?:the )?algorithm\b",
            r"\btime complexity\b",
            r"\bbig-?o\b",
        ],
    ),
    (
        "security",
        [
            r"\bcontent.security.policy\b",
            r"\bcross.site scripting\b",
        ],
    ),
    (
        "architecture",
        [
            r"\babstract base class\b",
            r"\badapter pattern\b",
        ],
    ),
    (
        "frontend",
        [
            r"\bdom\b.*\bmanipu",
            r"\bevent listener\b",
        ],
    ),
]


def infer_lesson_type(title: str, content: str) -> str | None:
    """Infer lesson_type from title and content keywords. Returns None only for
    index/meta files with no substantive teaching content."""
    title_lower = title.lower()
    # Title-based rules first (high confidence)
    for lesson_type, patterns in _TITLE_RULES:
        for pat in patterns:
            if re.search(pat, title_lower):
                return lesson_type
    # Content-based rules (stricter patterns)
    content_lower = content.lower()
    for lesson_type, patterns in _CONTENT_RULES:
        for pat in patterns:
            if re.search(pat, content_lower):
                return lesson_type
    # Default fallback for substantive lessons
    if len(content.split()) > 50:
        return "implementation"
    return None


def load_repos() -> list[dict]:
    """Load and validate data/repos.yml."""
    if not REPOS_YML.exists():
        log_error(f"Missing {REPOS_YML}")
        return []

    with open(REPOS_YML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "repos" not in data:
        log_error("repos.yml must contain a top-level 'repos' list")
        return []

    repos = data["repos"]
    if not isinstance(repos, list):
        log_error("repos.yml 'repos' must be a list")
        return []

    seen_ids = set()
    valid = []
    for repo in repos:
        if not isinstance(repo, dict):
            log_error(f"Invalid repo entry: {repo}")
            continue

        missing = REQUIRED_REPO_FIELDS - set(repo.keys())
        if missing:
            log_error(f"Repo entry missing fields {missing}: {repo.get('id', '?')}")
            continue

        rid = repo["id"]
        if not REPO_ID_PATTERN.match(rid):
            log_error(f"Invalid repo ID format: {rid}")
            continue

        if rid in seen_ids:
            log_error(f"Duplicate repo ID: {rid}")
            continue
        seen_ids.add(rid)

        if not repo.get("enabled", True):
            print(f"  Skipping disabled repo: {rid}")
            continue

        valid.append(repo)

    return valid


def clone_repo(repo: dict) -> Path | None:
    """Clone a repo to tmp/repos/{id}. Returns clone path or None on failure."""
    rid = repo["id"]
    dest = TMP_DIR / rid

    owner = repo["owner"]
    name = repo["repo"]
    branch = repo["branch"]

    token = os.environ.get("LESSONS_REPO_TOKEN")
    if token:
        url = f"https://x-access-token:{token}@github.com/{owner}/{name}.git"
    else:
        url = f"https://github.com/{owner}/{name}.git"

    # Never print the URL when token is present
    display_url = f"https://github.com/{owner}/{name}.git"
    print(f"  Cloning {rid} from {display_url} (branch: {branch})...")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, url, str(dest)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to clone {rid}: {e.stderr.strip()}")
        return None

    return dest


def parse_lesson(filepath: Path, repo: dict) -> dict | None:
    """Parse a single lesson markdown file into a normalized record."""
    rid = repo["id"]

    try:
        post = frontmatter.load(filepath)
    except Exception as e:
        log_error(f"Unreadable lesson file {filepath}: {e}")
        return None

    content = post.content.strip()
    if not content:
        log_error(f"Empty lesson content: {filepath}")
        return None

    title, inferred = extract_title(post, filepath)
    if inferred:
        log_warning(f"Title inferred from filename: {filepath.name} -> '{title}'")

    # Source path relative to lessons_path
    if repo.get("virtual"):
        lessons_root = ROOT / repo["lessons_path"]
    else:
        lessons_root = TMP_DIR / rid / repo["lessons_path"]

    lesson_slug = make_slug(post, filepath, lessons_root)
    lesson_id = f"{rid}-{lesson_slug}"
    try:
        rel_path = filepath.relative_to(lessons_root)
    except ValueError:
        rel_path = filepath.name

    source_url = build_source_url(repo, rel_path)
    project_url = repo.get(
        "project_url", f"https://github.com/{repo['owner']}/{repo['repo']}"
    )

    # Frontmatter fields — coerce list values to strings (malformed YAML)
    summary = post.get("summary", "")
    if isinstance(summary, list):
        summary = summary[0] if summary else ""
    date = coerce_date(post.get("date"))
    updated = coerce_date(post.get("updated"))
    phase = post.get("phase")
    if isinstance(phase, list):
        phase = phase[0] if phase else None
    lesson_type = post.get("lesson_type")
    if isinstance(lesson_type, list):
        lesson_type = lesson_type[0] if lesson_type else None
    if not lesson_type:
        lesson_type = infer_lesson_type(title, content)
    status = post.get("status", "active")
    if isinstance(status, list):
        status = status[0] if status else "active"
    tags = normalize_tags(post.get("tags", []))

    word_count = len(content.split())

    reading_minutes = compute_reading_time(word_count)

    return {
        "id": lesson_id,
        "title": title,
        "summary": summary or "",
        "repo_id": rid,
        "repo_name": repo["name"],
        "repo_owner": repo["owner"],
        "repo_slug": repo["repo"],
        "source_path": str(rel_path),
        "source_url": source_url,
        "project_url": project_url,
        "date": date,
        "updated": updated,
        "phase": phase,
        "lesson_type": lesson_type,
        "status": status or "active",
        "tags": tags,
        "source_files": post.get("source_files", []) or [],
        "related_prs": post.get("related_prs", []) or [],
        "related_issues": post.get("related_issues", []) or [],
        "related_commits": post.get("related_commits", []) or [],
        "audience": post.get("audience", []) or [],
        "original_source": post.get("original_source", ""),
        "content": content,
        "word_count": word_count,
        "reading_minutes": reading_minutes,
    }


def scan_lessons(repo: dict, clone_path: Path) -> list[dict]:
    """Scan all .md files in the lessons path (recursive)."""
    rid = repo["id"]
    lessons_dir = clone_path / repo["lessons_path"]

    if not lessons_dir.exists():
        log_error(f"Lessons path not found: {lessons_dir} (repo: {rid})")
        return []

    md_files = sorted(lessons_dir.rglob("*.md"))
    # Exclude README.md and TEMPLATE.md files
    md_files = [
        f for f in md_files if f.name.lower() not in ("readme.md", "template.md")
    ]

    if not md_files:
        log_warning(f"No lesson files found in {lessons_dir} (repo: {rid})")
        return []

    lessons = []
    for md_file in md_files:
        lesson = parse_lesson(md_file, repo)
        if lesson:
            lessons.append(lesson)

    return lessons


def check_duplicate_ids(lessons: list[dict]) -> None:
    """Check for duplicate lesson IDs."""
    seen = {}
    for lesson in lessons:
        lid = lesson["id"]
        if lid in seen:
            log_error(
                f"Duplicate lesson ID: {lid} (first in {seen[lid]}, also in {lesson['repo_id']})"
            )
        else:
            seen[lid] = lesson["repo_id"]


def generate_indexes(lessons: list[dict], repos: list[dict]) -> None:
    """Generate aggregate JSON indexes."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # lessons.json
    write_json(GENERATED_DIR / "lessons.json", lessons)

    # repos.json — repo metadata with lesson counts
    repo_index = []
    for repo in repos:
        rid = repo["id"]
        repo_lessons = [l for l in lessons if l["repo_id"] == rid]
        all_tags = set()
        for l in repo_lessons:
            all_tags.update(l["tags"])
        dates = [l["date"] for l in repo_lessons if l["date"]]
        repo_index.append(
            {
                "id": rid,
                "name": repo["name"],
                "owner": repo["owner"],
                "repo": repo["repo"],
                "branch": repo["branch"],
                "project_url": repo.get("project_url", ""),
                "description": repo.get("description", ""),
                "lesson_count": len(repo_lessons),
                "tags": sorted(all_tags),
                "recent_date": max(dates) if dates else None,
            }
        )
    write_json(GENERATED_DIR / "repos.json", repo_index)

    # tags.json — tag name + count + lesson IDs
    tag_map: dict[str, list[str]] = {}
    for l in lessons:
        for tag in l["tags"]:
            tag_map.setdefault(tag, []).append(l["id"])
    tags_index = sorted(
        [
            {"tag": t, "count": len(ids), "lesson_ids": sorted(ids)}
            for t, ids in tag_map.items()
        ],
        key=lambda x: (-x["count"], x["tag"]),
    )
    write_json(GENERATED_DIR / "tags.json", tags_index)

    # phases.json
    phase_map: dict[str, list[str]] = {}
    for l in lessons:
        p = l["phase"] or "unspecified"
        if isinstance(p, list):
            p = p[0] if p else "unspecified"
        phase_map.setdefault(p, []).append(l["id"])
    phases_index = sorted(
        [
            {"phase": p, "count": len(ids), "lesson_ids": sorted(ids)}
            for p, ids in phase_map.items()
        ],
        key=lambda x: (-x["count"], x["phase"]),
    )
    write_json(GENERATED_DIR / "phases.json", phases_index)

    # lesson_types.json
    type_map: dict[str, list[str]] = {}
    for l in lessons:
        t = l["lesson_type"] or "unspecified"
        if isinstance(t, list):
            t = t[0] if t else "unspecified"
        type_map.setdefault(t, []).append(l["id"])
    types_index = sorted(
        [
            {"lesson_type": t, "count": len(ids), "lesson_ids": sorted(ids)}
            for t, ids in type_map.items()
        ],
        key=lambda x: (-x["count"], x["lesson_type"]),
    )
    write_json(GENERATED_DIR / "lesson_types.json", types_index)


def generate_exports(lessons: list[dict]) -> None:
    """Generate AI-readable export files."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # lessons-pack.json — full records
    write_json(EXPORTS_DIR / "lessons-pack.json", lessons)

    # lessons-index.json — compact records
    index = [
        {
            "id": l["id"],
            "title": l["title"],
            "repo": l["repo_id"],
            "summary": l["summary"],
            "tags": l["tags"],
            "url": f"/lessons/{l['id']}",
        }
        for l in lessons
    ]
    write_json(EXPORTS_DIR / "lessons-index.json", index)

    # lessons-pack.md — all lessons in markdown
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Lessons Pack",
        "",
        f"Generated: {timestamp}",
        f"Total lessons: {len(lessons)}",
        "",
    ]

    # Group by repo
    by_repo: dict[str, list[dict]] = {}
    for l in lessons:
        by_repo.setdefault(l["repo_id"], []).append(l)

    for repo_id in sorted(by_repo):
        repo_lessons = by_repo[repo_id]
        lines.append(f"## {repo_lessons[0]['repo_name']} ({repo_id})")
        lines.append("")
        for l in sorted(repo_lessons, key=lambda x: x["title"]):
            lines.append(f"### {l['title']}")
            lines.append("")
            lines.append(f"- **ID:** {l['id']}")
            lines.append(f"- **Source:** {l['source_url']}")
            if l["tags"]:
                lines.append(f"- **Tags:** {', '.join(l['tags'])}")
            lines.append("")
            lines.append(l["content"])
            lines.append("")
            lines.append("---")
            lines.append("")

    (EXPORTS_DIR / "lessons-pack.md").write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, data) -> None:
    """Write deterministic JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    reset_log_stats()
    stats = get_log_stats()
    print("Lessons Hub Harvester")
    print("=" * 40)

    # Load repos
    repos = load_repos()
    if stats.errors:
        print(f"\nFATAL: {stats.errors} error(s) loading repos. Aborting.")
        return 1

    if not repos:
        print("\nNo enabled repos found.")
        return 0

    print(f"\n{len(repos)} enabled repo(s) to harvest.\n")

    # Clean and create tmp directory
    if TMP_DIR.exists():
        # On Windows, git clone creates read-only files that rmtree can't delete
        def on_rm_error(func, path, exc_info):
            os.chmod(path, 0o777)
            func(path)

        shutil.rmtree(TMP_DIR, onexc=on_rm_error)
    TMP_DIR.mkdir(parents=True)

    # Clone and scan
    all_lessons = []
    repos_scanned = 0
    for repo in repos:
        if repo.get("virtual"):
            clone_path = ROOT
            print(f"  Scanning local {repo['id']}...")
        else:
            clone_path = clone_repo(repo)
            if clone_path is None:
                continue
        repos_scanned += 1
        lessons = scan_lessons(repo, clone_path)
        all_lessons.extend(lessons)
        print(f"  Found {len(lessons)} lesson(s) in {repo['id']}")

    if stats.errors:
        print(f"\nFATAL: {stats.errors} error(s) during harvest. Aborting.")
        return 1

    # Check duplicate IDs
    check_duplicate_ids(all_lessons)
    if stats.errors:
        print(f"\nFATAL: {stats.errors} error(s) — duplicate IDs. Aborting.")
        return 1

    # Generate outputs
    print("\nGenerating indexes...")
    generate_indexes(all_lessons, repos)

    print("Generating export packs...")
    generate_exports(all_lessons)

    # Summary
    print("\n" + "=" * 40)
    print("Harvest Summary")
    print(f"  Repos scanned:  {repos_scanned}")
    print(f"  Lessons found:  {len(all_lessons)}")
    print(f"  Warnings:       {stats.warnings}")
    print(f"  Errors:         {stats.errors}")
    print("=" * 40)

    return 0


if __name__ == "__main__":
    sys.exit(main())

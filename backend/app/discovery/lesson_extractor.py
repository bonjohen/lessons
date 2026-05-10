"""Lesson extractor — generate candidate lessons from external repos."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CANDIDATE_LESSONS_DIR = PROJECT_ROOT / "docs" / "candidate-lessons" / "external"

# File patterns that suggest extractable content
DOC_PATTERNS = ["*.md", "*.rst", "*.txt"]
CI_PATTERNS = [".github/workflows/*.yml", ".github/workflows/*.yaml"]
DEPLOY_PATTERNS = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "*.tf", "deploy.sh"]
ARCH_PATTERNS = ["docs/adr/*.md", "docs/architecture*.md", "ARCHITECTURE.md", "ADR*.md"]

ATTRIBUTION_TEMPLATE = dedent("""\
## Attribution and Thanks

**Source Project:** [{owner}/{repo_name}]({github_url})
**Source Link:** {github_url}

This candidate lesson was generated from publicly available project material.
Thank you to the maintainers of {owner}/{repo_name} for making their work available.
This lesson should not be proposed back to the source project until it has been
reviewed and the owner/maintainer coordination TODO has been completed.
""")

# Categories and what they indicate about the project
_CATEGORY_DESCRIPTIONS = {
    "docs": "documentation",
    "ci": "CI/CD workflows",
    "deploy": "deployment configuration",
    "architecture": "architecture decisions",
}


def detect_extractable_content(repo_dir: Path) -> dict:
    """Detect documentation, CI, deployment, and architecture files."""
    found = {"docs": [], "ci": [], "deploy": [], "architecture": []}

    for pattern in DOC_PATTERNS:
        found["docs"].extend(sorted(repo_dir.rglob(pattern))[:20])
    for pattern in CI_PATTERNS:
        found["ci"].extend(sorted(repo_dir.glob(pattern)))
    for name in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]:
        if (repo_dir / name).exists():
            found["deploy"].append(repo_dir / name)
    for pattern in ARCH_PATTERNS:
        found["architecture"].extend(sorted(repo_dir.glob(pattern)))

    return found


def _summarize_sources(repo_dir: Path, content_files: dict) -> list[tuple[Path, str]]:
    """Extract a 1–3 sentence summary from each evidence file.

    Returns a list of (file_path, summary) tuples.
    """
    summaries: list[tuple[Path, str]] = []

    for category, files in content_files.items():
        desc = _CATEGORY_DESCRIPTIONS.get(category, category)
        for f in files[:5]:  # Cap per category
            try:
                text = f.read_text(encoding="utf-8", errors="replace")[:3000]
            except OSError:
                continue

            # Extract a meaningful summary based on file type
            name = f.name.lower()
            if name == "readme.md":
                # First non-empty paragraph after the title
                lines = text.split("\n")
                para = []
                past_title = False
                for line in lines:
                    if line.startswith("# ") and not past_title:
                        past_title = True
                        continue
                    if past_title and line.strip():
                        para.append(line.strip())
                        if len(para) >= 3:
                            break
                    elif past_title and para:
                        break
                summary = " ".join(para) if para else f"Project README ({desc})."
            elif name in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                summary = f"Provides {desc} for containerized deployment."
            elif name.endswith((".yml", ".yaml")) and category == "ci":
                summary = f"GitHub Actions workflow for {desc}."
            elif name.endswith(".tf"):
                summary = "Terraform configuration for infrastructure provisioning."
            else:
                # Generic: first non-blank line
                first = next(
                    (line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#")),
                    f"Contains {desc}.",
                )
                summary = first[:200]

            summaries.append((f, summary))

    return summaries


def _draft_lesson(topic: str, missing_concepts: list[str], summaries: list[tuple[Path, str]]) -> str:
    """Combine source summaries into a cohesive lesson body paragraph."""
    if not summaries:
        return (
            f"The project demonstrates practices related to {topic} that may be valuable "
            f"for the lessons corpus. Further human analysis is needed to extract specific lessons."
        )

    concept_str = ", ".join(missing_concepts[:5]) if missing_concepts else topic
    intro = (
        f"This project offers insights into **{topic}**, specifically addressing "
        f"gaps in the corpus around: {concept_str}.\n\n"
    )

    points = []
    for _, summary in summaries[:6]:
        points.append(f"- {summary}")

    body = (
        f"Based on analysis of {len(summaries)} source file(s), the project demonstrates:\n\n"
        + "\n".join(points)
        + "\n\n"
        + "These practices should be reviewed and expanded into a full lesson narrative "
        + "by someone familiar with the domain."
    )

    return intro + body


def _build_evidence_links(
    repo_dir: Path,
    owner: str,
    repo_name: str,
    summaries: list[tuple[Path, str]],
    branch: str = "main",
) -> str:
    """Generate markdown evidence links pointing to GitHub blob URLs."""
    if not summaries:
        return "No specific evidence files detected."

    lines = []
    for f, summary in summaries:
        try:
            rel = f.relative_to(repo_dir)
        except ValueError:
            continue
        # Use forward slashes for URL
        rel_str = str(rel).replace("\\", "/")
        blob_url = f"https://github.com/{owner}/{repo_name}/blob/{branch}/{rel_str}"
        lines.append(f"- [`{rel_str}`]({blob_url}) — {summary}")

    return "\n".join(lines) if lines else "No specific evidence files detected."


def _build_review_checklist() -> str:
    """Build a standardized review checklist."""
    return dedent("""\
    ## Review Checklist

    - [ ] Lesson accurately reflects source project
    - [ ] Attribution is correct
    - [ ] No proprietary content copied
    - [ ] Ready to propose to source project owner
    """)


def generate_candidate_lesson(
    repo_dir: Path,
    candidate: dict,
    gap: dict,
    content_files: dict,
) -> Path | None:
    """Generate a candidate lesson markdown file.

    Returns the path to the generated lesson, or None if extraction fails.
    """
    owner = candidate["owner"]
    repo_name = candidate["repo_name"]
    github_url = candidate["github_url"]
    topic = gap.get("normalized_topic", "unknown topic")
    missing_concepts = gap.get("missing_concepts", [])
    slug = topic.replace(" ", "-")[:50]

    # Multi-stage pipeline
    summaries = _summarize_sources(repo_dir, content_files)
    lesson_body = _draft_lesson(topic, missing_concepts, summaries)
    evidence_section = _build_evidence_links(repo_dir, owner, repo_name, summaries)
    review_checklist = _build_review_checklist()

    # Build frontmatter
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frontmatter = dedent(f"""\
    ---
    title: "Lessons from {owner}/{repo_name}: {topic}"
    summary: "Candidate lesson extracted from {owner}/{repo_name} related to {topic}"
    date: {today}
    phase: discovery
    lesson_type: other
    status: candidate_external
    tags: [{", ".join(missing_concepts[:5])}]
    source_project: "{owner}/{repo_name}"
    source_project_url: "{github_url}"
    source_owner: "{owner}"
    source_repo: "{repo_name}"
    source_license: "{candidate.get("license", "unknown")}"
    harvested_date: {today}
    review_status: needs_review
    coordination_status: owner_not_contacted
    generated_by: lesson_extractor_v2
    thank_you_note: "Thank you to the maintainers of {owner}/{repo_name}"
    ---
    """)

    # Build content
    content = dedent(f"""\
    # Lessons from {owner}/{repo_name}: {topic}

    ## Summary

    This candidate lesson was automatically generated from the public repository
    [{owner}/{repo_name}]({github_url}) to address a gap in the lessons corpus
    regarding: **{topic}**.

    ## Source Project

    - **Repository:** [{owner}/{repo_name}]({github_url})
    - **Language:** {candidate.get("primary_language", "Unknown")}
    - **Stars:** {candidate.get("stars", 0)}
    - **License:** {candidate.get("license", "Unknown")}

    ## Lesson

    {lesson_body}

    ## Evidence From Project

    {evidence_section}

    ## Why This May Belong in Lessons Hub

    This project was identified through corpus gap detection. The gap record
    indicates that questions about "{topic}" cannot be adequately answered
    from existing lessons.

    """)

    attribution = ATTRIBUTION_TEMPLATE.format(
        owner=owner,
        repo_name=repo_name,
        github_url=github_url,
    )

    coordination = dedent("""\
    ## Coordination TODO

    Before proposing this lesson to the source project:
    1. Complete the review checklist above
    2. Verify the coordination TODO has been created
    3. Contact the project maintainer if contributing upstream
    """)

    full_content = frontmatter + content + attribution + review_checklist + coordination

    # Write to candidate-lessons directory
    lesson_dir = CANDIDATE_LESSONS_DIR / owner / repo_name
    lesson_dir.mkdir(parents=True, exist_ok=True)
    lesson_path = lesson_dir / f"{slug}.md"
    lesson_path.write_text(full_content, encoding="utf-8")

    return lesson_path

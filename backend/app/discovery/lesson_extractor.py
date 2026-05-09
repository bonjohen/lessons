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

    # Build lesson content from detected files
    summary_parts = []
    evidence_parts = []

    readme = repo_dir / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8", errors="replace")[:2000]
        summary_parts.append(f"Project README excerpt:\n{readme_text[:500]}")

    for category, files in content_files.items():
        if files:
            evidence_parts.append(f"**{category.title()}:** {len(files)} file(s) found")
            for f in files[:3]:
                try:
                    rel = f.relative_to(repo_dir)
                    evidence_parts.append(f"  - `{rel}`")
                except ValueError:
                    pass

    topic = gap.get("normalized_topic", "unknown topic")
    slug = topic.replace(" ", "-")[:50]

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
    tags: [{', '.join(gap.get('missing_concepts', [])[:5])}]
    source_project: "{owner}/{repo_name}"
    source_project_url: "{github_url}"
    source_owner: "{owner}"
    source_repo: "{repo_name}"
    source_license: "{candidate.get('license', 'unknown')}"
    harvested_date: {today}
    review_status: needs_review
    coordination_status: owner_not_contacted
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
    - **Language:** {candidate.get('primary_language', 'Unknown')}
    - **Stars:** {candidate.get('stars', 0)}
    - **License:** {candidate.get('license', 'Unknown')}

    ## Lesson

    *This section needs human review and expansion based on the source project's
    actual practices and documentation.*

    The project demonstrates practices related to {topic} that may be valuable
    for the lessons corpus.

    ## Evidence From Project

    {chr(10).join(evidence_parts) if evidence_parts else 'No specific evidence files detected.'}

    ## Why This May Belong in Lessons Hub

    This project was identified through corpus gap detection. The gap record
    indicates that questions about "{topic}" cannot be adequately answered
    from existing lessons.

    """)

    attribution = ATTRIBUTION_TEMPLATE.format(
        owner=owner, repo_name=repo_name, github_url=github_url,
    )

    review_notes = dedent("""\
    ## Review Notes

    - [ ] Review generated content for accuracy
    - [ ] Expand the Lesson section with specific practices from the project
    - [ ] Verify attribution is correct
    - [ ] Check license compatibility

    ## Coordination TODO

    Before proposing this lesson to the source project:
    1. Complete the review checklist above
    2. Verify the coordination TODO has been created
    3. Contact the project maintainer if contributing upstream
    """)

    full_content = frontmatter + content + attribution + review_notes

    # Write to candidate-lessons directory
    lesson_dir = CANDIDATE_LESSONS_DIR / owner / repo_name
    lesson_dir.mkdir(parents=True, exist_ok=True)
    lesson_path = lesson_dir / f"{slug}.md"
    lesson_path.write_text(full_content, encoding="utf-8")

    return lesson_path

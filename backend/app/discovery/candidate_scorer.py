"""Score candidate repositories for lesson extraction potential."""

from __future__ import annotations


def score_candidate(repo: dict, gap: dict) -> tuple[float, list[str]]:
    """Score a candidate repo on a 0-1 scale with reasons.

    Criteria from PDR 11.2:
    1. Topic relevance
    2. README quality (description length as proxy)
    3. Documentation quality (topics/wiki)
    4. Deployment files (inferred from topics)
    5. CI/CD files (inferred from topics)
    6. Presence of lessons/docs/ADRs
    7. Recent activity
    8. License availability
    9. Extraction simplicity
    10. Gap match
    """
    score = 0.0
    reasons = []

    # 1. Topic relevance — check if gap concepts appear in repo description/topics
    gap_concepts = set(gap.get("missing_concepts", []))
    desc = (repo.get("description", "") + " " + " ".join(repo.get("topics", []))).lower()
    matching = gap_concepts & set(desc.split())
    if matching:
        s = min(0.2, len(matching) * 0.05)
        score += s
        reasons.append(f"Topic match: {', '.join(matching)}")

    # 2. README quality (description length)
    if len(repo.get("description", "")) > 50:
        score += 0.1
        reasons.append("Has detailed description")

    # 3. Documentation signals
    if repo.get("has_wiki"):
        score += 0.05
        reasons.append("Has wiki")
    topics = repo.get("topics", [])
    doc_topics = {"documentation", "docs", "tutorial", "guide", "example", "lessons-learned"}
    if doc_topics & set(topics):
        score += 0.1
        reasons.append("Has documentation topics")

    # 4. Deployment signals
    deploy_topics = {"terraform", "docker", "kubernetes", "deployment", "ci-cd", "github-actions"}
    if deploy_topics & set(topics):
        score += 0.1
        reasons.append("Has deployment-related topics")

    # 5. CI/CD signals (overlaps with 4)
    ci_topics = {"github-actions", "ci", "ci-cd", "continuous-integration"}
    if ci_topics & set(topics):
        score += 0.05
        reasons.append("Has CI/CD topics")

    # 6. Lessons/docs/ADR signals
    lesson_topics = {"lessons-learned", "adr", "architecture-decision-records", "postmortem"}
    if lesson_topics & set(topics):
        score += 0.15
        reasons.append("Has lessons/ADR topics")

    # 7. Recent activity — updated in last year gets a bonus
    last_updated = repo.get("last_updated", "")
    if last_updated and last_updated[:4] >= "2025":
        score += 0.1
        reasons.append("Recently active")

    # 8. License
    if repo.get("license"):
        score += 0.05
        reasons.append(f"Licensed: {repo['license']}")

    # 9. Stars as quality proxy
    stars = repo.get("stars", 0)
    if stars >= 100:
        score += 0.1
        reasons.append(f"{stars} stars")
    elif stars >= 10:
        score += 0.05
        reasons.append(f"{stars} stars")

    return min(1.0, round(score, 2)), reasons

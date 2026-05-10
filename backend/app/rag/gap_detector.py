"""Gap detector — identifies when the corpus cannot answer a query well."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from nltk.stem import SnowballStemmer

logger = logging.getLogger(__name__)

_stemmer = SnowballStemmer("english")

# Minimum relevance score threshold
MIN_RELEVANCE_THRESHOLD = 0.3

# Minimum distinct lessons for adequate coverage
MIN_DISTINCT_LESSONS = 2

# Rule 3: related-but-unanswered thresholds
RELATED_BUT_UNANSWERED_THRESHOLD = 0.5
MIN_CHUNKS_FOR_RELATED = 3

# Rule 7: general-knowledge answer threshold
MIN_ANSWER_LENGTH_FOR_WEAK_EVIDENCE = 200

# Weak-answer signal phrases
WEAK_ANSWER_PHRASES = [
    "does not appear to contain",
    "no relevant lessons",
    "could not find",
    "limited coverage",
    "not enough material",
    "corpus does not",
    "don't have enough",
    "insufficient information",
    "I don't see",
    "no lessons found",
]

# Gap type classifications
GAP_TYPES = {
    "missing_topic",
    "thin_coverage",
    "missing_platform",
    "missing_example",
    "missing_deployment_pattern",
    "missing_failure_case",
    "missing_comparison",
    "missing_reference_implementation",
}

# Keywords suggesting platform-specific queries — loaded from JSON, with hardcoded fallback
_PLATFORM_KEYWORDS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "platform-keywords.json"
_FALLBACK_PLATFORM_KEYWORDS = [
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "heroku", "vercel", "netlify", "cloudflare", "digitalocean",
]


def _load_platform_keywords() -> list[str]:
    try:
        with open(_PLATFORM_KEYWORDS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _FALLBACK_PLATFORM_KEYWORDS


PLATFORM_KEYWORDS = _load_platform_keywords()


def detect_gap(
    query: str,
    chunks: list[dict],
    answer: str,
    relevant_lessons: list[dict],
) -> dict | None:
    """Evaluate whether a query reveals a corpus gap.

    Returns a gap record dict if a gap is detected, or None.
    Implements the 7 detection rules from PDR section 10.
    """
    reasons = []

    # Rule 1: No retrieval results exceed minimum relevance
    scores = [c.get("similarity_score", 0) for c in chunks]
    rule1 = not scores or max(scores) < MIN_RELEVANCE_THRESHOLD
    if rule1:
        reasons.append("no_relevant_chunks")
    logger.debug("Rule 1 (no_relevant_chunks): %s", "fired" if rule1 else "passed")

    # Rule 2: Fewer than 2 distinct lessons are relevant
    above_threshold = [c for c in chunks if c.get("similarity_score", 0) >= MIN_RELEVANCE_THRESHOLD]
    distinct_lessons = set(c.get("lesson_id", "") for c in above_threshold)
    rule2 = len(distinct_lessons) < MIN_DISTINCT_LESSONS
    if rule2:
        reasons.append("few_distinct_lessons")
    logger.debug("Rule 2 (few_distinct_lessons): %s", "fired" if rule2 else "passed")

    # Rule 3: Retrieved lessons related but don't answer the question
    # (Detected via low top score with some results present)
    rule3 = scores and 0 < max(scores) < RELATED_BUT_UNANSWERED_THRESHOLD and len(chunks) >= MIN_CHUNKS_FOR_RELATED
    if rule3:
        reasons.append("related_but_unanswered")
    logger.debug("Rule 3 (related_but_unanswered): %s", "fired" if rule3 else "passed")

    # Rule 4: Model answer uses weak language
    answer_lower = answer.lower()
    rule4 = False
    for phrase in WEAK_ANSWER_PHRASES:
        if phrase in answer_lower:
            reasons.append("weak_answer_language")
            rule4 = True
            break
    logger.debug("Rule 4 (weak_answer_language): %s", "fired" if rule4 else "passed")

    # Rule 5: User explicitly asks for material not present
    # (Detected by question patterns like "do I have any lessons about...")
    ask_patterns = [
        r"do i have.*(lesson|material|content|doc)",
        r"what lessons.*(about|on|for|regarding)",
        r"any.*(lesson|coverage|material).*(about|on|for)",
    ]
    rule5 = False
    for pattern in ask_patterns:
        if re.search(pattern, query.lower()):
            # Only flag if answer suggests absence
            if any(p in answer_lower for p in WEAK_ANSWER_PHRASES):
                reasons.append("explicit_absence_query")
                rule5 = True
            break
    logger.debug("Rule 5 (explicit_absence_query): %s", "fired" if rule5 else "passed")

    # Rule 6: Query contains named technology/platform with no matching lessons
    query_lower = query.lower()
    rule6 = False
    for platform in PLATFORM_KEYWORDS:
        if platform in query_lower:
            # Check if any retrieved lesson mentions this platform
            chunk_texts = " ".join(c.get("chunk_text", "") for c in chunks).lower()
            if platform not in chunk_texts:
                reasons.append("missing_platform")
                rule6 = True
                break
    logger.debug("Rule 6 (missing_platform): %s", "fired" if rule6 else "passed")

    # Rule 7: Answer depends mostly on general knowledge
    # (Proxy: answer is long but few relevant chunks)
    rule7 = len(answer) > MIN_ANSWER_LENGTH_FOR_WEAK_EVIDENCE and len(above_threshold) < MIN_DISTINCT_LESSONS
    if rule7:
        reasons.append("general_knowledge_answer")
    logger.debug("Rule 7 (general_knowledge_answer): %s", "fired" if rule7 else "passed")

    if not reasons:
        logger.info("Gap detection: no gap for query %r", query)
        return None

    logger.info("Gap detected for query %r: reasons=%s", query, reasons)

    # Classify gap type
    gap_type = _classify_gap(reasons, query)

    # Generate gap ID
    topic = _normalize_topic(query)
    gap_id = f"gap_{hashlib.md5(topic.encode()).hexdigest()[:12]}"

    return {
        "gap_id": gap_id,
        "created_date": datetime.now(timezone.utc).isoformat(),
        "updated_date": datetime.now(timezone.utc).isoformat(),
        "status": "open",
        "trigger_query": query,
        "normalized_topic": topic,
        "missing_concepts": _extract_concepts(query),
        "retrieval_summary": (
            f"{len(chunks)} chunks retrieved, {len(distinct_lessons)} distinct lessons, "
            f"max score {max(scores) if scores else 0:.2f}"
        ),
        "best_matching_lessons": list(distinct_lessons)[:5],
        "confidence_score": max(scores) if scores else 0.0,
        "suggested_github_queries": _suggest_github_queries(query, topic),
        "candidate_repo_ids": [],
        "todo_ids": [],
        "resolution_notes": "",
        "gap_type": gap_type,
        "detection_reasons": reasons,
    }


def _classify_gap(reasons: list[str], query: str) -> str:
    """Classify the gap type from detection reasons and query content."""
    if "missing_platform" in reasons:
        return "missing_platform"
    if "no_relevant_chunks" in reasons:
        return "missing_topic"
    if "few_distinct_lessons" in reasons and "related_but_unanswered" not in reasons:
        return "thin_coverage"

    query_lower = query.lower()
    if any(w in query_lower for w in ["example", "sample", "demo", "tutorial"]):
        return "missing_example"
    if any(w in query_lower for w in ["deploy", "deployment", "ci/cd", "pipeline"]):
        return "missing_deployment_pattern"
    if any(w in query_lower for w in ["fail", "error", "bug", "issue", "postmortem"]):
        return "missing_failure_case"
    if any(w in query_lower for w in ["compare", "vs", "versus", "difference", "alternative"]):
        return "missing_comparison"

    return "missing_topic"


def _normalize_topic(query: str) -> str:
    """Normalize a query into a stemmed topic string."""
    # Remove question words and punctuation
    topic = re.sub(r"^(what|how|why|when|where|do|does|is|are|can|should|have)\b", "", query.lower()).strip()
    topic = re.sub(r"[?!.,;:]", "", topic).strip()
    topic = re.sub(r"\s+", " ", topic)
    # Stem each word and sort for order-independent gap merging
    words = topic.split()
    stemmed = sorted(set(_stemmer.stem(w) for w in words))
    return " ".join(stemmed)[:100]


def _extract_concepts(query: str) -> list[str]:
    """Extract key concepts from the query."""
    stop_words = {
        "i",
        "my",
        "me",
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "do",
        "does",
        "have",
        "has",
        "had",
        "what",
        "how",
        "why",
        "when",
        "where",
        "about",
        "any",
        "lessons",
        "lesson",
        "material",
        "content",
        "documentation",
        "in",
        "on",
        "for",
        "to",
        "of",
        "and",
        "or",
        "with",
        "from",
        "that",
        "this",
        "it",
    }
    words = re.findall(r"\b[a-z][a-z0-9-]+\b", query.lower())
    # Stem concepts for consistent gap merging
    stemmed = []
    seen = set()
    for w in words:
        if w in stop_words or len(w) <= 2:
            continue
        s = _stemmer.stem(w)
        if s not in seen:
            seen.add(s)
            stemmed.append(s)
    return stemmed[:10]


def _suggest_github_queries(query: str, topic: str) -> list[str]:
    """Generate GitHub search queries from the topic."""
    concepts = _extract_concepts(query)
    if not concepts:
        return [topic]

    queries = []
    # Full topic
    queries.append(" ".join(concepts[:5]))
    # Top concepts with context words
    if len(concepts) >= 3:
        queries.append(f"{concepts[0]} {concepts[1]} tutorial")
        queries.append(f"{concepts[0]} {concepts[1]} {concepts[2]} example")
    if len(concepts) >= 2:
        queries.append(f"{concepts[0]} {concepts[1]} best practices")

    return queries[:5]

---
title: Rule-Based Gap Detection Without ML
summary: Seven heuristic rules detect when a RAG corpus can't answer a query, without training data or a classifier — transparent and debuggable, with known trade-offs.
date: 2026-05-09
phase: implementation
lesson_type: architecture
status: active
tags: [rag, gap-detection, heuristics, nlp, quality]
---

# Rule-Based Gap Detection Without ML

## The Lesson

When you need to detect quality gaps in a retrieval system but don't have labeled training data, a set of transparent heuristic rules — each testing one specific signal — is more maintainable and debuggable than a black-box classifier. The rules will be imperfect, but their imperfections are visible and individually fixable.

## Context

A RAG chatbot over a corpus of 793 chunks from 116 lessons needed to detect when a user's query exposed a gap — a topic the corpus couldn't answer well. Detected gaps feed into a discovery pipeline that searches GitHub for candidate source material. There was no labeled dataset of "good answers" vs. "gap answers" to train a classifier. The system needed to work immediately with reasonable accuracy, and the maintainer needed to understand and tune why each detection fired.

## What Happened

1. Defined seven independent rules, each testing a different signal from the retrieval results and the generated answer. Each rule either fires or doesn't, appending a reason tag to a list.
2. **Rule 1: No relevant chunks.** If the maximum similarity score across all retrieved chunks is below 0.3, the corpus has nothing close to the query. This catches completely novel topics.
3. **Rule 2: Few distinct lessons.** If fewer than 2 distinct lessons have chunks above the 0.3 threshold, coverage is thin — one lesson mentioning the topic in passing isn't real coverage.
4. **Rule 3: Related but unanswered.** If chunks exist with scores between 0.0 and 0.5, and there are 3+ results, the corpus has related material but doesn't actually answer the question.
5. **Rule 4: Weak answer language.** If the LLM's answer contains phrases like "does not appear to contain," "no relevant lessons," or "insufficient information" (10 phrases total), the model is signaling it couldn't ground its answer.
6. **Rule 5: Explicit absence query.** If the user asks "do I have any lessons about X" and the answer uses weak language, this combines user intent with model acknowledgment.
7. **Rule 6: Missing platform.** If the query mentions a platform keyword (AWS, Docker, Kubernetes, etc.) but none of the retrieved chunks contain that keyword, there's a platform-specific gap.
8. **Rule 7: General knowledge answer.** If the answer is longer than 200 characters but fewer than 2 chunks scored above threshold, the model is filling in from general knowledge rather than corpus evidence.
9. Multiple rules can fire simultaneously. The gap record captures all triggered reasons, enabling analysis of which combinations are most reliable.
10. Gap records merge by normalized topic (MD5 hash). Repeated queries about the same topic append to `additional_queries` rather than creating duplicates.

## Key Insights

- **Each rule should test exactly one signal.** Combining "low scores AND weak language" into a single rule makes it impossible to tell which signal mattered. Separate rules that fire independently let you analyze detection patterns — if Rule 4 fires without Rule 1, the corpus has relevant material but the LLM couldn't synthesize an answer from it.

- **Transparent thresholds are worth the imprecision.** The 0.3 relevance threshold is somewhat arbitrary. But because it's a named constant (`MIN_RELEVANCE_THRESHOLD = 0.3`), anyone can find it, understand it, and adjust it. A trained classifier with 0.82 accuracy is harder to improve when it misclassifies.

- **Testing heuristic rules is straightforward.** Each rule is a pure function of (query, chunks, answer, lessons). Unit tests construct specific inputs that should or shouldn't trigger each rule. 17 tests cover all 7 rules, topic normalization, and edge cases. Testing a trained model requires a labeled evaluation set.

- **Gap merging prevents duplication but loses nuance.** Hashing the normalized topic means "how do I deploy to Kubernetes" and "Kubernetes deployment best practices" produce the same gap ID. This is usually correct — they're the same gap. But "Kubernetes networking" and "Kubernetes storage" might also collide after normalization strips question words.

- **The concept extraction is the weakest link.** A stopword list without stemming means "deploying" and "deployment" are treated as different concepts. This affects both gap merging (different gap IDs for the same topic) and GitHub search query generation. Adding a stemmer is the highest-value improvement.

- **Platform keyword lists decay.** The hardcoded list of 11 platforms (AWS, Docker, Kubernetes, etc.) was correct at authoring time but doesn't include platforms added to the corpus later. Data-driven keyword lists loaded from configuration would track the corpus.

## Examples

**Rule interaction example:**

A query about "Terraform module best practices" against a corpus with no Terraform content:
- Rule 1 fires: max similarity = 0.12 (below 0.3)
- Rule 2 fires: 0 distinct lessons above threshold
- Rule 6 fires: "terraform" in query, not in any chunk text
- Rule 4 fires: answer contains "no relevant lessons"
- Gap type classified as `missing_platform` (Rule 6 takes priority)
- Detection reasons: `["no_relevant_chunks", "few_distinct_lessons", "missing_platform", "weak_answer_language"]`

## Applicability

Rule-based gap detection works when:
- You have observable signals (scores, text patterns, metadata) that correlate with quality
- You need to ship immediately without training data
- Maintainers need to understand and tune detection behavior
- The cost of false positives is low (creating an unnecessary gap record is cheap)

Consider a trained classifier instead when:
- You have 1000+ labeled examples of good vs. gap responses
- The signals are subtle or interdependent (rules can't capture the interaction)
- You need calibrated confidence scores, not binary fire/no-fire

## Related Lessons

- [RAG Corpus Chunking Strategy](rag-corpus-chunking-strategy.md) — the chunking decisions that determine what similarity scores the gap detector sees

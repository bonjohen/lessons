---
title: RAG Corpus Chunking Strategy
summary: Splitting documents at H2 headings with stable IDs and content hashes produces predictable, debuggable chunks that support incremental re-indexing.
date: 2026-05-09
phase: implementation
lesson_type: architecture
status: active
tags: [rag, chunking, embeddings, vector-search, content-hashing]
---

# RAG Corpus Chunking Strategy

## The Lesson

When chunking documents for RAG retrieval, split at semantic boundaries the author already created (headings) rather than at arbitrary token counts. Assign deterministic chunk IDs and compute content hashes so that re-indexing can detect what changed without re-embedding everything.

## Context

A lessons library of 116 markdown documents needed to be chunked for vector search. Each lesson is a standalone markdown file with an H1 title, optional H2 sections, and YAML frontmatter (title, summary, tags, repo source). The chunks feed into a RAG chatbot that retrieves relevant excerpts, cites sources by lesson title, and builds grounded answers. The corpus is rebuilt on every CI run (daily + on push), so re-indexing performance matters.

## What Happened

1. Chose H2 headings as the split boundary. Each lesson's content before the first H2 becomes chunk 0 (labeled "Introduction"). Each H2 section becomes a subsequent chunk. H3 and deeper headings stay within their parent H2 chunk — splitting on every heading would create fragments too small for meaningful retrieval.
2. Assigned chunk IDs as `{lesson_id}-{chunk_index}` where `chunk_index` is the position within the lesson (0 for intro, 1+ for sections). This is deterministic: the same lesson content always produces the same IDs, regardless of when or where the build runs.
3. Each chunk carries a heading path breadcrumb (e.g., "Git Basics > Branching") so the RAG prompt builder can tell the LLM where in a lesson the excerpt came from. This improves citation quality — the model can say "according to the Branching section of Git Basics" rather than just "according to Git Basics."
4. Computed a SHA-256 content hash (truncated to 16 hex chars) of each chunk's text. The hash is stored in the chunk metadata. On re-indexing, the embedder can compare hashes against the vector store's existing metadata to skip unchanged chunks. This infrastructure exists but isn't wired yet — the current embedder does a full re-index every time.
5. Token count is estimated as `word_count * 1.33` (approximately 0.75 tokens per word), with a minimum of 1. The corpus validator warns if any chunk exceeds 5,000 estimated tokens but doesn't fail the build. In practice, 793 chunks from 116 lessons averaged well under 1,000 tokens.
6. The corpus builder outputs two files: `rag-chunks.json` (the chunks) and `rag-manifest.json` (statistics: total lessons, chunks, skipped empty lessons, average tokens). The manifest is a build artifact for monitoring corpus drift over time.

## Key Insights

- **Author-defined boundaries beat arbitrary token windows.** H2 headings are where the author decided to change topics. A chunk that spans "## Setup" and half of "## Configuration" is semantically incoherent. A chunk that is exactly "## Setup" is a self-contained unit. The trade-off is variable chunk size — some sections are 50 words, others are 2,000.

- **Stable IDs enable diffing.** `lesson-slug-0`, `lesson-slug-1` are the same across builds if the lesson hasn't changed. This means the vector store can be updated incrementally: delete chunks whose IDs disappeared, re-embed chunks whose content hashes changed, skip the rest. Without stable IDs, every rebuild is a full re-index.

- **Content hashes are cheap insurance.** SHA-256 of the chunk text adds negligible build time but enables the most valuable optimization (incremental re-indexing). Even if you don't implement incremental re-indexing immediately, having the hashes in the data means you can add it later without rebuilding the corpus format.

- **Intro content needs a chunk too.** Many lessons have substantial content before the first H2 — overview paragraphs, context, motivation. Dropping this content (only chunking H2 sections) loses the most general and often most useful text. Making it chunk 0 with heading path set to just the lesson title preserves it naturally.

- **Validation should warn, not block.** A 5,000-token chunk is unusual but not necessarily wrong — some lessons have long reference sections. Warning lets the maintainer investigate; failing the build blocks deployment for a content issue. Error severity should match the consequence: empty chunks are errors (would produce nonsense embeddings), large chunks are warnings.

## Examples

**Input markdown:**
```markdown
This lesson covers Git basics.

## Branching

Create branches with `git checkout -b feature`.

## Merging

Merge with `git merge feature`.
```

**Output chunks:**
| chunk_id | chunk_index | heading_path | content |
|----------|-------------|-------------|---------|
| `git-basics-0` | 0 | "Git Basics" | "This lesson covers Git basics." |
| `git-basics-1` | 1 | "Git Basics > Branching" | "## Branching\n\nCreate branches..." |
| `git-basics-2` | 2 | "Git Basics > Merging" | "## Merging\n\nMerge with..." |

## Applicability

Heading-based chunking works when:
- Documents have consistent heading structure (technical docs, tutorials, guides)
- Headings correspond to topic boundaries (not just formatting)
- Variable chunk size is acceptable (retrieval systems handle it; fixed-size-window systems may not)

Consider fixed-size windows instead when:
- Documents lack headings or use them inconsistently
- Exact token budget compliance is required (e.g., context window limits)
- Documents are very long (books, legal filings) where heading sections can be 10,000+ tokens

## Related Lessons

- [Rule-Based Gap Detection](rule-based-gap-detection.md) — gap detection quality depends on chunk granularity and similarity score distributions
- [Harvester Design Decisions](harvester-design-decisions.md) — the upstream lesson parsing that produces the content being chunked

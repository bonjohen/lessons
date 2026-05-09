# Product Design Review: Lessons Hub Cloud RAG Backend and External Lessons Discovery

Date: May 9, 2026
Repository: `github.com/bonjohen/lessons`
Project: Lessons Hub
Target Version: V2
Primary Goal: Extend the existing Lessons Hub static site into a cloud-backed RAG system that can answer questions from the lessons corpus, identify unanswered requests, and discover external GitHub projects that may deserve lesson extraction.

---

## 1. Product Summary

Lessons Hub currently harvests lesson markdown files from configured GitHub repositories, normalizes the lesson data, validates it, builds an Astro static website, generates search indexes, and publishes AI-readable exports.

V2 adds three major capabilities:

1. A cloud-based RAG chatbot backed by the harvested lessons corpus.
2. A corpus-gap detection system that identifies useful questions the current corpus cannot answer.
3. A GitHub project discovery workflow that finds relevant external projects, pulls them locally, harvests or drafts candidate lessons, stages those lessons inside the Lessons Hub workflow, and creates a coordination TODO before any external contribution is proposed.

The existing static website remains the main browsing interface. The chatbot and discovery features are additive.

---

## 2. Current State

Lessons Hub currently has:

1. A repo registry in `data/repos.yml`.
2. A lesson harvesting pipeline.
3. Lesson validation.
4. Generated lesson JSON.
5. AI-readable export packs.
6. Astro static site generation.
7. Pagefind search indexing.
8. GitHub Pages deployment.
9. Source repos expected to place lessons in `docs/lessons/*.md`.

The current system is suitable as the foundation for a RAG corpus because it already normalizes lessons and generates machine-readable exports.

---

## 3. Target Capabilities

V2 should support:

1. Chatbot questions over the lessons corpus.
2. Answers with relevant lesson links.
3. Clear admission when the corpus lacks enough information.
4. Logging of unanswered or weakly answered requests.
5. Reviewable “corpus gap” records.
6. GitHub search for projects relevant to corpus gaps.
7. Candidate external project intake.
8. Local clone/pull of candidate projects.
9. Automated lesson harvesting or lesson drafting from candidate projects.
10. Staging of candidate lessons in Lessons Hub.
11. TODO creation for owner coordination before contributing lessons upstream.
12. Four deployment profiles:

    * Local development
    * AWS
    * Azure
    * GCP

---

## 4. Non-Goals

V2 does not include:

1. Automatic pull requests to external project owners.
2. Automatic commits to third-party repositories.
3. User accounts.
4. Personalized chat memory.
5. Public lesson editing.
6. Comments, ratings, or social features.
7. Model fine-tuning.
8. Replacing Pagefind search.
9. Replacing the static Astro site.
10. Treating generated external lessons as authoritative before review.

---

## 5. User Experience

### 5.1 Chatbot Experience

User opens “Ask the Lessons” and asks:

> What lessons do I have about staging deployments before production?

The system returns:

1. A concise answer.
2. Links to relevant lessons.
3. Source lesson cards.
4. Confidence indicator.
5. Optional “This seems missing” notice if coverage is weak.

### 5.2 Corpus Gap Experience

If the user asks:

> What lessons do I have about Azure Container Apps deployment?

And the corpus has weak or no coverage, the system should say:

> I do not see enough material in the lessons corpus to answer this well.

Then it should create or update a gap record:

```text
Gap: Azure Container Apps deployment lessons
Triggering query: What lessons do I have about Azure Container Apps deployment?
Status: Open
Suggested action: Search GitHub for relevant projects and generate candidate lessons.
```

### 5.3 External Discovery Experience

From a gap record, the user or scheduled process can run:

```text
Search GitHub for relevant projects
```

The system then:

1. Searches GitHub for projects related to the gap.
2. Scores candidate repositories.
3. Pulls selected candidates into a local/external workspace.
4. Applies the Lessons extraction workflow.
5. Stages generated candidate lessons in Lessons Hub.
6. Creates a TODO to contact or coordinate with the project owner before proposing the lessons.

Generated lessons must include:

1. Source project name.
2. Source project URL.
3. Date harvested.
4. Clear attribution.
5. Thank-you note.
6. Review status.
7. Coordination TODO.

---

## 6. System Architecture

V2 adds four layers to the current project:

1. RAG backend
2. Gap detection
3. External GitHub discovery
4. Multi-cloud deployment

Logical flow:

```text
configured source repos
→ harvest lessons
→ normalize lessons
→ validate lessons
→ build static site
→ build RAG corpus
→ embed/index chunks
→ chatbot retrieves chunks
→ chatbot answers with lesson links
→ weak answers create corpus gaps
→ gaps drive GitHub discovery
→ discovery stages candidate lessons
→ TODO tracks owner coordination
```

---

## 7. Main Components

### 7.1 Static Frontend

Existing Astro site remains.

Add:

1. Chat panel.
2. “Ask the Lessons” page.
3. Relevant lesson cards.
4. Corpus gap notice.
5. Optional gap review page.
6. Optional external candidate review page.

### 7.2 Backend API

Use FastAPI.

Primary endpoints:

1. `GET /health`
2. `POST /api/retrieve`
3. `POST /api/chat`
4. `POST /api/gaps`
5. `GET /api/gaps`
6. `POST /api/github/search`
7. `POST /api/github/harvest-candidate`
8. `GET /api/todos`

### 7.3 RAG Corpus Builder

Converts normalized lessons into retrieval chunks.

Responsibilities:

1. Load generated lesson data.
2. Convert markdown to text.
3. Chunk lessons by heading.
4. Preserve source metadata.
5. Generate stable chunk IDs.
6. Produce `rag-chunks.json`.
7. Produce `rag-manifest.json`.

### 7.4 Vector Index

Stores lesson chunks for retrieval.

Local profile:

1. PostgreSQL with pgvector.

AWS profile:

1. Bedrock Knowledge Bases or OpenSearch Serverless.

Azure profile:

1. Azure AI Search.

GCP profile:

1. Vertex AI Vector Search.

### 7.5 Gap Detection

Determines when the current corpus does not answer a request.

Inputs:

1. User query.
2. Retrieval results.
3. Similarity scores.
4. Number of distinct relevant lessons.
5. Model answer quality signal.
6. “I don’t know” generation behavior.

Outputs:

1. Gap record.
2. Suggested search terms.
3. Candidate tags.
4. Candidate repo search query.
5. TODO item if action is needed.

### 7.6 GitHub Discovery

Finds public GitHub projects that may contain relevant material.

Responsibilities:

1. Build GitHub search queries from gap records.
2. Search repositories.
3. Score candidates.
4. Pull selected repositories into a controlled workspace.
5. Run lesson extraction workflow.
6. Stage candidate lessons.
7. Create coordination TODOs.

### 7.7 TODO System

A lightweight project TODO list for generated follow-up work.

Required fields:

1. `todo_id`
2. `title`
3. `notes`
4. `status`
5. `priority`
6. `severity`
7. `created_date`
8. `due_date`
9. `completion_date`
10. `source_gap_id`
11. `source_project_url`
12. `candidate_lesson_path`

---

## 8. Data Model

### 8.1 Lesson Record

Required fields:

1. `lesson_id`
2. `title`
3. `summary`
4. `repo_id`
5. `repo_name`
6. `repo_url`
7. `lesson_url`
8. `source_path`
9. `date`
10. `phase`
11. `lesson_type`
12. `status`
13. `tags`
14. `content_markdown`
15. `content_text`

### 8.2 RAG Chunk Record

Required fields:

1. `chunk_id`
2. `lesson_id`
3. `repo_id`
4. `title`
5. `summary`
6. `lesson_url`
7. `chunk_index`
8. `heading_path`
9. `chunk_text`
10. `token_count`
11. `tags`
12. `content_hash`
13. `embedding_model`
14. `indexed_at`

### 8.3 Corpus Gap Record

Location:

```text
data/gaps/corpus-gaps.json
```

Required fields:

1. `gap_id`
2. `created_date`
3. `updated_date`
4. `status`
5. `trigger_query`
6. `normalized_topic`
7. `missing_concepts`
8. `retrieval_summary`
9. `best_matching_lessons`
10. `confidence_score`
11. `suggested_github_queries`
12. `candidate_repo_ids`
13. `todo_ids`
14. `resolution_notes`

Allowed statuses:

1. `open`
2. `searching`
3. `candidates_found`
4. `lessons_staged`
5. `owner_coordination_needed`
6. `resolved`
7. `closed_no_action`

### 8.4 Candidate Repository Record

Location:

```text
data/external/candidate-repos.json
```

Required fields:

1. `candidate_repo_id`
2. `gap_id`
3. `github_url`
4. `owner`
5. `repo_name`
6. `description`
7. `primary_language`
8. `stars`
9. `last_updated`
10. `license`
11. `clone_url`
12. `local_path`
13. `score`
14. `score_reasons`
15. `harvest_status`
16. `candidate_lesson_paths`
17. `todo_ids`

### 8.5 Candidate Lesson Record

Candidate lessons are staged as markdown.

Location:

```text
docs/candidate-lessons/external/{owner}/{repo}/{lesson_slug}.md
```

Required frontmatter:

```yaml
title:
summary:
date:
phase:
lesson_type:
status: candidate_external
tags:
source_project:
source_project_url:
source_owner:
source_repo:
source_license:
harvested_date:
review_status: needs_review
coordination_status: owner_not_contacted
thank_you_note:
```

Required content sections:

1. Summary
2. Source Project
3. Lesson
4. Evidence From Project
5. Why This May Belong in Lessons Hub
6. Attribution and Thanks
7. Review Notes
8. Coordination TODO

---

## 9. External Lesson Attribution Standard

Every generated external candidate lesson must include this attribution block:

```text
Source Project: {owner}/{repo}
Source Link: {github_url}

This candidate lesson was generated from publicly available project material. Thank you to the maintainers of {owner}/{repo} for making their work available. This lesson should not be proposed back to the source project until it has been reviewed and the owner/maintainer coordination TODO has been completed.
```

The generated lesson must not imply endorsement by the project owner.

The generated lesson must not be committed to the source project without explicit human review and coordination.

---

## 10. Gap Detection Rules

A gap should be created when one or more of these are true:

1. No retrieval results exceed the minimum relevance threshold.
2. Fewer than two distinct lessons are relevant.
3. The retrieved lessons are related but do not answer the question.
4. The model answer uses weak language such as “the corpus does not appear to contain.”
5. The user explicitly asks for material not present in the corpus.
6. The query contains a named technology, platform, or pattern with no matching lessons.
7. The answer depends mostly on general model knowledge instead of retrieved context.

The gap detector should classify the gap as:

1. `missing_topic`
2. `thin_coverage`
3. `missing_platform`
4. `missing_example`
5. `missing_deployment_pattern`
6. `missing_failure_case`
7. `missing_comparison`
8. `missing_reference_implementation`

---

## 11. GitHub Discovery Rules

### 11.1 Search Query Generation

From each gap record, generate 3–10 GitHub search queries.

Example gap:

```text
Azure Container Apps deployment lessons
```

Generated searches:

```text
Azure Container Apps static site deployment GitHub Actions
Azure Container Apps FastAPI GitHub Actions
Azure Container Apps RAG chatbot
Azure Container Apps Terraform deployment
Azure Container Apps production staging workflow
```

### 11.2 Candidate Scoring

Score candidate repositories using:

1. Topic relevance.
2. README quality.
3. Documentation quality.
4. Presence of deployment files.
5. Presence of GitHub Actions workflows.
6. Presence of lessons, notes, docs, ADRs, or postmortems.
7. Recent activity.
8. License availability.
9. Simplicity of extracting a useful lesson.
10. Match to the original corpus gap.

### 11.3 Candidate Intake

For selected candidates:

1. Clone or pull into `.external/repos/{owner}/{repo}`.
2. Capture repo metadata.
3. Detect documentation files.
4. Detect CI/CD files.
5. Detect deployment scripts.
6. Detect architecture docs.
7. Run lesson extraction.
8. Stage candidate lessons.
9. Create TODOs.

### 11.4 Owner Coordination TODO

Every staged external lesson requires a TODO.

Example:

```yaml
title: Coordinate with owner for candidate lesson from azure-sample-app
notes: Review generated lesson, verify attribution, and decide whether to contact the source project owner about contributing or referencing the lesson.
status: Open
priority: 2
severity: 2
created_date: 2026-05-09
due_date:
completion_date:
source_project_url: https://github.com/example/azure-sample-app
candidate_lesson_path: docs/candidate-lessons/external/example/azure-sample-app/deployment-safety.md
```

---

## 12. API Design

### 12.1 Chat

Endpoint:

```text
POST /api/chat
```

Request:

```json
{
  "message": "What lessons do I have about Azure deployments?",
  "top_k": 8,
  "filters": {
    "repo": null,
    "tags": [],
    "lesson_type": null
  }
}
```

Response:

```json
{
  "answer": "The current corpus has limited Azure-specific deployment lessons...",
  "relevant_lessons": [],
  "gap_detected": true,
  "gap_id": "gap_azure_deployments",
  "suggested_actions": [
    "Search GitHub for Azure deployment projects",
    "Create candidate lessons from relevant repos"
  ]
}
```

### 12.2 Retrieve

Endpoint:

```text
POST /api/retrieve
```

Returns relevant chunks without generation.

### 12.3 Create Gap

Endpoint:

```text
POST /api/gaps
```

Creates or updates a corpus gap.

### 12.4 List Gaps

Endpoint:

```text
GET /api/gaps
```

Supports filters:

1. `status`
2. `tag`
3. `created_after`
4. `has_candidates`
5. `has_todos`

### 12.5 GitHub Search

Endpoint:

```text
POST /api/github/search
```

Request:

```json
{
  "gap_id": "gap_azure_deployments",
  "max_results": 20,
  "languages": ["Python", "TypeScript", "JavaScript"],
  "min_stars": 0
}
```

Response:

```json
{
  "gap_id": "gap_azure_deployments",
  "candidates": [
    {
      "github_url": "https://github.com/example/project",
      "score": 0.82,
      "score_reasons": [
        "Contains Azure Container Apps deployment files",
        "Has GitHub Actions workflow",
        "Has detailed README"
      ]
    }
  ]
}
```

### 12.6 Harvest Candidate

Endpoint:

```text
POST /api/github/harvest-candidate
```

Request:

```json
{
  "candidate_repo_id": "candidate_example_project",
  "mode": "stage_candidate_lessons"
}
```

Response:

```json
{
  "candidate_repo_id": "candidate_example_project",
  "staged_lessons": [
    "docs/candidate-lessons/external/example/project/deployment-pipeline.md"
  ],
  "todos": [
    "todo_coordinate_example_project"
  ]
}
```

---

## 13. Repository Structure

Add:

```text
backend/
  app/
    main.py
    api/
      chat.py
      retrieve.py
      gaps.py
      github_discovery.py
      health.py
    rag/
      corpus.py
      retriever.py
      generator.py
      gap_detector.py
      prompt_builder.py
    discovery/
      github_search.py
      repo_intake.py
      lesson_extractor.py
      candidate_scorer.py
      todo_writer.py
    adapters/
      vector/
      llm/
      cloud/
    models/
    tests/

data/
  gaps/
    corpus-gaps.json
  external/
    candidate-repos.json
  todos/
    todos.json

docs/
  candidate-lessons/
    external/
  deployment/
  rag/
  discovery/

scripts/
  build_rag_corpus.py
  validate_rag_corpus.py
  embed_rag_corpus.py
  search_github_for_gaps.py
  harvest_external_candidate.py
  validate_candidate_lessons.py
```

---

## 14. Frontend Changes

Add:

```text
src/components/ChatPanel.astro
src/components/RelevantLessonCard.astro
src/components/CorpusGapNotice.astro
src/components/CandidateRepoCard.astro
src/components/TodoCard.astro
src/pages/ask.astro
src/pages/gaps.astro
src/pages/candidate-lessons.astro
```

Required behavior:

1. Static site works without backend.
2. Chat UI shows backend unavailable state if needed.
3. Relevant lessons are linked.
4. Gap notices are clear but not intrusive.
5. Candidate external lessons are visually distinct from approved lessons.
6. External candidate pages must show attribution and review status.

---

## 15. Backend Implementation Stack

Use:

1. FastAPI backend.
2. Pydantic models.
3. Python lesson ingestion utilities.
4. Provider-specific vector adapters.
5. Provider-specific LLM adapters.
6. GitHub CLI or GitHub API for repository discovery.
7. Local filesystem staging for candidate external lessons.
8. JSON-backed gap and TODO storage for V2.

Database-backed storage can be added later if gap volume grows.

---

## 16. Deployment Profiles

### 16.1 Local

Local stack:

1. Astro frontend.
2. FastAPI backend.
3. PostgreSQL with pgvector.
4. Local or hosted embedding model.
5. Local or hosted chat model.
6. Local external repo workspace.

Local URLs:

```text
Frontend: http://localhost:4321
Backend:  http://localhost:8000
Health:   http://localhost:8000/health
```

### 16.2 AWS

AWS stack:

1. Static site: S3 + CloudFront.
2. Backend: ECS Fargate.
3. Container registry: ECR.
4. Vector/RAG: Bedrock Knowledge Bases or OpenSearch Serverless.
5. LLM: Bedrock.
6. Secrets: Secrets Manager.
7. Logs: CloudWatch.
8. Deployment auth: GitHub Actions OIDC.

### 16.3 Azure

Azure stack:

1. Static site: Azure Static Web Apps or Storage + CDN.
2. Backend: Azure Container Apps.
3. Container registry: Azure Container Registry.
4. Vector search: Azure AI Search.
5. LLM: Azure OpenAI or Azure AI Foundry endpoint.
6. Secrets: Key Vault.
7. Logs: Azure Monitor.
8. Deployment auth: GitHub Actions OIDC.

### 16.4 GCP

GCP stack:

1. Static site: Cloud Storage + Cloud CDN or Firebase Hosting.
2. Backend: Cloud Run.
3. Container registry: Artifact Registry.
4. Vector search: Vertex AI Vector Search.
5. LLM: Vertex AI.
6. Secrets: Secret Manager.
7. Logs: Cloud Logging.
8. Deployment auth: GitHub Actions OIDC.

---

## 17. CI/CD Design

### 17.1 Pull Request Checks

Run:

1. Install dependencies.
2. Harvest lessons.
3. Validate lessons.
4. Build RAG corpus.
5. Validate RAG corpus.
6. Build static site.
7. Build Pagefind index.
8. Run backend tests.
9. Run discovery tests with mocked GitHub responses.
10. Validate candidate lesson schema.

No production deployment from pull requests.

### 17.2 Staging Deployment

On merge to `main`:

1. Build static artifact.
2. Build backend container.
3. Build RAG corpus.
4. Deploy to staging.
5. Index staging vector store.
6. Run smoke tests.
7. Verify chat response includes lesson links.
8. Verify gap creation works for a known missing topic.

### 17.3 Production Deployment

Production requires manual approval.

Production deploys:

1. Same static artifact tested in staging.
2. Same backend container tested in staging.
3. Same corpus/index version unless explicitly rebuilt.
4. Same configuration pattern with production secrets.

---

## 18. Required Configuration

Shared:

```text
DEPLOYMENT_PROFILE
PUBLIC_RAG_API_BASE_URL
RAG_VECTOR_ADAPTER
RAG_LLM_ADAPTER
RAG_EMBEDDING_MODEL
RAG_CHAT_MODEL
RAG_TOP_K
RAG_MIN_RELEVANCE_SCORE
RAG_GAP_THRESHOLD
LESSONS_REPO_TOKEN
GITHUB_DISCOVERY_ENABLED
GITHUB_DISCOVERY_MAX_REPOS
EXTERNAL_REPO_WORKSPACE
```

Local:

```text
DATABASE_URL
LOCAL_VECTOR_DIMENSIONS
OPENAI_API_KEY
OLLAMA_BASE_URL
```

AWS:

```text
AWS_REGION
AWS_ACCOUNT_ID
ECR_REPOSITORY
ECS_CLUSTER
ECS_SERVICE
BEDROCK_KNOWLEDGE_BASE_ID
BEDROCK_MODEL_ID
STATIC_BUCKET
CLOUDFRONT_DISTRIBUTION_ID
```

Azure:

```text
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP
AZURE_CONTAINER_APP_NAME
AZURE_CONTAINER_REGISTRY
AZURE_AI_SEARCH_ENDPOINT
AZURE_AI_SEARCH_INDEX
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT
```

GCP:

```text
GCP_PROJECT_ID
GCP_REGION
GCP_ARTIFACT_REGISTRY
GCP_CLOUD_RUN_SERVICE
GCP_VERTEX_INDEX_ID
GCP_VERTEX_ENDPOINT_ID
GCP_VERTEX_MODEL
GCP_STATIC_BUCKET
```

---

## 19. Security and Safety Requirements

1. Do not store long-lived cloud credentials in GitHub.
2. Use cloud secret managers for provider keys.
3. Do not expose private tokens to the frontend.
4. Do not expose vector stores directly to browsers.
5. Disable external GitHub harvesting in public deployments unless explicitly enabled.
6. Never push to external repositories automatically.
7. Never open pull requests to external repositories automatically.
8. Generated candidate lessons must be marked as `candidate_external`.
9. External candidate lessons must include attribution.
10. External candidate lessons require human review.
11. Owner coordination TODO must exist before external contribution is considered.
12. Respect repository licenses.
13. Do not extract private repositories unless explicitly configured.
14. Do not copy large source files into lessons.
15. Summarize project practices; do not duplicate project documentation wholesale.

---

## 20. Testing Requirements

### 20.1 RAG Tests

1. Corpus generation preserves lesson metadata.
2. Chunk IDs are stable.
3. Lesson URLs resolve.
4. Retrieval returns relevant chunks.
5. Chat response includes source links.
6. Weak retrieval creates gap record.
7. Strong retrieval does not create unnecessary gap record.

### 20.2 Gap Tests

1. Missing topic creates new gap.
2. Similar missing topic updates existing gap.
3. Gap status transitions are valid.
4. Suggested GitHub queries are generated.
5. Gap records include triggering queries.

### 20.3 Discovery Tests

1. GitHub search results are parsed.
2. Candidate scoring works.
3. Candidate repo metadata is stored.
4. Clone/pull path is controlled.
5. Candidate lessons are staged.
6. Attribution block is present.
7. Thank-you note is present.
8. Coordination TODO is created.
9. No external PR is created automatically.

### 20.4 Deployment Smoke Tests

For every deployment profile:

1. Static site loads.
2. Backend health endpoint returns success.
3. Retrieval endpoint returns expected results.
4. Chat endpoint returns answer plus links.
5. Missing-topic query creates or identifies a gap.
6. Discovery endpoint is either disabled or works according to configuration.
7. Candidate lesson pages render if candidate lessons exist.

---

## 21. Acceptance Criteria

V2 is accepted when:

1. Existing static Lessons Hub behavior still works.
2. RAG chatbot answers questions from harvested lessons.
3. Chat responses include relevant lesson links.
4. Missing or weakly covered requests create gap records.
5. Gap records generate useful GitHub search queries.
6. GitHub discovery can find and score candidate repositories.
7. Selected candidate repos can be pulled into a controlled workspace.
8. Candidate lessons can be generated and staged.
9. Candidate lessons include source links and thank-you notes.
10. Owner coordination TODOs are created.
11. Local deployment works.
12. AWS deployment works.
13. Azure deployment works.
14. GCP deployment works.
15. Production deployment requires manual approval.
16. Failed builds cannot deploy to production.

---

## 22. Implementation Phases

### Phase 1: Local RAG Backend

Deliver:

1. FastAPI backend.
2. RAG corpus builder.
3. Local vector index.
4. Retrieval endpoint.
5. Chat endpoint.
6. Frontend chat panel.
7. Basic tests.

Exit condition:

Local chatbot answers questions and links to lessons.

### Phase 2: Gap Detection

Deliver:

1. Gap detector.
2. Gap record schema.
3. Gap persistence.
4. Gap API endpoints.
5. Gap UI.
6. Tests for missing-topic behavior.

Exit condition:

Weak or missing answers create reviewable gap records.

### Phase 3: GitHub Discovery

Deliver:

1. GitHub search query generator.
2. Candidate repo scoring.
3. Candidate repo intake.
4. External workspace.
5. Candidate lesson generation.
6. Attribution block.
7. Coordination TODO creation.
8. Tests with mocked GitHub data.

Exit condition:

A gap can produce staged candidate external lessons and TODOs.

### Phase 4: CI/CD Safety

Deliver:

1. PR validation workflow.
2. Staging deployment workflow.
3. Production approval workflow.
4. Smoke tests.
5. Artifact promotion.

Exit condition:

Production cannot be updated by an unverified direct push.

### Phase 5: AWS Deployment

Deliver:

1. AWS infrastructure.
2. Static site deployment.
3. Backend container deployment.
4. Vector/LLM adapters.
5. Smoke tests.
6. Deployment documentation.

Exit condition:

AWS staging and production both work.

### Phase 6: Azure Deployment

Deliver:

1. Azure infrastructure.
2. Static site deployment.
3. Backend container deployment.
4. Vector/LLM adapters.
5. Smoke tests.
6. Deployment documentation.

Exit condition:

Azure staging and production both work.

### Phase 7: GCP Deployment

Deliver:

1. GCP infrastructure.
2. Static site deployment.
3. Backend container deployment.
4. Vector/LLM adapters.
5. Smoke tests.
6. Deployment documentation.

Exit condition:

GCP staging and production both work.

---

## 23. Coding Agent Summary

Convert Lessons Hub into a static-plus-backend RAG application. Preserve the current Astro site, harvesting pipeline, validation pipeline, generated exports, and Pagefind search. Add a FastAPI backend that retrieves lesson chunks, generates grounded answers, and returns relevant lesson links. Add corpus gap detection for questions that cannot be answered from existing lessons. Add GitHub discovery for finding relevant external projects, pulling selected projects into a controlled workspace, generating candidate lessons, staging those lessons under `docs/candidate-lessons/external/`, and creating TODOs for owner coordination. Candidate external lessons must include source project links, attribution, and thank-you notes. Support local, AWS, Azure, and GCP deployments with staging and production separation.

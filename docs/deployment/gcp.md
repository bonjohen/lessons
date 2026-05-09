# GCP Deployment

## Architecture

- **Static site:** Cloud Storage + Cloud CDN (or Firebase Hosting)
- **Backend:** Cloud Run (FastAPI container)
- **Embeddings:** Vertex AI text-embedding-004
- **Chat model:** Vertex AI Gemini 1.5 Flash
- **Vector store:** Vertex AI Vector Search
- **CI/CD:** GitHub Actions with Workload Identity Federation (OIDC)

## Prerequisites

1. GCP project with Vertex AI API enabled
2. Workload Identity Federation configured for GitHub Actions
3. GitHub repository secrets configured (see below)

## Infrastructure Setup

Run the deployment script:

```bash
chmod +x infra/gcp/deploy.sh
./infra/gcp/deploy.sh staging <your-project-id> us-central1
```

This creates:
- Artifact Registry repository
- Cloud Storage bucket for static site
- Workload Identity Pool + Provider for GitHub Actions
- Service account with required IAM roles

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | GCP project ID |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity Provider resource name |
| `GCP_SERVICE_ACCOUNT` | Service account email |
| `ARTIFACT_REPO` | Artifact Registry repository name |
| `CLOUD_RUN_SERVICE` | Cloud Run service name |
| `GCS_BUCKET` | Cloud Storage bucket for static site |
| `BACKEND_URL` | Cloud Run service URL for smoke tests |
| `SITE_URL` | Static site URL for smoke tests |
| `LESSONS_REPO_TOKEN` | GitHub token for harvesting private repos |

## Deployment

Trigger via GitHub Actions:

```bash
gh workflow run deploy-gcp.yml -f environment=staging
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_PROFILE` | `local` | Set to `gcp` |
| `GCP_PROJECT_ID` | — | GCP project ID |
| `GCP_LOCATION` | `us-central1` | GCP region |
| `VERTEX_EMBED_MODEL` | `text-embedding-004` | Vertex AI embedding model |
| `VERTEX_CHAT_MODEL` | `gemini-1.5-flash-001` | Vertex AI chat model |
| `VERTEX_INDEX_ID` | — | Vertex AI Vector Search index resource name |
| `VERTEX_INDEX_ENDPOINT_ID` | — | Vertex AI Vector Search endpoint resource name |
| `VERTEX_DEPLOYED_INDEX_ID` | `lessons_chunks` | Deployed index ID |

## Cost Estimate (staging)

- Cloud Run (min instances = 0): ~$0-5/month (pay per request)
- Cloud Storage: ~$0.02/month
- Vertex AI Vector Search: ~$30/month (minimum 1 replica)
- Vertex AI Gemini: pay-per-token, ~$1-5/month for light usage
- Artifact Registry: ~$0.10/month
- **Total:** ~$31-40/month for staging

Note: Vertex AI Vector Search has a relatively high minimum cost. For cost-sensitive staging, consider using ChromaDB locally and only deploying Vector Search for production.

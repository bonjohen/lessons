#!/usr/bin/env bash
# Lessons Hub V2 — GCP Infrastructure Deployment
# Usage: ./deploy.sh <environment> <project-id> <region>

set -euo pipefail

ENV="${1:-staging}"
PROJECT="${2:?Usage: deploy.sh <env> <project-id> <region>}"
REGION="${3:-us-central1}"
PREFIX="lessons-hub-${ENV}"

echo "=== Deploying Lessons Hub V2 to GCP ($ENV) ==="
echo "Project: $PROJECT"
echo "Region: $REGION"

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  --project="$PROJECT"

# Create Artifact Registry repository
echo "Creating Artifact Registry..."
gcloud artifacts repositories create "${PREFIX}-repo" \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT" \
  --quiet 2>/dev/null || echo "Repository already exists"

# Create Cloud Storage bucket for static site
echo "Creating Cloud Storage bucket..."
BUCKET="${PREFIX}-static-${PROJECT}"
gsutil mb -p "$PROJECT" -l "$REGION" "gs://${BUCKET}" 2>/dev/null || echo "Bucket already exists"
gsutil web set -m index.html -e 404.html "gs://${BUCKET}"
gsutil iam ch allUsers:objectViewer "gs://${BUCKET}"

# Create Workload Identity Pool for GitHub Actions
echo "Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --project="$PROJECT" \
  --quiet 2>/dev/null || echo "Pool already exists"

gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --project="$PROJECT" \
  --quiet 2>/dev/null || echo "Provider already exists"

# Create service account for GitHub Actions
SA_NAME="${PREFIX}-github"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
echo "Creating service account: $SA_EMAIL"
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="Lessons Hub GitHub Actions ($ENV)" \
  --project="$PROJECT" \
  --quiet 2>/dev/null || echo "Service account already exists"

# Grant roles
for ROLE in \
  roles/run.developer \
  roles/artifactregistry.writer \
  roles/storage.objectAdmin \
  roles/aiplatform.user \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --quiet
done

echo ""
echo "=== Deployment Complete ==="
echo "Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT}/${PREFIX}-repo"
echo "Static bucket: gs://${BUCKET}"
echo "Service account: ${SA_EMAIL}"
echo ""
echo "Next steps:"
echo "1. Deploy Cloud Run service: gcloud run deploy ${PREFIX}-backend ..."
echo "2. Set up Vertex AI Vector Search index via console or API"
echo "3. Configure GitHub secrets (see docs/deployment/gcp.md)"

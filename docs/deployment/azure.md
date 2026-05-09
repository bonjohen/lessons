# Azure Deployment

## Architecture

- **Static site:** Azure Static Web Apps
- **Backend:** Azure Container Apps (FastAPI container)
- **Embeddings:** Azure OpenAI text-embedding-3-small
- **Chat model:** Azure OpenAI gpt-4o-mini
- **Vector store:** Azure AI Search
- **CI/CD:** GitHub Actions with OIDC (federated credentials)

## Prerequisites

1. Azure subscription with OpenAI service access
2. Azure AD app registration with federated credentials for GitHub Actions
3. GitHub repository secrets configured (see below)

## Infrastructure Setup

Deploy the Bicep template:

```bash
az deployment group create \
  --resource-group lessons-hub-staging \
  --template-file infra/azure/main.bicep \
  --parameters environment=staging
```

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Azure AD app registration client ID |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Resource group name |
| `ACR_NAME` | Azure Container Registry name |
| `ACR_LOGIN_SERVER` | ACR login server (e.g. `lhstagingacr.azurecr.io`) |
| `CONTAINER_APP_NAME` | Container Apps app name |
| `AZURE_STATIC_WEB_APPS_TOKEN` | Static Web Apps deployment token |
| `BACKEND_URL` | Backend URL for smoke tests |
| `SITE_URL` | Static Web App URL for smoke tests |
| `LESSONS_REPO_TOKEN` | GitHub token for harvesting private repos |

## Deployment

Trigger via GitHub Actions:

```bash
gh workflow run deploy-azure.yml -f environment=staging
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_PROFILE` | `local` | Set to `azure` |
| `AZURE_OPENAI_ENDPOINT` | — | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | — | Azure OpenAI API key |
| `AZURE_OPENAI_EMBED_DEPLOYMENT` | `text-embedding-3-small` | Embedding model deployment name |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | `gpt-4o-mini` | Chat model deployment name |
| `AZURE_OPENAI_API_VERSION` | `2024-06-01` | API version |
| `AZURE_SEARCH_ENDPOINT` | — | Azure AI Search endpoint |
| `AZURE_SEARCH_API_KEY` | — | Azure AI Search admin key |
| `AZURE_SEARCH_INDEX` | `lessons-chunks` | Search index name |

## Cost Estimate (staging)

- Container Apps (0.25 vCPU / 0.5 GB, scale to zero): ~$0-5/month
- Static Web Apps (Free tier): $0/month
- Azure AI Search (Free tier): $0/month
- Azure OpenAI: pay-per-token, ~$1-5/month for light usage
- Key Vault: ~$0.03/month
- **Total:** ~$1-10/month for staging

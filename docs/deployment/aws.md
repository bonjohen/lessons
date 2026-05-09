# AWS Deployment

## Architecture

- **Static site:** S3 + CloudFront
- **Backend:** ECS Fargate (FastAPI container)
- **Embeddings:** Amazon Titan Embed Text v2 via Bedrock
- **Chat model:** Claude 3 Haiku via Bedrock
- **Vector store:** OpenSearch Serverless
- **CI/CD:** GitHub Actions with OIDC authentication

## Prerequisites

1. AWS account with Bedrock model access enabled (Titan Embed, Claude 3 Haiku)
2. GitHub repository secrets configured (see below)
3. CloudFormation stack deployed

## Infrastructure Setup

Deploy the CloudFormation template:

```bash
aws cloudformation deploy \
  --template-file infra/aws/cloudformation.yml \
  --stack-name lessons-hub-staging \
  --parameter-overrides \
    Environment=staging \
    ContainerImage=INITIAL_PLACEHOLDER \
  --capabilities CAPABILITY_NAMED_IAM
```

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | GitHub Actions OIDC role ARN (from stack outputs) |
| `ECR_REPOSITORY` | ECR repository name |
| `S3_BUCKET_NAME` | Static site S3 bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID |
| `ECS_CLUSTER` | ECS cluster name |
| `ECS_SERVICE` | ECS service name |
| `BACKEND_URL` | Backend ALB URL for smoke tests |
| `SITE_URL` | CloudFront URL for smoke tests |
| `LESSONS_REPO_TOKEN` | GitHub token for harvesting private repos |

## Deployment

Trigger via GitHub Actions:

```bash
gh workflow run deploy-aws.yml -f environment=staging
```

## Environment Variables

The backend container uses these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_PROFILE` | `local` | Set to `aws` for Bedrock/OpenSearch |
| `AWS_REGION` | `us-east-1` | AWS region |
| `BEDROCK_EMBED_MODEL` | `amazon.titan-embed-text-v2:0` | Bedrock embedding model ID |
| `BEDROCK_CHAT_MODEL` | `anthropic.claude-3-haiku-20240307-v1:0` | Bedrock chat model ID |
| `OPENSEARCH_ENDPOINT` | — | OpenSearch Serverless endpoint |
| `OPENSEARCH_INDEX` | `lessons-chunks` | OpenSearch index name |

## Cost Estimate (staging)

- ECS Fargate (256 CPU / 512 MB): ~$9/month
- CloudFront + S3: ~$1/month (low traffic)
- OpenSearch Serverless: ~$25/month (minimum 2 OCU)
- Bedrock: pay-per-token, ~$1-5/month for light usage
- **Total:** ~$36-40/month for staging

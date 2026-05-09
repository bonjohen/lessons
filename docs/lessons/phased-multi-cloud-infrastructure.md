---
title: Phased Multi-Cloud Infrastructure as Code
summary: Three cloud stacks (AWS, Azure, GCP) built in separate phases with OIDC federation, avoiding cross-cloud coupling while sharing a common authentication pattern.
date: 2026-05-09
phase: deployment
lesson_type: deployment
status: active
tags: [aws, azure, gcp, oidc, infrastructure, ci-cd, cloudformation, bicep]
---

# Phased Multi-Cloud Infrastructure as Code

## The Lesson

When building infrastructure for multiple cloud providers, treat each provider as an independent phase with its own IaC tool, deployment workflow, and tests. The only shared pattern should be the authentication mechanism (OIDC federation) and the deployment contract (what the application expects). Attempting to unify IaC across providers with abstraction layers adds complexity without reducing work.

## Context

A static site with a RAG chatbot backend needed to deploy to AWS, Azure, and GCP alongside an existing GitHub Pages pipeline. Each cloud deployment runs the same Docker container for the backend and serves the same static assets for the frontend, but uses provider-native services for LLM inference and vector search. CI/CD runs on GitHub Actions. The goal was keyless deployments — no long-lived credentials stored in GitHub Secrets.

## What Happened

1. Built each cloud stack in a separate implementation phase (Phase 6: AWS, Phase 7: Azure, Phase 8: GCP), each with its own commit. This prevented cross-cloud coupling — a bug in the Azure Bicep template couldn't break the AWS CloudFormation stack.
2. **AWS (CloudFormation):** Full VPC with 4 subnets across 2 AZs, ALB, ECS Fargate, ECR with lifecycle policy, CloudFront with S3 origin and ALB backend origin (cache bypass for `/api/*`), IAM roles with Bedrock and OpenSearch policies, CloudWatch Logs. GitHub OIDC provider with subject constraint `repo:bonjohen/lessons:*`.
3. **Azure (Bicep):** Container Apps with Log Analytics, ACR, Static Web Apps (Free tier), Azure AI Search (Free tier), Azure OpenAI with two model deployments, Key Vault. Container Apps scale to zero in staging (`minReplicas: 0`), minimum 1 in production.
4. **GCP (shell script):** Enables APIs, creates Artifact Registry, Cloud Storage bucket, Workload Identity Pool/Provider, and a service account with granular IAM roles. Chose a shell script over Terraform because the resource set is small and the Workload Identity setup is imperative by nature.
5. All three stacks use environment-based parameters (staging vs. production) that control replica counts, log retention, and scaling behavior. The same template handles both environments.
6. All three CI/CD workflows (one per cloud) authenticate via OIDC/Workload Identity Federation — GitHub Actions presents a JWT, the cloud provider validates it against the configured trust relationship, and temporary credentials are issued. No static access keys or service account JSON files.
7. Each cloud's adapter tests run independently using `sys.modules.setdefault()` mocking — no cloud SDK is required in CI.

## Key Insights

- **OIDC federation is the right authentication pattern for CI/CD.** All three clouds support it, the setup is a one-time cost, and it eliminates credential rotation, secret sprawl, and the risk of leaked keys. The trust boundary is explicit: "only JWTs from GitHub Actions for repository X are accepted."

- **Each cloud's IaC tool is the right tool for that cloud.** CloudFormation for AWS, Bicep for Azure, and gcloud CLI for GCP. Cross-cloud abstraction tools (Pulumi, Terraform with multiple providers) add a translation layer that obscures provider-specific features. Since the application already uses provider-specific services (Bedrock vs. Azure OpenAI vs. Vertex AI), there's no benefit to abstracting the infrastructure.

- **Environment parameters should be baked into the template, not the pipeline.** A single CloudFormation template with `IsProduction` conditionals is better than two separate templates for staging and production. The template is the source of truth for what differs between environments.

- **Scale-to-zero in staging saves money without sacrificing testability.** Azure Container Apps supports `minReplicas: 0` natively. GCP Cloud Run does the same by default. AWS ECS Fargate requires at least one task but can use smaller CPU/memory in staging. The staging environment should exist permanently (for smoke tests after every push) but shouldn't cost anything when idle.

- **Phase isolation prevents cascading failures.** Building AWS, Azure, and GCP in separate phases with separate commits means a broken Azure deployment doesn't block AWS work. Each phase has its own tests. If one cloud's adapter or infrastructure template has issues, the others are unaffected.

## Applicability

This approach works when:
- You're deploying the same application to multiple clouds (not different applications to different clouds)
- Each cloud uses native services that can't be abstracted (managed AI, provider-specific vector stores)
- CI/CD is centralized on one platform (GitHub Actions) that all clouds can federate with

It does **not** apply when:
- You're using only cloud-agnostic services (Kubernetes everywhere) — then Terraform with one provider is simpler
- The application has no cloud-specific dependencies — a single Dockerfile with a multi-cloud Kubernetes deployment is sufficient
- You need to switch clouds frequently at runtime (that's a different problem — see the adapter pattern)

## Related Lessons

- [Adapter Pattern for Multi-Cloud Portability](adapter-pattern-for-multi-cloud.md) — the application-level complement to infrastructure-level multi-cloud
- [GitHub Pages Build Pipeline](github-pages-build-pipeline.md) — the original single-cloud deployment this expanded from

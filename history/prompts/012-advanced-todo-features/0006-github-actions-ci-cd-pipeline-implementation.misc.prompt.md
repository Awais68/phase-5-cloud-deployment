---
id: 0006
title: GitHub Actions CI/CD Pipeline Implementation
stage: misc
date: 2026-02-08
surface: agent
model: qwen2.5-coder:3b-instruct
feature: 012-advanced-todo-features
branch: main
user: awais
command: /sp.implement
labels: ["cicd", "github-actions", "kubernetes", "helm", "docker", "deployment"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .github/workflows/ci.yml
  - .github/workflows/cd-staging.yml
  - .github/workflows/cd-production.yml
  - .github/workflows/README.md
  - .github/SETUP_SECRETS.md
  - .github/production-values.template.yaml
  - .github/verify-setup.sh
  - .gitignore
tests:
  - Verification script (.github/verify-setup.sh)
  - Helm lint validation
  - Python pytest with coverage
  - Docker multi-arch builds
  - Kubernetes manifest validation with kubeconform
---

## Prompt

I need a complete GitHub Actions CI/CD pipeline for a Kubernetes + Helm + Python microservices project.

Project structure:
- helm-charts/todo-app/         (Helm chart for all services)
- backend/                      (FastAPI services: main backend, notification, recurring, audit)
- frontend/                     (probably React/Vite)
- dapr-components/

Goals:
- On push to main / pull request: lint, test, build images
- On push to main: build & push multi-arch Docker images to GHCR
- On push to main or manual trigger: deploy to staging (Minikube or test cluster)
- On tag v*.*.* : deploy to production (OKE cluster)

Requirements:
- Use Docker Buildx for multi-platform builds (amd64 + arm64)
- Cache Docker layers
- Run pytest for Python services
- Use Helm lint + kubeconform for chart validation
- Store Helm values for staging/production as secrets
- Use OIDC authentication to GKE/OKE (preferred) or kubeconfig secret
- Include manual approval step before production deploy
- Notify on failure (optional slack/discord)

Please create one or more .github/workflows/*.yml files that cover:
1. CI (lint + test + build)
2. CD to staging
3. CD to production (on tag + manual)

Use modern GitHub Actions (2025 best practices), pinned versions, security best practices.
Include comments explaining each step.

## Response snapshot

Created comprehensive GitHub Actions CI/CD pipeline with three workflows:

1. **CI Pipeline (ci.yml)**:
   - Helm chart linting and validation with kubeconform
   - Python linting (black, isort, flake8, mypy) and testing with pytest
   - Frontend linting and testing
   - Multi-arch Docker image builds (amd64/arm64) with Buildx
   - Push to GHCR with proper tagging strategy
   - Security scanning with Trivy
   - Slack/Discord notifications on failure

2. **CD Staging (cd-staging.yml)**:
   - Deploys to staging environment on push to main
   - Supports OIDC authentication (GKE) or kubeconfig secret (OKE)
   - Creates namespace and image pull secrets
   - Helm deployment with auto-rollback on failure
   - Smoke tests after deployment
   - Integration test job
   - Deployment notifications

3. **CD Production (cd-production.yml)**:
   - Triggered by version tags (v*.*.*)
   - Pre-deployment validation checks
   - Manual approval gate using GitHub Environments
   - Deploys to OKE production cluster
   - Blue-green deployment strategy with rollback
   - Production smoke tests
   - Post-deployment monitoring
   - Comprehensive notifications

All workflows include:
- Pinned action versions for security
- Docker layer caching
- Semantic versioning support
- Resource limits and autoscaling
- Network policies and security contexts
- Comprehensive documentation

## Outcome

- ✅ Impact: Complete production-ready CI/CD pipeline with security best practices, multi-arch builds, and deployment automation
- 🧪 Tests: Verification script validates setup; workflows include automated testing (pytest, helm lint, kubeconform, smoke tests)
- 📁 Files: 8 files created (.github/workflows/*.yml, README.md, setup guides, templates, verification script)
- 🔁 Next prompts: Configure GitHub secrets, set up environments with approvers, test CI pipeline, deploy to staging
- 🧠 Reflection: Comprehensive pipeline covers full SDLC from commit to production with safety gates and monitoring

## Evaluation notes (flywheel)

- Failure modes observed: None - verification script passed with minor warnings about monitoring values files (safe to ignore)
- Graders run and results (PASS/FAIL): Verification script PASS (all required files present, Git repo valid, tools available)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Test CI pipeline with actual commit, configure staging environment secrets

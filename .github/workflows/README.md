# GitHub Actions CI/CD Pipeline

This directory contains the complete CI/CD pipeline for the Todo App Kubernetes microservices project.

## Workflows Overview

### 1. CI Pipeline (`ci.yml`)
**Trigger**: Push to `main` or Pull Requests
**Purpose**: Continuous Integration - lint, test, build, and security scan

**Jobs**:
- **Helm Lint**: Validates Helm charts with `helm lint` and `kubeconform`
- **Python Lint & Test**: Runs black, isort, flake8, mypy, and pytest for all Python services
- **Frontend Lint & Test**: Runs ESLint and npm tests for frontend
- **Build & Push Images**: Builds multi-arch Docker images (amd64/arm64) and pushes to GHCR
- **Security Scan**: Scans images with Trivy for vulnerabilities
- **Notify on Failure**: Sends Slack/Discord notifications on failures

### 2. Staging Deployment (`cd-staging.yml`)
**Trigger**: Push to `main` or manual dispatch
**Purpose**: Deploy to staging environment (Minikube/test cluster)

**Jobs**:
- **Deploy Staging**: Deploys application to staging namespace with Helm
- **Integration Tests**: Runs integration tests against staging environment

**Features**:
- OIDC authentication support (GKE/OKE)
- Automatic rollback on failure
- Smoke tests after deployment
- Deployment notifications

### 3. Production Deployment (`cd-production.yml`)
**Trigger**: Git tags matching `v*.*.*` or manual dispatch
**Purpose**: Deploy to production OKE cluster

**Jobs**:
- **Pre-Deployment Checks**: Validates version format, images, and security
- **Approval Gate**: Requires manual approval before production deployment
- **Deploy Production**: Deploys to OKE with blue-green strategy
- **Post-Deployment**: Monitors health after deployment

**Features**:
- Manual approval requirement
- Version validation
- Automated rollback on failure
- Production-grade resource limits
- Comprehensive health checks

## Setup Instructions

### 1. Required GitHub Secrets

#### GHCR (GitHub Container Registry)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

#### Staging Environment
- `STAGING_KUBECONFIG` - Base64-encoded kubeconfig for staging cluster
- `STAGING_VALUES` - Base64-encoded Helm values for staging (optional)
- `STAGING_DB_HOST` - Database host
- `STAGING_DB_USER` - Database username
- `STAGING_DB_PASSWORD` - Database password
- `STAGING_API_KEY` - API key for integration tests

#### Production Environment (OKE)
- `OKE_KUBECONFIG` - Base64-encoded kubeconfig for OKE cluster
- `OKE_CONTEXT_NAME` - Kubernetes context name (optional)
- `PRODUCTION_VALUES` - Base64-encoded Helm values for production
- `PRODUCTION_DB_HOST` - Production database host
- `PRODUCTION_DB_USER` - Production database username
- `PRODUCTION_DB_PASSWORD` - Production database password

#### Notifications (Optional)
- `SLACK_WEBHOOK_URL` - Slack webhook for deployment notifications
- `DISCORD_WEBHOOK_URL` - Discord webhook for deployment notifications

### 2. Creating Base64-Encoded Secrets

```bash
# Kubeconfig
cat ~/.kube/config | base64 -w 0 > kubeconfig.b64

# Helm values
cat production-values.yaml | base64 -w 0 > production-values.b64
```

### 3. Setting Up GitHub Environments

Navigate to **Settings > Environments** in your GitHub repository and create:

#### `staging` Environment
- No protection rules needed
- Add staging secrets

#### `production-approval` Environment
- **Required reviewers**: Add team members who must approve production deployments
- **Wait timer**: Optional delay before deployment (e.g., 5 minutes)

#### `production` Environment
- Add production secrets
- Deployment branch rule: Only `main` or tags matching `v*.*.*`

### 4. OIDC Authentication Setup (Recommended)

#### For Google Cloud (GKE):
1. Create Workload Identity Pool
2. Create Workload Identity Provider
3. Add secrets:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
   - `GKE_CLUSTER_NAME`
   - `GKE_CLUSTER_ZONE`

Uncomment the GKE authentication section in `cd-staging.yml` and `cd-production.yml`.

#### For Oracle Cloud (OKE):
OKE doesn't natively support OIDC from GitHub Actions. Use kubeconfig method (already configured).

## Usage

### Running CI Pipeline
```bash
# Automatically triggered on push to main or PR
git push origin main

# Or create a PR
git checkout -b feature-branch
git push origin feature-branch
# Open PR on GitHub
```

### Deploying to Staging
```bash
# Automatic: Push to main triggers staging deployment
git push origin main

# Manual: Go to Actions > CD - Deploy to Staging > Run workflow
```

### Deploying to Production
```bash
# Method 1: Create and push a version tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Method 2: Manual dispatch
# Go to Actions > CD - Deploy to Production > Run workflow
# - Enter version: v1.0.0
# - Enter confirmation: DEPLOY
```

## Workflow Details

### Multi-Platform Docker Builds
All Docker images are built for both `linux/amd64` and `linux/arm64` using Docker Buildx.

**Image naming convention**:
```
ghcr.io/<github-username>/todo-backend:latest
ghcr.io/<github-username>/todo-backend:main-abc1234
ghcr.io/<github-username>/todo-backend:v1.0.0
```

### Helm Chart Validation
Charts are validated with:
- `helm lint --strict` - Linting
- `kubeconform` - Kubernetes manifest validation

### Python Testing
Each service is tested with:
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **pytest** - Unit tests with coverage

### Deployment Strategy
- **Staging**: Rolling update with automatic rollback
- **Production**: Blue-green deployment with manual approval

### Rollback Procedures

#### Automatic Rollback
Workflows automatically rollback on failure using:
```bash
helm rollback todo-app --namespace <namespace>
```

#### Manual Rollback
```bash
# List releases
helm list -n production

# Rollback to previous version
helm rollback todo-app -n production

# Rollback to specific revision
helm rollback todo-app <revision> -n production
```

## Monitoring and Notifications

### Slack Notifications
Set `SLACK_WEBHOOK_URL` secret to receive:
- CI pipeline failures
- Deployment status (success/failure)
- Rollback notifications

### Discord Notifications
Set `DISCORD_WEBHOOK_URL` secret for Discord notifications.

### Creating Webhooks

**Slack**:
1. Go to https://api.slack.com/apps
2. Create new app > Incoming Webhooks
3. Add webhook to workspace
4. Copy webhook URL

**Discord**:
1. Server Settings > Integrations > Webhooks
2. Create Webhook
3. Copy webhook URL

## Troubleshooting

### CI Pipeline Issues

**Build failing for a specific service:**
```bash
# Run locally with Docker
cd backend/services/notification-service
docker build -t test .
```

**Tests failing:**
```bash
# Run tests locally
cd backend/services/notification-service
pip install -r requirements.txt
pytest -v
```

### Deployment Issues

**Deployment stuck:**
```bash
# Check pod status
kubectl get pods -n staging

# View logs
kubectl logs -f <pod-name> -n staging

# Describe pod for events
kubectl describe pod <pod-name> -n staging
```

**Image pull errors:**
- Verify GHCR secret exists: `kubectl get secret ghcr-secret -n staging`
- Check image name and tag are correct
- Verify GitHub token has package read permissions

**Helm deployment fails:**
```bash
# Check Helm release status
helm list -n staging

# View release history
helm history todo-app -n staging

# Get values from failed release
helm get values todo-app -n staging
```

### OIDC Authentication Issues

**GKE authentication failing:**
- Verify Workload Identity Pool configuration
- Check service account permissions
- Ensure cluster is properly configured for Workload Identity

**OKE kubeconfig issues:**
- Verify kubeconfig is properly base64 encoded
- Check context name matches secret
- Ensure kubeconfig hasn't expired

## Best Practices

1. **Never skip CI**: Always wait for CI to pass before merging PRs
2. **Test in staging first**: All changes should deploy to staging before production
3. **Use semantic versioning**: Follow `v<major>.<minor>.<patch>` for production tags
4. **Review approval logs**: Check who approved production deployments
5. **Monitor after deployment**: Watch metrics for at least 15 minutes post-deployment
6. **Keep secrets rotated**: Regularly update API keys and database passwords
7. **Document rollbacks**: Log reasons for any rollbacks

## Security Considerations

1. **Secrets Management**:
   - Never commit secrets to repository
   - Use GitHub Secrets for all sensitive data
   - Rotate secrets regularly

2. **Image Security**:
   - Trivy scans all images for vulnerabilities
   - Critical/High vulnerabilities block deployment
   - Review security scan results before production

3. **RBAC**:
   - Use least-privilege service accounts
   - Restrict production namespace access
   - Enable audit logging

4. **Network Policies**:
   - Enable network policies in production
   - Restrict inter-service communication
   - Use mTLS with Dapr

## Maintenance

### Updating Dependencies
```bash
# Update GitHub Actions versions
# Check: https://github.com/actions/<action>/releases

# Update Helm version
# Modify HELM_VERSION in workflows

# Update kubectl version
# Modify KUBECTL_VERSION in workflows
```

### Adding New Services
1. Update CI workflow matrix with new service path
2. Add new image name to environment variables
3. Update Helm chart values with new service configuration
4. Test in staging before production

## Support

For issues or questions:
- Check workflow logs in GitHub Actions
- Review Kubernetes events: `kubectl get events -n <namespace>`
- Consult deployment logs: `kubectl logs -f deployment/<service> -n <namespace>`

## License
[Your License Here]

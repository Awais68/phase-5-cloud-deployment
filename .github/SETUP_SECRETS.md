# GitHub Secrets Setup Guide

This guide will help you configure all required GitHub secrets for the CI/CD pipeline.

## Prerequisites

- GitHub repository admin access
- Access to Kubernetes clusters (staging and production)
- Database credentials
- (Optional) Slack/Discord webhook URLs

## Step-by-Step Setup

### 1. Navigate to GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Navigate to **Secrets and variables** > **Actions**
4. Click **New repository secret**

### 2. Staging Environment Secrets

#### STAGING_KUBECONFIG

Create base64-encoded kubeconfig:

```bash
# For Minikube (local staging)
kubectl config view --minify --flatten > staging-kubeconfig.yaml
cat staging-kubeconfig.yaml | base64 -w 0 > staging-kubeconfig.b64

# Copy the contents of staging-kubeconfig.b64
cat staging-kubeconfig.b64

# Add as secret: STAGING_KUBECONFIG
```

**Alternative for cloud clusters:**
```bash
# Export specific context
kubectl config use-context <staging-context>
kubectl config view --minify --flatten | base64 -w 0
```

#### STAGING_DB_HOST
```
Example: ep-cool-snow-123456.us-east-1.aws.neon.tech
```

#### STAGING_DB_USER
```
Example: staging_user
```

#### STAGING_DB_PASSWORD
```
Example: strong_password_here
```

#### STAGING_API_KEY (Optional - for integration tests)
```
Example: staging_test_api_key_12345
```

#### STAGING_VALUES (Optional - custom Helm values)

If you want to override Helm values:

```bash
# Create staging-values.yaml with your custom configuration
cat staging-values.yaml | base64 -w 0 > staging-values.b64

# Copy contents and add as secret: STAGING_VALUES
cat staging-values.b64
```

### 3. Production Environment Secrets

#### OKE_KUBECONFIG

For Oracle Cloud OKE:

```bash
# Download kubeconfig from OCI Console or generate using OCI CLI
# Navigate to: Compute > Kubernetes Clusters (OKE) > Click cluster > Access Cluster

# Using OCI CLI:
oci ce cluster create-kubeconfig \
  --cluster-id <cluster-ocid> \
  --file production-kubeconfig.yaml \
  --region <region> \
  --token-version 2.0.0

# Encode for GitHub secret
cat production-kubeconfig.yaml | base64 -w 0 > production-kubeconfig.b64
cat production-kubeconfig.b64

# Add as secret: OKE_KUBECONFIG
```

#### OKE_CONTEXT_NAME (Optional)

Get context name from kubeconfig:

```bash
grep "current-context:" production-kubeconfig.yaml
```

Example: `context-c<cluster-id>`

#### PRODUCTION_DB_HOST
```
Example: ep-production-123456.us-east-1.aws.neon.tech
```

#### PRODUCTION_DB_USER
```
Example: production_user
```

#### PRODUCTION_DB_PASSWORD
```
Example: very_strong_production_password
```

#### PRODUCTION_VALUES (Optional)

```bash
# Create production-values.yaml with production configuration
cat production-values.yaml | base64 -w 0 > production-values.b64
cat production-values.b64

# Add as secret: PRODUCTION_VALUES
```

### 4. Notification Secrets (Optional)

#### SLACK_WEBHOOK_URL

**Create Slack Webhook:**

1. Go to https://api.slack.com/apps
2. Click **Create New App** > **From scratch**
3. Name: "GitHub Actions CI/CD"
4. Select workspace
5. Navigate to **Incoming Webhooks**
6. Activate Incoming Webhooks: **On**
7. Click **Add New Webhook to Workspace**
8. Select channel (e.g., #deployments)
9. Copy webhook URL

Example:
```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

Add as secret: `SLACK_WEBHOOK_URL`

#### DISCORD_WEBHOOK_URL

**Create Discord Webhook:**

1. Open Discord Server
2. Go to **Server Settings** > **Integrations**
3. Click **Webhooks** > **New Webhook**
4. Name: "GitHub CI/CD"
5. Select channel (e.g., #deployments)
6. Click **Copy Webhook URL**

Example:
```
https://discord.com/api/webhooks/123456789012345678/abcdefghijklmnopqrstuvwxyz
```

Add as secret: `DISCORD_WEBHOOK_URL`

### 5. GitHub Container Registry (GHCR)

**No setup needed!**

`GITHUB_TOKEN` is automatically provided by GitHub Actions with the necessary permissions to push to GHCR.

**Verify package permissions:**
1. Go to repository **Settings** > **Actions** > **General**
2. Scroll to **Workflow permissions**
3. Ensure **Read and write permissions** is selected

### 6. Environment Setup

#### Create `staging` Environment

1. Go to **Settings** > **Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**
5. (Optional) Add protection rules:
   - Required reviewers: none (for auto-deploy)
   - Deployment branches: `main` only

#### Create `production-approval` Environment

1. Create new environment: `production-approval`
2. **Required reviewers**: Add team members who must approve
   - Example: Add yourself and 1-2 team leads
3. **Wait timer**: (Optional) Set to 5 minutes
4. **Deployment branches**: `main` or tags matching `v*.*.*`

#### Create `production` Environment

1. Create new environment: `production`
2. Add all production secrets here (or use repository secrets)
3. **Deployment branches**: Only tags matching `v*.*.*`

## Verification

### Test Staging Deployment

```bash
# Trigger CI/CD by pushing to main
git checkout main
git pull
echo "# Test" >> README.md
git add README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main

# Watch in GitHub Actions tab
```

### Test Production Deployment

```bash
# Create a version tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Go to GitHub Actions > CD - Deploy to Production
# Wait for approval gate
# Approve deployment
# Watch deployment progress
```

## Troubleshooting

### Secret Not Found Error

```
Error: Secret STAGING_KUBECONFIG not found
```

**Solution:**
- Verify secret name matches exactly (case-sensitive)
- Check secret is added to correct environment
- Repository secrets are available in all environments
- Environment secrets override repository secrets

### Base64 Decoding Error

```
Error: base64: invalid input
```

**Solution:**
```bash
# Re-encode without line wrapping
cat file.yaml | base64 -w 0 > file.b64

# Verify decoding works
cat file.b64 | base64 -d
```

### Kubeconfig Authentication Failed

```
Error: Unable to connect to the server: x509: certificate signed by unknown authority
```

**Solutions:**

1. **Include full certificate chain:**
```bash
kubectl config view --minify --flatten --raw > kubeconfig-full.yaml
```

2. **For OKE, regenerate token:**
```bash
oci ce cluster create-kubeconfig \
  --cluster-id <cluster-ocid> \
  --file kubeconfig.yaml \
  --token-version 2.0.0
```

3. **Verify kubeconfig works locally:**
```bash
KUBECONFIG=./kubeconfig.yaml kubectl get nodes
```

### GHCR Push Permission Denied

```
Error: denied: permission_denied: write_package
```

**Solution:**
1. Go to **Settings** > **Actions** > **General**
2. **Workflow permissions** > Select **Read and write permissions**
3. Click **Save**

### Helm Deployment Timeout

```
Error: timed out waiting for the condition
```

**Solutions:**
1. Increase timeout in workflow: `--timeout 15m`
2. Check pod status: `kubectl describe pod <pod-name> -n <namespace>`
3. Check events: `kubectl get events -n <namespace>`
4. Review pod logs: `kubectl logs <pod-name> -n <namespace>`

## Security Best Practices

1. **Rotate Secrets Regularly**
   - Database passwords: Every 90 days
   - API keys: Every 90 days
   - Kubeconfig tokens: Every 180 days

2. **Least Privilege**
   - Use service accounts with minimal permissions
   - Don't use admin kubeconfig in CI/CD
   - Restrict namespace access

3. **Audit Logging**
   - Monitor secret access in GitHub audit log
   - Enable Kubernetes audit logging
   - Review deployment logs regularly

4. **Secret Scanning**
   - Enable GitHub secret scanning
   - Use pre-commit hooks to prevent secret commits
   - Scan Docker images for embedded secrets

## Maintenance

### Updating Secrets

```bash
# Get current value (if needed)
# Navigate to Settings > Secrets > Click secret name

# Update secret
# Click "Update secret"
# Paste new value
# Click "Update secret"
```

### Removing Secrets

```bash
# Navigate to Settings > Secrets
# Click secret name
# Click "Remove secret"
# Confirm removal
```

## Next Steps

After setting up secrets:

1. ✅ Review `.github/workflows/README.md` for workflow details
2. ✅ Test CI pipeline with a test commit
3. ✅ Test staging deployment
4. ✅ Configure monitoring and alerting
5. ✅ Document runbooks for common issues
6. ✅ Test production deployment process in non-peak hours

## Support

For issues:
- Check GitHub Actions logs
- Review this guide
- Consult `.github/workflows/README.md`
- Open an issue in the repository

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Kubernetes Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
- [Helm Documentation](https://helm.sh/docs/)
- [OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)

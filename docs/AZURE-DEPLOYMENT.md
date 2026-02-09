# Azure AKS Deployment Guide

This guide covers deploying the Todo Application to Azure Kubernetes Service (AKS).

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Helm 3.x installed
- kubectl installed
- Docker installed (for building images locally)

## Quick Start

### 1. Provision Azure Infrastructure

Run the automated setup script:

```bash
# Set your configuration
export RESOURCE_GROUP="todo-app-rg"
export LOCATION="eastus"
export AKS_CLUSTER_NAME="todo-app-aks"
export ACR_NAME="todoappacr"

# Run setup script
./scripts/azure-setup.sh
```

This creates:
- Azure Kubernetes Service (AKS) cluster
- Azure Container Registry (ACR)
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Event Hubs (Kafka-compatible)
- Azure Key Vault
- Application Insights
- NGINX Ingress Controller
- cert-manager for TLS

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository:

| Secret Name | Description |
|-------------|-------------|
| `AZURE_CREDENTIALS` | Service Principal JSON |
| `AZURE_RESOURCE_GROUP` | Resource group name |
| `AKS_CLUSTER_NAME` | AKS cluster name |
| `ACR_NAME` | ACR name (without .azurecr.io) |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |
| `AZURE_DATABASE_URL` | PostgreSQL connection string |
| `AZURE_REDIS_URL` | Redis connection string |
| `AZURE_EVENTHUB_CONNECTION` | Event Hubs connection string |
| `JWT_SECRET` | JWT signing secret |
| `OPENAI_API_KEY` | OpenAI API key |

#### Create Service Principal

```bash
az ad sp create-for-rbac \
  --name "todo-app-github" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
  --sdk-auth
```

Copy the JSON output to `AZURE_CREDENTIALS` secret.

### 3. Build and Push Images

#### Option A: Local Build

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build and push images
docker build -t $ACR_NAME.azurecr.io/todo-backend:v1.0.0 ./backend/hf_deployment
docker push $ACR_NAME.azurecr.io/todo-backend:v1.0.0

docker build -t $ACR_NAME.azurecr.io/todo-frontend:v1.0.0 ./frontend
docker push $ACR_NAME.azurecr.io/todo-frontend:v1.0.0

# Microservices
docker build -t $ACR_NAME.azurecr.io/notification-service:v1.0.0 ./backend/services/notification-service
docker push $ACR_NAME.azurecr.io/notification-service:v1.0.0

docker build -t $ACR_NAME.azurecr.io/recurring-task-service:v1.0.0 ./backend/services/recurring-task-service
docker push $ACR_NAME.azurecr.io/recurring-task-service:v1.0.0

docker build -t $ACR_NAME.azurecr.io/audit-log-service:v1.0.0 ./backend/services/audit-log-service
docker push $ACR_NAME.azurecr.io/audit-log-service:v1.0.0
```

#### Option B: GitHub Actions (Automated)

Push to `main` branch to trigger automated build and deployment.

### 4. Deploy with Helm

```bash
# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME

# Create namespace
kubectl create namespace production

# Create ACR pull secret
kubectl create secret docker-registry acr-secret \
  --namespace production \
  --docker-server=$ACR_NAME.azurecr.io \
  --docker-username=$ACR_USERNAME \
  --docker-password=$ACR_PASSWORD

# Create application secrets
kubectl create secret generic azure-secrets \
  --namespace production \
  --from-literal=database-url="$AZURE_DATABASE_URL" \
  --from-literal=redis-url="$AZURE_REDIS_URL" \
  --from-literal=eventhub-connection="$AZURE_EVENTHUB_CONNECTION" \
  --from-literal=jwt-secret="$JWT_SECRET"

# Update Helm dependencies
cd helm-charts/todo-app
helm dependency update

# Deploy
helm upgrade --install todo-app . \
  --namespace production \
  --values values-azure.yaml \
  --set global.registry=$ACR_NAME.azurecr.io \
  --set services.frontend.image=$ACR_NAME.azurecr.io/todo-frontend:v1.0.0 \
  --set services.backend.image=$ACR_NAME.azurecr.io/todo-backend:v1.0.0 \
  --set services.notification.image=$ACR_NAME.azurecr.io/notification-service:v1.0.0 \
  --set services.recurring.image=$ACR_NAME.azurecr.io/recurring-task-service:v1.0.0 \
  --set services.audit.image=$ACR_NAME.azurecr.io/audit-log-service:v1.0.0 \
  --wait
```

### 5. Configure DNS

Get the Ingress IP:

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

Create DNS records:
- `todo-app.yourdomain.com` → Ingress IP
- `api.todo-app.yourdomain.com` → Ingress IP

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods -n production

# Check services
kubectl get svc -n production

# Check ingress
kubectl get ingress -n production

# Check HPA
kubectl get hpa -n production

# View logs
kubectl logs -n production deployment/todo-app-backend -f
```

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         Azure DNS Zone              │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │    Azure Application Gateway        │
                    │    or NGINX Ingress + LB            │
                    └──────────────┬──────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        │              Azure Kubernetes Service               │
        │                          │                          │
        │  ┌───────────────────────┼───────────────────────┐  │
        │  │                       │                       │  │
        │  │  ┌─────────┐    ┌─────┴─────┐   ┌──────────┐  │  │
        │  │  │Frontend │    │  Backend  │   │Microservs│  │  │
        │  │  │ (Next.js)│   │ (FastAPI) │   │(Python)  │  │  │
        │  │  └─────────┘    └───────────┘   └──────────┘  │  │
        │  │                       │                       │  │
        │  └───────────────────────┼───────────────────────┘  │
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                  Azure Services                     │
        │                          │                          │
        │  ┌─────────────┐  ┌──────┴─────┐  ┌──────────────┐  │
        │  │ PostgreSQL  │  │   Redis    │  │ Event Hubs   │  │
        │  │ Flexible    │  │   Cache    │  │ (Kafka)      │  │
        │  └─────────────┘  └────────────┘  └──────────────┘  │
        │                                                     │
        │  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  │
        │  │ Key Vault   │  │ App        │  │ Log          │  │
        │  │             │  │ Insights   │  │ Analytics    │  │
        │  └─────────────┘  └────────────┘  └──────────────┘  │
        │                                                     │
        └─────────────────────────────────────────────────────┘
```

## Cost Estimation (Monthly)

| Service | SKU | Estimated Cost |
|---------|-----|----------------|
| AKS | 3x D4s_v3 nodes | ~$450 |
| PostgreSQL | D2s_v3 (HA) | ~$200 |
| Redis | Premium P1 | ~$250 |
| Event Hubs | Standard (2 TU) | ~$50 |
| ACR | Premium | ~$50 |
| Application Gateway | WAF_v2 | ~$350 |
| **Total** | | **~$1,350/month** |

For development/testing, use:
- AKS: 2x B2s nodes (~$60)
- PostgreSQL: Burstable B1ms (~$15)
- Redis: Basic C0 (~$15)
- Event Hubs: Basic (~$10)
- **Dev Total**: ~$100/month

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'
```

### Image pull errors

```bash
# Verify ACR secret
kubectl get secret acr-secret -n production -o yaml

# Test ACR access
az acr repository list --name $ACR_NAME
```

### Database connection issues

```bash
# Test connection from a pod
kubectl run test-db --rm -it --image=postgres:15 -- psql "$AZURE_DATABASE_URL"
```

### Ingress not working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress status
kubectl describe ingress todo-app-ingress -n production
```

## Cleanup

To delete all Azure resources:

```bash
# Delete resource group (removes everything)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

## Support

For issues or questions:
- Check GitHub Issues
- Review Azure documentation
- Contact the development team

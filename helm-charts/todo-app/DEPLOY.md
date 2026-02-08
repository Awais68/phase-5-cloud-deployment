# Todo App - Minikube Deployment Guide

## Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
./deploy-minikube.sh
```

This script automatically:
- Installs Helm if missing
- Starts Minikube
- Enables required addons
- Updates ingress with Minikube IP
- Deploys all services
- Shows access URLs

### Option 2: Manual Deployment

```bash
# 1. Start Minikube
minikube start --driver=docker --cpus=4 --memory=8192

# 2. Enable addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable registry

# 3. Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# 4. Update dev-values.yaml
# Edit dev-values.yaml and replace IP addresses with $MINIKUBE_IP

# 5. Create namespace
kubectl create namespace dev

# 6. Install Helm chart
helm install todo-app . \
  --namespace dev \
  --values dev-values.yaml
```

## Access the Application

After deployment:

```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Access via browser
echo "Frontend: http://app.$MINIKUBE_IP.nip.io"
echo "Backend: http://api.$MINIKUBE_IP.nip.io"
```

Or use port-forwarding:

```bash
# Frontend
kubectl port-forward -n dev svc/todo-app-frontend 3000:3000

# Backend
kubectl port-forward -n dev svc/todo-app-backend 8000:8000

# Then access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs
```

## Verify Deployment

```bash
# Check pods
kubectl get pods -n dev

# Check services
kubectl get svc -n dev

# Check ingress
kubectl get ingress -n dev

# View logs
kubectl logs -f -n dev deployment/todo-app-frontend
kubectl logs -f -n dev deployment/todo-app-backend
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n dev
kubectl logs <pod-name> -n dev
```

### Ingress not working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Verify ingress
kubectl describe ingress -n dev
```

### Image pull errors

```bash
# Check if images exist locally
docker images | grep todo

# Tag and push to local registry
docker tag your-image:tag localhost:5000/your-image:tag
docker push localhost:5000/your-image:tag
```

## Cleanup

```bash
# Automated cleanup
./cleanup.sh

# Manual cleanup
helm uninstall todo-app -n dev
kubectl delete namespace dev
```

## Services

- **Frontend** - Next.js PWA (Port 3000)
- **Backend** - FastAPI (Port 8000)
- **Notification Service** - Event-driven notifications (Port 8000)
- **Recurring Task Service** - Scheduled tasks (Port 8000)
- **Audit Log Service** - Audit trail (Port 8000)

## Configuration

Key configuration file: `dev-values.yaml`

```yaml
global:
  registry: localhost:5000
  ingress:
    enabled: true
    hosts:
      app: "app.<minikube-ip>.nip.io"
      api: "api.<minikube-ip>.nip.io"

replicaCount: 1  # Single replica for dev

dapr:
  enabled: true  # Dapr sidecars
```

## Next Steps

1. Build your Docker images
2. Tag and push to Minikube registry
3. Run `./deploy-minikube.sh`
4. Access the application via the provided URLs

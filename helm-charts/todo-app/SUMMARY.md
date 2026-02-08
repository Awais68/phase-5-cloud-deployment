# Helm Chart Fixes and Deployment Summary

## Issues Fixed

### 1. Chart.yaml
- ✅ Removed duplicate dependencies (postgresql, redis, kafka were listed twice)
- ✅ Set specific dependency versions instead of wildcards:
  - postgresql: 12.12.10
  - redis: 17.15.2
  - kafka: 22.1.5
  - common: 2.20.0

### 2. dev-values.yaml
- ✅ Fixed image references (removed invalid `${global.registry}` syntax)
- ✅ Added explicit dependency disabling (postgresql, redis, kafka disabled for Minikube)
- ✅ Configured for Minikube environment with resource limits

### 3. Templates
- ✅ Removed invalid configmap checksum annotation from deployment-frontend.yaml
- ✅ All service and deployment templates validated

## Files Created

### 1. deploy-minikube.sh
Automated deployment script that:
- Checks and installs prerequisites (Helm)
- Starts Minikube if not running
- Enables required addons (ingress, metrics-server, registry)
- Updates ingress hosts with actual Minikube IP
- Creates namespace and deploys the chart
- Shows access URLs and useful commands

### 2. cleanup.sh
Quick cleanup script to remove all deployed resources:
- Uninstalls Helm release
- Deletes namespace

### 3. DEPLOY.md
Comprehensive deployment guide with:
- Automated and manual deployment options
- Access instructions (ingress and port-forward)
- Verification commands
- Troubleshooting tips
- Service overview

## Current Chart Structure

```
todo-app/
├── Chart.yaml                    # Fixed: removed duplicates, set versions
├── Chart.lock                    # Dependency lock
├── dev-values.yaml              # Fixed: proper image refs, disabled deps
├── values-dev.yaml              # Alternative dev config
├── templates/
│   ├── _helpers.tpl             # Helper functions
│   ├── deployment-*.yaml        # 5 microservices
│   ├── service-*.yaml           # 5 services
│   ├── ingress.yaml             # Ingress configuration
│   ├── hpa.yaml                 # Horizontal Pod Autoscaler
│   └── NOTES.txt                # Post-install notes
├── deploy-minikube.sh           # ✅ NEW: Automated deployment
├── cleanup.sh                   # ✅ NEW: Cleanup script
└── DEPLOY.md                    # ✅ NEW: Deployment guide
```

## Deployment Steps

### Quick Start
```bash
# Make scripts executable
chmod +x deploy-minikube.sh cleanup.sh

# Deploy everything
./deploy-minikube.sh
```

### Manual Steps
```bash
# 1. Install Helm (if not present)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 2. Start Minikube
minikube start --driver=docker --cpus=4 --memory=8192

# 3. Enable addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable registry

# 4. Get Minikube IP and update dev-values.yaml
MINIKUBE_IP=$(minikube ip)
sed -i "s/192.168.49.2/$MINIKUBE_IP/g" dev-values.yaml

# 5. Build dependencies (optional, only if enabled)
helm dependency build .

# 6. Deploy
helm install todo-app . \
  --namespace dev \
  --create-namespace \
  --values dev-values.yaml
```

## Access URLs

After deployment:
```bash
MINIKUBE_IP=$(minikube ip)
echo "Frontend: http://app.$MINIKUBE_IP.nip.io"
echo "Backend: http://api.$MINIKUBE_IP.nip.io"
```

Or port-forward:
```bash
kubectl port-forward -n dev svc/todo-app-frontend 3000:3000
kubectl port-forward -n dev svc/todo-app-backend 8000:8000
```

## Services Deployed

1. **Frontend** (Next.js PWA) - Port 3000
   - Image: localhost:5000/nextjs-frontend:latest
   - Resources: 100m CPU, 128Mi memory

2. **Backend** (FastAPI) - Port 8000
   - Image: localhost:5000/fastapi-backend:latest
   - Resources: 250m CPU, 256Mi memory

3. **Notification Service** - Port 8000
   - Image: localhost:5000/notification-service:latest
   - Resources: 100m CPU, 128Mi memory

4. **Recurring Task Service** - Port 8000
   - Image: localhost:5000/recurring-task-service:latest
   - Resources: 100m CPU, 128Mi memory

5. **Audit Log Service** - Port 8000
   - Image: localhost:5000/audit-log-service:latest
   - Resources: 100m CPU, 128Mi memory

## Dapr Integration

All services have Dapr sidecar enabled:
- `dapr.io/enabled: "true"`
- Configured with app-id and app-port
- Enables service mesh capabilities

## Resource Configuration

Optimized for Minikube development:
- Single replica per service
- Conservative resource limits
- Autoscaling disabled
- External dependencies (DB, Redis, Kafka) disabled

## Verification Commands

```bash
# Check all resources
kubectl get all -n dev

# Check pods
kubectl get pods -n dev

# Check services
kubectl get svc -n dev

# Check ingress
kubectl get ingress -n dev

# View logs
kubectl logs -f -n dev deployment/todo-app-frontend
kubectl logs -f -n dev deployment/todo-app-backend

# Describe a pod
kubectl describe pod <pod-name> -n dev

# Get events
kubectl get events -n dev --sort-by='.lastTimestamp'
```

## Next Steps

1. **Build Docker Images**
   ```bash
   docker build -t localhost:5000/nextjs-frontend:latest ./frontend
   docker build -t localhost:5000/fastapi-backend:latest ./backend
   ```

2. **Push to Minikube Registry**
   ```bash
   docker push localhost:5000/nextjs-frontend:latest
   docker push localhost:5000/fastapi-backend:latest
   ```

3. **Deploy**
   ```bash
   ./deploy-minikube.sh
   ```

4. **Test Access**
   - Open browser to `http://app.<minikube-ip>.nip.io`
   - Test API at `http://api.<minikube-ip>.nip.io/docs`

## Troubleshooting

### Helm not found
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Minikube not starting
```bash
minikube delete
minikube start --driver=docker --cpus=4 --memory=8192
```

### Pods not starting
```bash
kubectl describe pod <pod-name> -n dev
kubectl logs <pod-name> -n dev
```

### Ingress not working
```bash
kubectl get pods -n ingress-nginx
kubectl describe ingress -n dev
```

## Cleanup

```bash
# Quick cleanup
./cleanup.sh

# Manual cleanup
helm uninstall todo-app -n dev
kubectl delete namespace dev

# Full cleanup (stop Minikube)
minikube stop
minikube delete
```

## Production Considerations

For production deployment:
1. Enable and configure PostgreSQL, Redis, Kafka dependencies
2. Set proper resource requests and limits
3. Enable autoscaling (HPA)
4. Configure TLS with cert-manager
5. Set up proper monitoring and logging
6. Use tagged images (not `latest`)
7. Enable network policies
8. Configure pod disruption budgets
9. Set up backup and disaster recovery

See `values.yaml` (commented) for production configuration template.

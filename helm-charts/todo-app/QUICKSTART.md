# Todo App - Minikube Quick Start 🚀

## TL;DR - Deploy in 3 Commands

```bash
chmod +x deploy-minikube.sh cleanup.sh validate.sh
./validate.sh
./deploy-minikube.sh
```

## What This Does

The deployment will:
1. ✅ Install Helm (if not present)
2. ✅ Start Minikube with 4 CPUs and 8GB RAM
3. ✅ Enable ingress, metrics-server, and registry addons
4. ✅ Create `dev` namespace
5. ✅ Deploy 5 microservices:
   - Frontend (Next.js PWA)
   - Backend (FastAPI)
   - Notification Service
   - Recurring Task Service
   - Audit Log Service
6. ✅ Configure ingress with automatic Minikube IP detection
7. ✅ Show access URLs

## Access Your App

After deployment completes, you'll see:

```
Frontend: http://app.192.168.49.2.nip.io
Backend API: http://api.192.168.49.2.nip.io
```

(IP will be your actual Minikube IP)

## Alternative Access via Port-Forward

```bash
# Frontend
kubectl port-forward -n dev svc/todo-app-frontend 3000:3000

# Backend
kubectl port-forward -n dev svc/todo-app-backend 8000:8000
```

Then open:
- http://localhost:3000 (Frontend)
- http://localhost:8000/docs (Backend API docs)

## Check Deployment Status

```bash
# All resources
kubectl get all -n dev

# Pods
kubectl get pods -n dev

# Services
kubectl get svc -n dev

# Logs
kubectl logs -f -n dev deployment/todo-app-frontend
kubectl logs -f -n dev deployment/todo-app-backend
```

## Troubleshooting

### Pods not starting?

```bash
kubectl describe pod <pod-name> -n dev
kubectl logs <pod-name> -n dev
```

### Ingress not working?

```bash
kubectl get ingress -n dev
minikube addons enable ingress
```

### Need to rebuild?

```bash
./cleanup.sh
./deploy-minikube.sh
```

## Cleanup

```bash
./cleanup.sh
```

This removes:
- Helm release
- Namespace and all resources

## Files Overview

- **deploy-minikube.sh** - Automated deployment
- **cleanup.sh** - Remove all resources
- **validate.sh** - Pre-deployment validation
- **dev-values.yaml** - Minikube configuration
- **values.yaml** - Production template
- **Chart.yaml** - Helm chart metadata
- **templates/** - Kubernetes manifests

## What's Deployed?

### Frontend Service
- Port: 3000
- Image: localhost:5000/nextjs-frontend:latest
- Resources: 100m CPU, 128Mi RAM

### Backend Service
- Port: 8000
- Image: localhost:5000/fastapi-backend:latest
- Resources: 250m CPU, 256Mi RAM

### Notification Service
- Port: 8000
- Image: localhost:5000/notification-service:latest
- Resources: 100m CPU, 128Mi RAM

### Recurring Task Service
- Port: 8000
- Image: localhost:5000/recurring-task-service:latest
- Resources: 100m CPU, 128Mi RAM

### Audit Log Service
- Port: 8000
- Image: localhost:5000/audit-log-service:latest
- Resources: 100m CPU, 128Mi RAM

## Configuration

All services have:
- ✅ Dapr sidecars enabled
- ✅ Resource limits configured
- ✅ Health probes (liveness & readiness)
- ✅ Security context (non-root user)

## Dependencies

For Minikube, these are **disabled** (use external services):
- PostgreSQL
- Redis
- Kafka

To enable for production, edit `values.yaml`:
```yaml
postgresql:
  enabled: true

redis:
  enabled: true

kafka:
  enabled: true
```

## Next Steps

1. **Build your images**
   ```bash
   docker build -t localhost:5000/nextjs-frontend:latest ./frontend
   docker build -t localhost:5000/fastapi-backend:latest ./backend
   docker push localhost:5000/nextjs-frontend:latest
   docker push localhost:5000/fastapi-backend:latest
   ```

2. **Deploy**
   ```bash
   ./deploy-minikube.sh
   ```

3. **Test**
   ```bash
   curl http://app.$(minikube ip).nip.io
   ```

## Documentation

- **DEPLOY.md** - Detailed deployment guide
- **SUMMARY.md** - Fixes and changes made
- **README.md** - Full Helm chart documentation

## Support

For issues:
- Check logs: `kubectl logs -f -n dev deployment/todo-app-frontend`
- Describe pod: `kubectl describe pod <pod-name> -n dev`
- Get events: `kubectl get events -n dev --sort-by='.lastTimestamp'`

Happy deploying! 🎉

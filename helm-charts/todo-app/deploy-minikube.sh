#!/bin/bash
set -e

echo "🚀 Todo App Minikube Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check prerequisites
echo -e "${YELLOW}1. Checking prerequisites...${NC}"

if ! command -v minikube &> /dev/null; then
    echo -e "${RED}❌ minikube not found. Please install: https://minikube.sigs.k8s.io/docs/start/${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install: https://kubernetes.io/docs/tasks/tools/${NC}"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${YELLOW}⚠️  helm not found. Installing helm...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# 2. Start Minikube if not running
echo -e "${YELLOW}2. Checking Minikube status...${NC}"
if ! minikube status &> /dev/null; then
    echo "Starting Minikube..."
    minikube start --driver=docker --cpus=4 --memory=8192
else
    echo -e "${GREEN}✅ Minikube is already running${NC}"
fi

# 3. Enable required addons
echo -e "${YELLOW}3. Enabling Minikube addons...${NC}"
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable registry
echo -e "${GREEN}✅ Addons enabled${NC}"

# 4. Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo -e "${GREEN}Minikube IP: ${MINIKUBE_IP}${NC}"

# 5. Update dev-values.yaml with actual Minikube IP
echo -e "${YELLOW}4. Updating ingress hosts with Minikube IP...${NC}"
sed -i "s/app: \"app\.[0-9.]*\.nip\.io\"/app: \"app.${MINIKUBE_IP}.nip.io\"/" dev-values.yaml
sed -i "s/api: \"api\.[0-9.]*\.nip\.io\"/api: \"api.${MINIKUBE_IP}.nip.io\"/" dev-values.yaml
echo -e "${GREEN}✅ Ingress hosts updated${NC}"

# 6. Create namespace
echo -e "${YELLOW}5. Creating dev namespace...${NC}"
kubectl create namespace dev --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ Namespace created${NC}"

# 7. Build Helm dependencies (if Chart.yaml has dependencies)
echo -e "${YELLOW}6. Building Helm dependencies...${NC}"
if [ -f "Chart.yaml" ]; then
    helm dependency build . || echo "No dependencies to build or already built"
fi
echo -e "${GREEN}✅ Dependencies built${NC}"

# 8. Deploy with Helm
echo -e "${YELLOW}7. Deploying todo-app with Helm...${NC}"
helm upgrade --install todo-app . \
  --namespace dev \
  --values dev-values.yaml \
  --wait \
  --timeout 10m

echo -e "${GREEN}✅ Deployment complete${NC}"

# 9. Wait for pods to be ready
echo -e "${YELLOW}8. Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=frontend -n dev --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=backend -n dev --timeout=300s || true

# 10. Show status
echo -e "${YELLOW}9. Checking deployment status...${NC}"
echo ""
echo "Pods:"
kubectl get pods -n dev
echo ""
echo "Services:"
kubectl get svc -n dev
echo ""
echo "Ingress:"
kubectl get ingress -n dev

# 11. Show access URLs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access your application:"
echo -e "  Frontend: ${YELLOW}http://app.${MINIKUBE_IP}.nip.io${NC}"
echo -e "  Backend API: ${YELLOW}http://api.${MINIKUBE_IP}.nip.io${NC}"
echo ""
echo "Or use port-forward:"
echo -e "  ${YELLOW}kubectl port-forward -n dev svc/todo-app-frontend 3000:3000${NC}"
echo -e "  ${YELLOW}kubectl port-forward -n dev svc/todo-app-backend 8000:8000${NC}"
echo ""
echo "Useful commands:"
echo -e "  View logs: ${YELLOW}kubectl logs -f -n dev deployment/todo-app-frontend${NC}"
echo -e "  Get pods: ${YELLOW}kubectl get pods -n dev${NC}"
echo -e "  Describe pod: ${YELLOW}kubectl describe pod <pod-name> -n dev${NC}"
echo ""

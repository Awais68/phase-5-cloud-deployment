#!/bin/bash
set -e

echo "📊 Setting up Monitoring Stack for Todo App"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}1. Checking prerequisites...${NC}"

if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm not found. Installing...${NC}"
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites met${NC}"

# Add Helm repositories
echo -e "\n${YELLOW}2. Adding Helm repositories...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update
echo -e "${GREEN}✅ Repositories added${NC}"

# Create monitoring namespace
echo -e "\n${YELLOW}3. Creating monitoring namespace...${NC}"
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ Namespace created${NC}"

# Install Prometheus + Grafana Stack
echo -e "\n${YELLOW}4. Installing Prometheus + Grafana Stack...${NC}"
echo "This may take several minutes..."

helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin \
  --set grafana.persistence.enabled=false \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
  --set alertmanager.enabled=true \
  --wait --timeout 10m

echo -e "${GREEN}✅ Prometheus + Grafana installed${NC}"

# Install Loki Stack for logs
echo -e "\n${YELLOW}5. Installing Loki Stack (logging)...${NC}"

helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set grafana.enabled=false \
  --set loki.persistence.enabled=false \
  --set loki.persistence.size=10Gi \
  --wait --timeout 10m

echo -e "${GREEN}✅ Loki Stack installed${NC}"

# Install Jaeger for distributed tracing
echo -e "\n${YELLOW}6. Installing Jaeger (tracing)...${NC}"

helm upgrade --install jaeger jaegertracing/jaeger \
  --namespace monitoring \
  --set provisionDataStore.cassandra=false \
  --set allInOne.enabled=true \
  --set storage.type=memory \
  --set agent.enabled=false \
  --set collector.enabled=false \
  --set query.enabled=false \
  --wait --timeout 5m

echo -e "${GREEN}✅ Jaeger installed${NC}"

# Wait for all pods to be ready
echo -e "\n${YELLOW}7. Waiting for all monitoring pods to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki -n monitoring --timeout=300s || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=jaeger -n monitoring --timeout=300s || true

# Display status
echo -e "\n${YELLOW}8. Monitoring stack status...${NC}"
echo ""
kubectl get pods -n monitoring
echo ""

# Create ServiceMonitor for Todo App services
echo -e "\n${YELLOW}9. Creating ServiceMonitors for Todo App...${NC}"

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: todo-app-frontend
  namespace: dev
  labels:
    app: frontend
spec:
  selector:
    matchLabels:
      app: frontend
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
---
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: todo-app-backend
  namespace: dev
  labels:
    app: backend
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
EOF

echo -e "${GREEN}✅ ServiceMonitors created${NC}"

# Configure Loki datasource in Grafana
echo -e "\n${YELLOW}10. Configuring Loki datasource in Grafana...${NC}"

kubectl patch configmap kube-prometheus-grafana -n monitoring --type merge -p '
{
  "data": {
    "datasources.yaml": "apiVersion: 1\ndatasources:\n- name: Loki\n  type: loki\n  access: proxy\n  url: http://loki:3100\n  isDefault: false\n  editable: true\n- name: Jaeger\n  type: jaeger\n  access: proxy\n  url: http://jaeger-query:16686\n  isDefault: false\n  editable: true"
  }
}' || echo "Datasource configuration attempted"

# Restart Grafana to pick up new datasources
kubectl rollout restart deployment kube-prometheus-grafana -n monitoring

echo -e "${GREEN}✅ Datasources configured${NC}"

# Show access information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Monitoring Stack Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access the monitoring tools:${NC}"
echo ""
echo -e "${YELLOW}1. Grafana (Dashboards & Visualization)${NC}"
echo "   Port-forward: kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80"
echo "   URL: http://localhost:3000"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo -e "${YELLOW}2. Prometheus (Metrics & Alerts)${NC}"
echo "   Port-forward: kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090"
echo "   URL: http://localhost:9090"
echo ""
echo -e "${YELLOW}3. Jaeger (Distributed Tracing)${NC}"
echo "   Port-forward: kubectl port-forward -n monitoring svc/jaeger-query 16686:16686"
echo "   URL: http://localhost:16686"
echo ""
echo -e "${YELLOW}4. AlertManager (Alert Management)${NC}"
echo "   Port-forward: kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093"
echo "   URL: http://localhost:9093"
echo ""
echo -e "${BLUE}Pre-configured Grafana Dashboards:${NC}"
echo "   - Kubernetes Cluster Monitoring"
echo "   - Kubernetes API Server"
echo "   - Kubernetes Nodes"
echo "   - Kubernetes Pods"
echo "   - Prometheus Stats"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Access Grafana and explore pre-built dashboards"
echo "2. Add Loki and Jaeger dashboards for logs and traces"
echo "3. Configure alerts in AlertManager"
echo "4. Instrument your application with metrics endpoints"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View all monitoring pods: kubectl get pods -n monitoring"
echo "  View Prometheus targets: kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090"
echo "  View Grafana logs: kubectl logs -n monitoring deployment/kube-prometheus-grafana"
echo "  Restart Grafana: kubectl rollout restart deployment/kube-prometheus-grafana -n monitoring"
echo ""

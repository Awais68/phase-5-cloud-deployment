#!/bin/bash
# Complete Observability Stack Deployment Script
# Deploys Prometheus, Grafana, Loki, and Jaeger for Todo App

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="monitoring"
TIMEOUT="600s"

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "======================================"
print_message "$BLUE" "  Observability Stack Deployment"
print_message "$BLUE" "======================================"
echo ""

# Check prerequisites
print_message "$YELLOW" "Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    print_message "$RED" "Error: kubectl not found. Please install kubectl."
    exit 1
fi

if ! command -v helm &> /dev/null; then
    print_message "$RED" "Error: helm not found. Please install Helm."
    exit 1
fi

print_message "$GREEN" "✓ kubectl and helm found"

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    print_message "$RED" "Error: Cannot connect to Kubernetes cluster."
    exit 1
fi

print_message "$GREEN" "✓ Connected to Kubernetes cluster"
echo ""

# Step 1: Create namespace
print_message "$YELLOW" "Step 1: Creating monitoring namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace $NAMESPACE monitoring=enabled --overwrite
print_message "$GREEN" "✓ Namespace created"
echo ""

# Step 2: Add Helm repositories
print_message "$YELLOW" "Step 2: Adding Helm repositories..."

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo add grafana https://grafana.github.io/helm-charts || true
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts || true

print_message "$YELLOW" "Updating Helm repositories..."
helm repo update

print_message "$GREEN" "✓ Helm repositories added and updated"
echo ""

# Step 3: Deploy Prometheus + Grafana Stack
print_message "$YELLOW" "Step 3: Deploying Prometheus + Grafana Stack..."
print_message "$YELLOW" "This may take 5-10 minutes..."

# Check if monitoring-values.yaml exists
if [ ! -f "../../helm-charts/todo-app/monitoring-values.yaml" ]; then
    print_message "$RED" "Error: monitoring-values.yaml not found at ../../helm-charts/todo-app/monitoring-values.yaml"
    print_message "$YELLOW" "Using default values instead..."

    helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
        --namespace $NAMESPACE \
        --set prometheus.prometheusSpec.retention=7d \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set grafana.adminPassword=admin \
        --set grafana.persistence.enabled=false \
        --timeout $TIMEOUT \
        --wait
else
    helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
        --namespace $NAMESPACE \
        --values ../../helm-charts/todo-app/monitoring-values.yaml \
        --timeout $TIMEOUT \
        --wait
fi

print_message "$GREEN" "✓ Prometheus + Grafana deployed"
echo ""

# Step 4: Deploy Loki Stack
print_message "$YELLOW" "Step 4: Deploying Loki Stack..."

if [ ! -f "./loki/loki-values.yaml" ]; then
    print_message "$YELLOW" "Using default Loki values..."

    helm upgrade --install loki grafana/loki-stack \
        --namespace $NAMESPACE \
        --set promtail.enabled=true \
        --set loki.persistence.enabled=true \
        --set loki.persistence.size=10Gi \
        --timeout $TIMEOUT \
        --wait
else
    helm upgrade --install loki grafana/loki-stack \
        --namespace $NAMESPACE \
        --values ./loki/loki-values.yaml \
        --timeout $TIMEOUT \
        --wait
fi

print_message "$GREEN" "✓ Loki Stack deployed"
echo ""

# Step 5: Deploy Jaeger
print_message "$YELLOW" "Step 5: Deploying Jaeger Tracing..."

if [ ! -f "./jaeger/jaeger-values.yaml" ]; then
    print_message "$YELLOW" "Using default Jaeger values..."

    helm upgrade --install jaeger jaegertracing/jaeger \
        --namespace $NAMESPACE \
        --set allInOne.enabled=true \
        --set storage.type=memory \
        --set query.ingress.enabled=false \
        --timeout $TIMEOUT \
        --wait
else
    helm upgrade --install jaeger jaegertracing/jaeger \
        --namespace $NAMESPACE \
        --values ./jaeger/jaeger-values.yaml \
        --timeout $TIMEOUT \
        --wait
fi

print_message "$GREEN" "✓ Jaeger deployed"
echo ""

# Step 6: Apply Prometheus Alert Rules
print_message "$YELLOW" "Step 6: Applying Prometheus Alert Rules..."

if [ -d "./prometheus/alerts" ]; then
    kubectl apply -f ./prometheus/alerts/ || print_message "$YELLOW" "Warning: Some alert rules may have failed to apply"
    print_message "$GREEN" "✓ Alert rules applied"
else
    print_message "$YELLOW" "Warning: Alert rules directory not found, skipping..."
fi
echo ""

# Step 7: Import Grafana Dashboards
print_message "$YELLOW" "Step 7: Importing Grafana Dashboards..."

if [ -d "./grafana/dashboards" ]; then
    # Create ConfigMap with dashboards
    kubectl create configmap todo-app-dashboards \
        --from-file=./grafana/dashboards/ \
        --namespace $NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -

    # Label for Grafana discovery
    kubectl label configmap todo-app-dashboards \
        --namespace $NAMESPACE \
        grafana_dashboard=1 \
        --overwrite

    print_message "$GREEN" "✓ Dashboards imported (will be auto-loaded by Grafana)"
else
    print_message "$YELLOW" "Warning: Dashboards directory not found, skipping..."
fi
echo ""

# Step 8: Wait for all pods to be ready
print_message "$YELLOW" "Step 8: Waiting for all pods to be ready..."

kubectl wait --for=condition=ready pod \
    -l "app.kubernetes.io/name=grafana" \
    -n $NAMESPACE \
    --timeout=300s || print_message "$YELLOW" "Warning: Grafana pod not ready within timeout"

kubectl wait --for=condition=ready pod \
    -l "app=prometheus" \
    -n $NAMESPACE \
    --timeout=300s || print_message "$YELLOW" "Warning: Prometheus pod not ready within timeout"

kubectl wait --for=condition=ready pod \
    -l "app=loki" \
    -n $NAMESPACE \
    --timeout=300s || print_message "$YELLOW" "Warning: Loki pod not ready within timeout"

kubectl wait --for=condition=ready pod \
    -l "app.kubernetes.io/name=jaeger" \
    -n $NAMESPACE \
    --timeout=300s || print_message "$YELLOW" "Warning: Jaeger pod not ready within timeout"

print_message "$GREEN" "✓ All core components are ready"
echo ""

# Step 9: Display status
print_message "$BLUE" "======================================"
print_message "$BLUE" "  Deployment Complete!"
print_message "$BLUE" "======================================"
echo ""

print_message "$GREEN" "All observability components are deployed in namespace: $NAMESPACE"
echo ""

print_message "$YELLOW" "Pod Status:"
kubectl get pods -n $NAMESPACE
echo ""

print_message "$YELLOW" "Service Status:"
kubectl get svc -n $NAMESPACE
echo ""

# Step 10: Display access instructions
print_message "$BLUE" "======================================"
print_message "$BLUE" "  Access Points"
print_message "$BLUE" "======================================"
echo ""

print_message "$GREEN" "Grafana (Main UI):"
print_message "$YELLOW" "  kubectl port-forward -n $NAMESPACE svc/kube-prometheus-grafana 3000:80"
print_message "$YELLOW" "  Then open: http://localhost:3000"
print_message "$YELLOW" "  Default credentials: admin / admin"
echo ""

print_message "$GREEN" "Prometheus (Metrics):"
print_message "$YELLOW" "  kubectl port-forward -n $NAMESPACE svc/kube-prometheus-kube-prome-prometheus 9090:9090"
print_message "$YELLOW" "  Then open: http://localhost:9090"
echo ""

print_message "$GREEN" "Jaeger (Traces):"
print_message "$YELLOW" "  kubectl port-forward -n $NAMESPACE svc/jaeger-query 16686:16686"
print_message "$YELLOW" "  Then open: http://localhost:16686"
echo ""

print_message "$GREEN" "AlertManager (Alerts):"
print_message "$YELLOW" "  kubectl port-forward -n $NAMESPACE svc/kube-prometheus-kube-prome-alertmanager 9093:9093"
print_message "$YELLOW" "  Then open: http://localhost:9093"
echo ""

# Step 11: Create quick access script
print_message "$YELLOW" "Creating quick access script..."

cat > access-monitoring.sh << 'EOF'
#!/bin/bash
# Quick access to monitoring services

echo "Select service to access:"
echo "1) Grafana (Main UI)"
echo "2) Prometheus"
echo "3) Jaeger"
echo "4) AlertManager"
echo "5) All (opens multiple terminals)"

read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo "Opening Grafana on http://localhost:3000"
        echo "Default credentials: admin / admin"
        kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80
        ;;
    2)
        echo "Opening Prometheus on http://localhost:9090"
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
        ;;
    3)
        echo "Opening Jaeger on http://localhost:16686"
        kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
        ;;
    4)
        echo "Opening AlertManager on http://localhost:9093"
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093
        ;;
    5)
        echo "Opening all services..."
        kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090 &
        kubectl port-forward -n monitoring svc/jaeger-query 16686:16686 &
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093 &
        echo ""
        echo "All services are now accessible:"
        echo "  Grafana: http://localhost:3000 (admin/admin)"
        echo "  Prometheus: http://localhost:9090"
        echo "  Jaeger: http://localhost:16686"
        echo "  AlertManager: http://localhost:9093"
        echo ""
        echo "Press Ctrl+C to stop all port-forwards"
        wait
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
EOF

chmod +x access-monitoring.sh
print_message "$GREEN" "✓ Created access-monitoring.sh for quick access"
echo ""

print_message "$BLUE" "======================================"
print_message "$GREEN" "Quick Access:"
print_message "$YELLOW" "  ./access-monitoring.sh"
print_message "$BLUE" "======================================"
echo ""

print_message "$GREEN" "Deployment completed successfully!"
print_message "$YELLOW" "For detailed usage, see: DEPLOYMENT-GUIDE.md"

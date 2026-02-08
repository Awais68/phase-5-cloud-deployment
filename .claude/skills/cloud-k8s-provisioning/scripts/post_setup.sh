#!/bin/bash
# Post-Cluster Setup Script (All Providers)
# Install: NGINX Ingress, cert-manager, Dapr, Kafka (Strimzi), Monitoring

set -e

EMAIL="${EMAIL:-your-email@example.com}"
KAFKA_NAMESPACE="${KAFKA_NAMESPACE:-kafka}"
MONITORING_NAMESPACE="${MONITORING_NAMESPACE:-monitoring}"

echo "🚀 Starting post-cluster setup..."

# 1. NGINX Ingress Controller
echo ""
echo "📦 Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

echo "⏳ Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

# 2. cert-manager
echo ""
echo "🔐 Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

echo "⏳ Waiting for cert-manager..."
kubectl wait --namespace cert-manager \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=cert-manager \
  --timeout=300s

# Create Let's Encrypt ClusterIssuer
echo "📝 Creating Let's Encrypt ClusterIssuer..."
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: $EMAIL
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# 3. Dapr
echo ""
echo "🔄 Installing Dapr..."
helm repo add dapr https://dapr.github.io/helm-charts/ || true
helm repo update

helm install dapr dapr/dapr \
  --version=1.12 \
  --namespace dapr-system \
  --create-namespace \
  --wait

# 4. Kafka (Strimzi)
echo ""
echo "📨 Installing Kafka (Strimzi)..."
kubectl create namespace $KAFKA_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "https://strimzi.io/install/latest?namespace=$KAFKA_NAMESPACE" -n $KAFKA_NAMESPACE

echo "⏳ Waiting for Strimzi operator..."
kubectl wait --namespace $KAFKA_NAMESPACE \
  --for=condition=ready pod \
  --selector=name=strimzi-cluster-operator \
  --timeout=300s

# Create Kafka cluster
echo "📝 Creating Kafka cluster..."
cat <<EOF | kubectl apply -f -
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: kafka-cluster
  namespace: $KAFKA_NAMESPACE
spec:
  kafka:
    version: 3.5.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
    storage:
      type: ephemeral
  zookeeper:
    replicas: 3
    storage:
      type: ephemeral
  entityOperator:
    topicOperator: {}
    userOperator: {}
EOF

# 5. Monitoring (Prometheus + Grafana)
echo ""
echo "📊 Installing monitoring stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo update

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace $MONITORING_NAMESPACE \
  --create-namespace \
  --wait

echo ""
echo "✅ Post-setup complete!"
echo ""
echo "📋 Verification Commands:"
echo ""
echo "# Check Ingress Controller"
echo "kubectl get pods -n ingress-nginx"
echo "kubectl get svc -n ingress-nginx"
echo ""
echo "# Check cert-manager"
echo "kubectl get pods -n cert-manager"
echo "kubectl get clusterissuer"
echo ""
echo "# Check Dapr"
echo "kubectl get pods -n dapr-system"
echo "dapr status -k"
echo ""
echo "# Check Kafka"
echo "kubectl get pods -n $KAFKA_NAMESPACE"
echo "kubectl get kafka -n $KAFKA_NAMESPACE"
echo ""
echo "# Check Monitoring"
echo "kubectl get pods -n $MONITORING_NAMESPACE"
echo ""
echo "# Access Grafana (port-forward)"
echo "kubectl port-forward -n $MONITORING_NAMESPACE svc/kube-prometheus-grafana 3000:80"
echo "# Default credentials: admin / prom-operator"

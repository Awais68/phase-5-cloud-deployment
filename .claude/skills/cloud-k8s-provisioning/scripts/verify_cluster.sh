#!/bin/bash
# Cluster Verification Script
# Verify cluster readiness and component health

set -e

echo "🔍 Verifying Kubernetes cluster..."
echo ""

# Check cluster connectivity
echo "✓ Checking cluster connectivity..."
if kubectl cluster-info &> /dev/null; then
  echo "  ✅ Cluster accessible"
else
  echo "  ❌ Cannot connect to cluster"
  exit 1
fi

# Check nodes
echo ""
echo "✓ Checking nodes..."
NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
READY_COUNT=$(kubectl get nodes --no-headers | grep -c " Ready")
echo "  ✅ Nodes: $READY_COUNT/$NODE_COUNT ready"

if [ $READY_COUNT -lt 1 ]; then
  echo "  ❌ No ready nodes found"
  exit 1
fi

# Check ingress controller
echo ""
echo "✓ Checking NGINX Ingress..."
if kubectl get svc -n ingress-nginx ingress-nginx-controller &> /dev/null; then
  EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
  fi
  echo "  ✅ Ingress controller running"
  echo "     External IP: ${EXTERNAL_IP:-Pending}"
else
  echo "  ⚠️  Ingress controller not found"
fi

# Check cert-manager
echo ""
echo "✓ Checking cert-manager..."
if kubectl get pods -n cert-manager &> /dev/null; then
  CERT_PODS=$(kubectl get pods -n cert-manager --no-headers | wc -l)
  CERT_READY=$(kubectl get pods -n cert-manager --no-headers | grep -c "Running")
  echo "  ✅ cert-manager: $CERT_READY/$CERT_PODS pods running"

  if kubectl get clusterissuer letsencrypt-prod &> /dev/null; then
    echo "  ✅ Let's Encrypt ClusterIssuer configured"
  else
    echo "  ⚠️  Let's Encrypt ClusterIssuer not found"
  fi
else
  echo "  ⚠️  cert-manager not installed"
fi

# Check Dapr
echo ""
echo "✓ Checking Dapr..."
if kubectl get pods -n dapr-system &> /dev/null; then
  DAPR_PODS=$(kubectl get pods -n dapr-system --no-headers | wc -l)
  DAPR_READY=$(kubectl get pods -n dapr-system --no-headers | grep -c "Running")
  echo "  ✅ Dapr: $DAPR_READY/$DAPR_PODS pods running"
else
  echo "  ⚠️  Dapr not installed"
fi

# Check Kafka
echo ""
echo "✓ Checking Kafka..."
if kubectl get kafka -n kafka &> /dev/null; then
  KAFKA_STATUS=$(kubectl get kafka kafka-cluster -n kafka -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
  if [ "$KAFKA_STATUS" = "True" ]; then
    echo "  ✅ Kafka cluster ready"
  else
    echo "  ⚠️  Kafka cluster not ready"
  fi
else
  echo "  ⚠️  Kafka not installed"
fi

# Check monitoring
echo ""
echo "✓ Checking monitoring..."
if kubectl get pods -n monitoring &> /dev/null; then
  MON_PODS=$(kubectl get pods -n monitoring --no-headers | wc -l)
  MON_READY=$(kubectl get pods -n monitoring --no-headers | grep -c "Running")
  echo "  ✅ Monitoring: $MON_READY/$MON_PODS pods running"
else
  echo "  ⚠️  Monitoring not installed"
fi

echo ""
echo "✅ Cluster verification complete!"
echo ""
echo "📊 Summary:"
kubectl get nodes
echo ""
echo "🔗 Quick Access:"
echo "   Grafana: kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80"
echo "   Default credentials: admin / prom-operator"

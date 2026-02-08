#!/bin/bash
# Kubernetes Secrets Management Script
# Create secrets for database, Kafka, and application

set -e

NAMESPACE="${NAMESPACE:-production}"

echo "🔐 Creating Kubernetes secrets in namespace: $NAMESPACE"

# Ensure namespace exists
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Database secrets
echo ""
echo "📦 Creating database secrets..."
read -p "Enter database connection string: " DB_CONNECTION_STRING
kubectl create secret generic db-secrets \
  --from-literal=connection-string="$DB_CONNECTION_STRING" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Kafka secrets
echo ""
echo "📦 Creating Kafka secrets..."
KAFKA_BOOTSTRAP="${KAFKA_BOOTSTRAP:-kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092}"
kubectl create secret generic kafka-secrets \
  --from-literal=bootstrap-servers="$KAFKA_BOOTSTRAP" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Application secrets
echo ""
echo "📦 Creating application secrets..."
read -p "Enter JWT secret key: " JWT_SECRET
read -p "Enter OpenAI API key: " OPENAI_API_KEY

kubectl create secret generic app-secrets \
  --from-literal=jwt-secret="$JWT_SECRET" \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✅ Secrets created successfully!"
echo ""
echo "📋 Verify with:"
echo "kubectl get secrets -n $NAMESPACE"
echo ""
echo "📝 Use in deployments:"
echo "env:"
echo "  - name: DATABASE_URL"
echo "    valueFrom:"
echo "      secretKeyRef:"
echo "        name: db-secrets"
echo "        key: connection-string"

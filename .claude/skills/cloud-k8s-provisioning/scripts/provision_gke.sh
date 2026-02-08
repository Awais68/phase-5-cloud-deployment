#!/bin/bash
# GKE Cluster Provisioning Script
# Prerequisites: gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-my-project}"
CLUSTER_NAME="${CLUSTER_NAME:-todo-cluster}"
REGION="${REGION:-us-central1}"
NODE_COUNT="${NODE_COUNT:-3}"
MIN_NODES="${MIN_NODES:-3}"
MAX_NODES="${MAX_NODES:-10}"
MACHINE_TYPE="${MACHINE_TYPE:-n1-standard-2}"

echo "🚀 Creating GKE cluster: $CLUSTER_NAME"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Nodes: $NODE_COUNT (autoscale: $MIN_NODES-$MAX_NODES)"
echo "   Machine: $MACHINE_TYPE"

# Create cluster
gcloud container clusters create $CLUSTER_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --num-nodes=$NODE_COUNT \
  --machine-type=$MACHINE_TYPE \
  --enable-autoscaling \
  --min-nodes=$MIN_NODES \
  --max-nodes=$MAX_NODES \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-ip-alias \
  --network="default" \
  --subnetwork="default" \
  --no-enable-basic-auth \
  --no-issue-client-certificate \
  --enable-stackdriver-kubernetes \
  --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver

echo "✅ Cluster created successfully"

# Get credentials
echo "🔑 Configuring kubectl access..."
gcloud container clusters get-credentials $CLUSTER_NAME \
  --region=$REGION \
  --project=$PROJECT_ID

# Verify
echo "✅ Verifying cluster..."
kubectl get nodes
kubectl cluster-info

echo ""
echo "✅ GKE cluster '$CLUSTER_NAME' is ready!"
echo "   Run post-setup with: bash scripts/post_setup.sh"

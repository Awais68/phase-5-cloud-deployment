#!/bin/bash
# OKE Cluster Provisioning Script (Always Free Tier)
# Prerequisites: OCI CLI installed and configured

set -e

# Configuration
COMPARTMENT_ID="${COMPARTMENT_ID:-ocid1.compartment.oc1..xxx}"
CLUSTER_NAME="${CLUSTER_NAME:-todo-cluster}"
VCN_CIDR="${VCN_CIDR:-10.0.0.0/16}"
SUBNET_CIDR="${SUBNET_CIDR:-10.0.0.0/24}"
K8S_VERSION="${K8S_VERSION:-v1.28.2}"
NODE_SHAPE="${NODE_SHAPE:-VM.Standard.E2.1.Micro}"
NODE_COUNT="${NODE_COUNT:-2}"

echo "🚀 Creating OKE cluster: $CLUSTER_NAME (Always Free Tier)"
echo "   Compartment: $COMPARTMENT_ID"
echo "   Kubernetes: $K8S_VERSION"
echo "   Shape: $NODE_SHAPE"
echo "   Nodes: $NODE_COUNT"

# Note: Always Free tier setup is best done via OCI Console
# This script provides the CLI equivalent for reference

echo "⚠️  For Always Free tier, use OCI Console:"
echo ""
echo "1. Navigate to: Developer Services > Kubernetes Clusters (OKE)"
echo "2. Click 'Create Cluster' > 'Quick Create'"
echo "3. Configuration:"
echo "   - Name: $CLUSTER_NAME"
echo "   - Kubernetes Version: Latest"
echo "   - Shape: VM.Standard.E2.1.Micro (Always Free)"
echo "   - Number of Nodes: 2"
echo "   - Public API Endpoint: Yes"
echo "4. Click 'Create Cluster'"
echo ""
echo "After cluster creation, download kubeconfig:"
echo ""
echo "oci ce cluster create-kubeconfig \\"
echo "  --cluster-id <your-cluster-ocid> \\"
echo "  --file ~/.kube/config \\"
echo "  --region <your-region> \\"
echo "  --token-version 2.0.0"
echo ""
echo "Then verify:"
echo "kubectl get nodes"
echo ""
echo "✅ Run post-setup with: bash scripts/post_setup.sh"

#!/bin/bash
# AKS Cluster Provisioning Script
# Prerequisites: Azure CLI installed and authenticated

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-todo-rg}"
CLUSTER_NAME="${CLUSTER_NAME:-todo-cluster}"
LOCATION="${LOCATION:-eastus}"
NODE_COUNT="${NODE_COUNT:-3}"
MIN_NODES="${MIN_NODES:-3}"
MAX_NODES="${MAX_NODES:-10}"
NODE_VM_SIZE="${NODE_VM_SIZE:-Standard_D2s_v3}"

echo "🚀 Creating AKS cluster: $CLUSTER_NAME"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Nodes: $NODE_COUNT (autoscale: $MIN_NODES-$MAX_NODES)"
echo "   VM Size: $NODE_VM_SIZE"

# Create resource group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create cluster
echo "🏗️  Creating cluster..."
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --location $LOCATION \
  --node-count $NODE_COUNT \
  --node-vm-size $NODE_VM_SIZE \
  --enable-cluster-autoscaler \
  --min-count $MIN_NODES \
  --max-count $MAX_NODES \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --network-plugin azure \
  --network-policy azure

echo "✅ Cluster created successfully"

# Get credentials
echo "🔑 Configuring kubectl access..."
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --overwrite-existing

# Verify
echo "✅ Verifying cluster..."
kubectl get nodes
kubectl cluster-info

echo ""
echo "✅ AKS cluster '$CLUSTER_NAME' is ready!"
echo "   Run post-setup with: bash scripts/post_setup.sh"

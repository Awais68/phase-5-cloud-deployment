#!/bin/bash
# Cluster Cleanup Script
# Delete cloud Kubernetes clusters

set -e

PROVIDER="${PROVIDER:-gcp}"

echo "🗑️  Cluster cleanup for provider: $PROVIDER"
echo ""

case $PROVIDER in
  gcp)
    PROJECT_ID="${PROJECT_ID:-my-project}"
    CLUSTER_NAME="${CLUSTER_NAME:-todo-cluster}"
    REGION="${REGION:-us-central1}"

    echo "⚠️  WARNING: This will delete the GKE cluster:"
    echo "   Project: $PROJECT_ID"
    echo "   Cluster: $CLUSTER_NAME"
    echo "   Region: $REGION"
    echo ""
    read -p "Are you sure? (yes/no): " CONFIRM

    if [ "$CONFIRM" = "yes" ]; then
      echo "🗑️  Deleting GKE cluster..."
      gcloud container clusters delete $CLUSTER_NAME \
        --project=$PROJECT_ID \
        --region=$REGION \
        --quiet
      echo "✅ GKE cluster deleted"
    else
      echo "❌ Cancelled"
    fi
    ;;

  azure)
    RESOURCE_GROUP="${RESOURCE_GROUP:-todo-rg}"
    CLUSTER_NAME="${CLUSTER_NAME:-todo-cluster}"

    echo "⚠️  WARNING: This will delete the AKS cluster:"
    echo "   Resource Group: $RESOURCE_GROUP"
    echo "   Cluster: $CLUSTER_NAME"
    echo ""
    read -p "Are you sure? (yes/no): " CONFIRM

    if [ "$CONFIRM" = "yes" ]; then
      echo "🗑️  Deleting AKS cluster..."
      az aks delete \
        --resource-group $RESOURCE_GROUP \
        --name $CLUSTER_NAME \
        --yes --no-wait
      echo "✅ AKS cluster deletion initiated"

      read -p "Delete resource group too? (yes/no): " DELETE_RG
      if [ "$DELETE_RG" = "yes" ]; then
        az group delete --name $RESOURCE_GROUP --yes --no-wait
        echo "✅ Resource group deletion initiated"
      fi
    else
      echo "❌ Cancelled"
    fi
    ;;

  oracle)
    echo "⚠️  For Oracle Cloud (OKE), use OCI Console:"
    echo ""
    echo "1. Navigate to: Developer Services > Kubernetes Clusters (OKE)"
    echo "2. Select your cluster"
    echo "3. Click 'Delete'"
    echo "4. Confirm deletion"
    echo ""
    echo "Or use OCI CLI:"
    echo "oci ce cluster delete --cluster-id <cluster-ocid>"
    ;;

  *)
    echo "❌ Unknown provider: $PROVIDER"
    echo "Supported providers: gcp, azure, oracle"
    exit 1
    ;;
esac

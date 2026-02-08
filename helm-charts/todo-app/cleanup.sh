#!/bin/bash
set -e

echo "🧹 Cleaning up todo-app deployment"

# Uninstall Helm release
echo "Removing Helm release..."
helm uninstall todo-app -n dev || echo "Release not found"

# Delete namespace (this will remove all resources)
echo "Deleting namespace..."
kubectl delete namespace dev --ignore-not-found=true

echo "✅ Cleanup complete"

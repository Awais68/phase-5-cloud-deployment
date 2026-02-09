#!/bin/bash
# Azure AKS Infrastructure Setup Script
# This script provisions all required Azure resources for the Todo App

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these variables
RESOURCE_GROUP="${RESOURCE_GROUP:-todo-app-rg}"
LOCATION="${LOCATION:-eastus}"
AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-todo-app-aks}"
ACR_NAME="${ACR_NAME:-todoappacr$(date +%s | tail -c 6)}"
KEYVAULT_NAME="${KEYVAULT_NAME:-todo-app-kv}"
POSTGRES_SERVER="${POSTGRES_SERVER:-todo-app-db}"
REDIS_NAME="${REDIS_NAME:-todo-app-redis}"
EVENTHUB_NAMESPACE="${EVENTHUB_NAMESPACE:-todo-app-eh}"
LOG_ANALYTICS_WORKSPACE="${LOG_ANALYTICS_WORKSPACE:-todo-app-logs}"
NODE_COUNT="${NODE_COUNT:-1}"  # Reduced for quota limits
NODE_VM_SIZE="${NODE_VM_SIZE:-Standard_DC2ds_v3}"  # 2 vCPU - fits within 4 vCPU quota

echo -e "${GREEN}=== Azure AKS Infrastructure Setup ===${NC}"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "AKS Cluster: $AKS_CLUSTER_NAME"
echo "ACR: $ACR_NAME"
echo ""

# Function to check if Azure CLI is logged in
check_azure_login() {
    echo -e "${YELLOW}Checking Azure CLI login...${NC}"
    if ! az account show &>/dev/null; then
        echo -e "${RED}Not logged in to Azure CLI. Please run 'az login' first.${NC}"
        exit 1
    fi
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    echo -e "${GREEN}Logged in. Subscription: $SUBSCRIPTION_ID${NC}"
}

# Function to create resource group
create_resource_group() {
    echo -e "${YELLOW}Creating Resource Group...${NC}"
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION \
        --tags project=todo-app environment=production
    echo -e "${GREEN}Resource Group created.${NC}"
}

# Function to create Azure Container Registry
create_acr() {
    echo -e "${YELLOW}Creating Azure Container Registry...${NC}"
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Premium \
        --admin-enabled true \
        --location $LOCATION

    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

    echo -e "${GREEN}ACR created: $ACR_NAME.azurecr.io${NC}"
    echo "ACR Username: $ACR_USERNAME"
}

# Function to create Log Analytics Workspace
create_log_analytics() {
    echo -e "${YELLOW}Creating Log Analytics Workspace...${NC}"
    az monitor log-analytics workspace create \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $LOG_ANALYTICS_WORKSPACE \
        --location $LOCATION

    LOG_ANALYTICS_ID=$(az monitor log-analytics workspace show \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $LOG_ANALYTICS_WORKSPACE \
        --query id -o tsv)

    echo -e "${GREEN}Log Analytics Workspace created.${NC}"
}

# Function to create AKS cluster
# Options:
#   - K8s 1.32 (Standard tier, latest stable)
#   - K8s 1.28 with LTS (Premium tier, long-term support until 2027)
create_aks_cluster() {
    echo -e "${YELLOW}Creating AKS Cluster (this may take 10-15 minutes)...${NC}"

    # Choose Kubernetes version strategy:
    # Option 1: Latest stable (1.32) - Standard tier
    # Option 2: LTS version (1.28) - Requires Premium tier
    K8S_VERSION="${K8S_VERSION:-1.32}"
    AKS_TIER="${AKS_TIER:-standard}"  # Set to "premium" for LTS support

    az aks create \
        --resource-group $RESOURCE_GROUP \
        --name $AKS_CLUSTER_NAME \
        --node-count $NODE_COUNT \
        --node-vm-size $NODE_VM_SIZE \
        --enable-managed-identity \
        --enable-addons monitoring \
        --workspace-resource-id $LOG_ANALYTICS_ID \
        --attach-acr $ACR_NAME \
        --network-plugin azure \
        --network-policy azure \
        --generate-ssh-keys \
        --enable-cluster-autoscaler \
        --min-count 1 \
        --max-count 2 \
        --tier $AKS_TIER \
        --kubernetes-version $K8S_VERSION \
        --location $LOCATION \
        --tags project=todo-app environment=production

    # Enable LTS if using Premium tier with K8s 1.28
    if [ "$AKS_TIER" == "premium" ] && [ "$K8S_VERSION" == "1.28" ]; then
        echo -e "${YELLOW}Enabling Long-Term Support for Kubernetes 1.28...${NC}"
        az aks update \
            --resource-group $RESOURCE_GROUP \
            --name $AKS_CLUSTER_NAME \
            --enable-long-term-support
    fi

    # Get credentials
    az aks get-credentials \
        --resource-group $RESOURCE_GROUP \
        --name $AKS_CLUSTER_NAME \
        --overwrite-existing

    echo -e "${GREEN}AKS Cluster created and configured.${NC}"
    echo "  Kubernetes Version: $K8S_VERSION"
    echo "  Tier: $AKS_TIER"
}

# Function to install NGINX Ingress Controller
install_ingress_controller() {
    echo -e "${YELLOW}Installing NGINX Ingress Controller...${NC}"

    # Add Helm repo
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update

    # Install NGINX Ingress
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.replicaCount=2 \
        --set controller.nodeSelector."kubernetes\.io/os"=linux \
        --set defaultBackend.nodeSelector."kubernetes\.io/os"=linux \
        --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz \
        --set controller.service.externalTrafficPolicy=Local

    echo -e "${GREEN}NGINX Ingress Controller installed.${NC}"
}

# Function to install cert-manager
install_cert_manager() {
    echo -e "${YELLOW}Installing cert-manager...${NC}"

    # Add Helm repo
    helm repo add jetstack https://charts.jetstack.io
    helm repo update

    # Install cert-manager
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --set installCRDs=true

    # Wait for cert-manager to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager

    # Create ClusterIssuer for Let's Encrypt
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

    echo -e "${GREEN}cert-manager installed.${NC}"
}

# Function to create Azure Database for PostgreSQL
create_postgres() {
    echo -e "${YELLOW}Creating Azure Database for PostgreSQL...${NC}"

    # Generate random password
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)

    az postgres flexible-server create \
        --resource-group $RESOURCE_GROUP \
        --name $POSTGRES_SERVER \
        --location $LOCATION \
        --admin-user todoadmin \
        --admin-password "$DB_PASSWORD" \
        --sku-name Standard_D2s_v3 \
        --tier GeneralPurpose \
        --storage-size 128 \
        --version 15 \
        --high-availability ZoneRedundant \
        --zone 1 \
        --standby-zone 2

    # Create database
    az postgres flexible-server db create \
        --resource-group $RESOURCE_GROUP \
        --server-name $POSTGRES_SERVER \
        --database-name tododb

    # Allow Azure services
    az postgres flexible-server firewall-rule create \
        --resource-group $RESOURCE_GROUP \
        --name $POSTGRES_SERVER \
        --rule-name AllowAzureServices \
        --start-ip-address 0.0.0.0 \
        --end-ip-address 0.0.0.0

    echo -e "${GREEN}PostgreSQL created.${NC}"
    echo "PostgreSQL Password: $DB_PASSWORD"
    echo "Connection string: postgresql://todoadmin:$DB_PASSWORD@$POSTGRES_SERVER.postgres.database.azure.com:5432/tododb?sslmode=require"
}

# Function to create Azure Cache for Redis
create_redis() {
    echo -e "${YELLOW}Creating Azure Cache for Redis...${NC}"

    az redis create \
        --resource-group $RESOURCE_GROUP \
        --name $REDIS_NAME \
        --location $LOCATION \
        --sku Premium \
        --vm-size P1 \
        --enable-non-ssl-port false \
        --minimum-tls-version 1.2 \
        --zones 1 2 3

    # Get Redis access key
    REDIS_KEY=$(az redis list-keys \
        --resource-group $RESOURCE_GROUP \
        --name $REDIS_NAME \
        --query primaryKey -o tsv)

    echo -e "${GREEN}Redis created.${NC}"
    echo "Redis Connection: rediss://:$REDIS_KEY@$REDIS_NAME.redis.cache.windows.net:6380/0"
}

# Function to create Azure Event Hubs (Kafka)
create_eventhub() {
    echo -e "${YELLOW}Creating Azure Event Hubs Namespace...${NC}"

    az eventhubs namespace create \
        --resource-group $RESOURCE_GROUP \
        --name $EVENTHUB_NAMESPACE \
        --location $LOCATION \
        --sku Standard \
        --enable-kafka true \
        --capacity 2

    # Create Event Hubs (Kafka topics)
    for topic in task-events notification-events audit-events; do
        az eventhubs eventhub create \
            --resource-group $RESOURCE_GROUP \
            --namespace-name $EVENTHUB_NAMESPACE \
            --name $topic \
            --partition-count 4 \
            --message-retention 7
    done

    # Get connection string
    EVENTHUB_CONNECTION=$(az eventhubs namespace authorization-rule keys list \
        --resource-group $RESOURCE_GROUP \
        --namespace-name $EVENTHUB_NAMESPACE \
        --name RootManageSharedAccessKey \
        --query primaryConnectionString -o tsv)

    echo -e "${GREEN}Event Hubs created.${NC}"
    echo "Kafka Bootstrap: $EVENTHUB_NAMESPACE.servicebus.windows.net:9093"
}

# Function to create Azure Key Vault
create_keyvault() {
    echo -e "${YELLOW}Creating Azure Key Vault...${NC}"

    az keyvault create \
        --resource-group $RESOURCE_GROUP \
        --name $KEYVAULT_NAME \
        --location $LOCATION \
        --enable-rbac-authorization true

    # Get AKS managed identity
    AKS_IDENTITY=$(az aks show \
        --resource-group $RESOURCE_GROUP \
        --name $AKS_CLUSTER_NAME \
        --query identityProfile.kubeletidentity.objectId -o tsv)

    # Grant Key Vault access to AKS
    az role assignment create \
        --role "Key Vault Secrets User" \
        --assignee $AKS_IDENTITY \
        --scope $(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)

    echo -e "${GREEN}Key Vault created.${NC}"
}

# Function to create Application Insights
create_app_insights() {
    echo -e "${YELLOW}Creating Application Insights...${NC}"

    az monitor app-insights component create \
        --app todo-app-insights \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP \
        --kind web \
        --application-type web \
        --workspace $LOG_ANALYTICS_ID

    APPINSIGHTS_KEY=$(az monitor app-insights component show \
        --app todo-app-insights \
        --resource-group $RESOURCE_GROUP \
        --query instrumentationKey -o tsv)

    echo -e "${GREEN}Application Insights created.${NC}"
    echo "Instrumentation Key: $APPINSIGHTS_KEY"
}

# Function to print summary
print_summary() {
    echo ""
    echo -e "${GREEN}=== Setup Complete ===${NC}"
    echo ""
    echo "Resources Created:"
    echo "  - Resource Group: $RESOURCE_GROUP"
    echo "  - AKS Cluster: $AKS_CLUSTER_NAME"
    echo "  - ACR: $ACR_NAME.azurecr.io"
    echo "  - PostgreSQL: $POSTGRES_SERVER.postgres.database.azure.com"
    echo "  - Redis: $REDIS_NAME.redis.cache.windows.net"
    echo "  - Event Hubs: $EVENTHUB_NAMESPACE.servicebus.windows.net"
    echo "  - Key Vault: $KEYVAULT_NAME"
    echo "  - Application Insights: todo-app-insights"
    echo ""
    echo "Next Steps:"
    echo "  1. Store secrets in GitHub repository:"
    echo "     - AZURE_CREDENTIALS (Service Principal JSON)"
    echo "     - ACR_NAME, ACR_USERNAME, ACR_PASSWORD"
    echo "     - AZURE_DATABASE_URL, AZURE_REDIS_URL"
    echo "     - AZURE_EVENTHUB_CONNECTION"
    echo ""
    echo "  2. Deploy the application:"
    echo "     helm upgrade --install todo-app ./helm-charts/todo-app \\"
    echo "       -f ./helm-charts/todo-app/values-azure.yaml \\"
    echo "       --namespace production --create-namespace"
    echo ""
    echo "  3. Get Ingress IP:"
    echo "     kubectl get svc -n ingress-nginx"
    echo ""
}

# Main execution
main() {
    check_azure_login
    create_resource_group
    create_log_analytics
    create_acr
    create_aks_cluster
    install_ingress_controller
    install_cert_manager
    create_postgres
    create_redis
    create_eventhub
    create_keyvault
    create_app_insights
    print_summary
}

# Run main function
main

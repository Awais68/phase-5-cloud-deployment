#!/bin/bash

echo "🔍 Helm Chart Validation"
echo "========================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# 1. Check if Chart.yaml exists
echo -e "\n${YELLOW}1. Checking Chart.yaml...${NC}"
if [ -f "Chart.yaml" ]; then
    echo -e "${GREEN}✅ Chart.yaml exists${NC}"

    # Check for duplicate dependencies
    if grep -q "name: postgresql" Chart.yaml && [ $(grep -c "name: postgresql" Chart.yaml) -gt 1 ]; then
        echo -e "${RED}❌ Duplicate postgresql dependency found${NC}"
        ERRORS=$((ERRORS+1))
    else
        echo -e "${GREEN}✅ No duplicate dependencies${NC}"
    fi
else
    echo -e "${RED}❌ Chart.yaml not found${NC}"
    ERRORS=$((ERRORS+1))
fi

# 2. Check templates directory
echo -e "\n${YELLOW}2. Checking templates...${NC}"
if [ -d "templates" ]; then
    echo -e "${GREEN}✅ templates/ directory exists${NC}"

    TEMPLATE_COUNT=$(find templates -name "*.yaml" -o -name "*.tpl" | wc -l)
    echo -e "${GREEN}✅ Found $TEMPLATE_COUNT template files${NC}"

    # Check for required templates
    REQUIRED_TEMPLATES=("deployment-frontend.yaml" "deployment-backend.yaml" "service-frontend.yaml" "service-backend.yaml" "ingress.yaml")
    for template in "${REQUIRED_TEMPLATES[@]}"; do
        if [ -f "templates/$template" ]; then
            echo -e "${GREEN}✅ templates/$template exists${NC}"
        else
            echo -e "${RED}❌ templates/$template missing${NC}"
            ERRORS=$((ERRORS+1))
        fi
    done
else
    echo -e "${RED}❌ templates/ directory not found${NC}"
    ERRORS=$((ERRORS+1))
fi

# 3. Check values files
echo -e "\n${YELLOW}3. Checking values files...${NC}"
if [ -f "dev-values.yaml" ]; then
    echo -e "${GREEN}✅ dev-values.yaml exists${NC}"

    # Check for invalid variable syntax
    if grep -q '\${' dev-values.yaml; then
        echo -e "${YELLOW}⚠️  Found shell variable syntax in dev-values.yaml (should use Helm templating)${NC}"
        WARNINGS=$((WARNINGS+1))
    else
        echo -e "${GREEN}✅ No invalid variable syntax${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  dev-values.yaml not found${NC}"
    WARNINGS=$((WARNINGS+1))
fi

# 4. Check Helm syntax
echo -e "\n${YELLOW}4. Validating Helm chart syntax...${NC}"
if command -v helm &> /dev/null; then
    if helm lint . 2>/dev/null; then
        echo -e "${GREEN}✅ Helm lint passed${NC}"
    else
        echo -e "${RED}❌ Helm lint failed${NC}"
        echo "Run 'helm lint .' for details"
        ERRORS=$((ERRORS+1))
    fi

    # Try template rendering
    if helm template test-release . --values dev-values.yaml > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Helm template rendering successful${NC}"
    else
        echo -e "${RED}❌ Helm template rendering failed${NC}"
        echo "Run 'helm template test-release . --values dev-values.yaml' for details"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${YELLOW}⚠️  Helm not installed, skipping syntax validation${NC}"
    echo "Install with: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
    WARNINGS=$((WARNINGS+1))
fi

# 5. Check deployment scripts
echo -e "\n${YELLOW}5. Checking deployment scripts...${NC}"
if [ -f "deploy-minikube.sh" ]; then
    if [ -x "deploy-minikube.sh" ]; then
        echo -e "${GREEN}✅ deploy-minikube.sh is executable${NC}"
    else
        echo -e "${YELLOW}⚠️  deploy-minikube.sh not executable (run: chmod +x deploy-minikube.sh)${NC}"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo -e "${YELLOW}⚠️  deploy-minikube.sh not found${NC}"
    WARNINGS=$((WARNINGS+1))
fi

if [ -f "cleanup.sh" ]; then
    if [ -x "cleanup.sh" ]; then
        echo -e "${GREEN}✅ cleanup.sh is executable${NC}"
    else
        echo -e "${YELLOW}⚠️  cleanup.sh not executable (run: chmod +x cleanup.sh)${NC}"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo -e "${YELLOW}⚠️  cleanup.sh not found${NC}"
    WARNINGS=$((WARNINGS+1))
fi

# 6. Check prerequisites
echo -e "\n${YELLOW}6. Checking prerequisites...${NC}"
if command -v kubectl &> /dev/null; then
    echo -e "${GREEN}✅ kubectl installed${NC}"
else
    echo -e "${RED}❌ kubectl not installed${NC}"
    ERRORS=$((ERRORS+1))
fi

if command -v minikube &> /dev/null; then
    echo -e "${GREEN}✅ minikube installed${NC}"
else
    echo -e "${YELLOW}⚠️  minikube not installed${NC}"
    WARNINGS=$((WARNINGS+1))
fi

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ docker installed${NC}"
else
    echo -e "${YELLOW}⚠️  docker not installed${NC}"
    WARNINGS=$((WARNINGS+1))
fi

# Summary
echo -e "\n${YELLOW}================================${NC}"
echo -e "${YELLOW}Validation Summary${NC}"
echo -e "${YELLOW}================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed!${NC}"
    echo -e "${GREEN}✅ Chart is ready for deployment${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Build your Docker images"
    echo "  2. Run: ./deploy-minikube.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found${NC}"
    echo -e "${YELLOW}Chart should work but may have issues${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found${NC}"
    echo -e "${RED}❌ $WARNINGS warning(s) found${NC}"
    echo -e "${RED}Please fix errors before deployment${NC}"
    exit 1
fi

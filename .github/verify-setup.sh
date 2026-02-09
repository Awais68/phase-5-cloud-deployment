#!/bin/bash
# Verify GitHub Actions CI/CD Setup
# This script checks if all required files and configurations are in place

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "GitHub Actions CI/CD Setup Verification"
echo "======================================"
echo ""

# Check if .github/workflows directory exists
echo -n "Checking .github/workflows directory... "
if [ -d ".github/workflows" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  ERROR: .github/workflows directory not found"
    exit 1
fi

# Check if CI workflow exists
echo -n "Checking CI workflow (ci.yml)... "
if [ -f ".github/workflows/ci.yml" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  ERROR: .github/workflows/ci.yml not found"
    exit 1
fi

# Check if CD staging workflow exists
echo -n "Checking CD staging workflow (cd-staging.yml)... "
if [ -f ".github/workflows/cd-staging.yml" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  ERROR: .github/workflows/cd-staging.yml not found"
    exit 1
fi

# Check if CD production workflow exists
echo -n "Checking CD production workflow (cd-production.yml)... "
if [ -f ".github/workflows/cd-production.yml" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  ERROR: .github/workflows/cd-production.yml not found"
    exit 1
fi

# Check if Helm chart exists
echo -n "Checking Helm chart... "
if [ -f "helm-charts/todo-app/Chart.yaml" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  ERROR: helm-charts/todo-app/Chart.yaml not found"
    exit 1
fi

# Check backend services
echo ""
echo "Checking backend services:"

SERVICES=(
    "backend/hf_deployment"
    "backend/services/notification-service"
    "backend/services/recurring-task-service"
    "backend/services/audit-log-service"
)

for SERVICE in "${SERVICES[@]}"; do
    echo -n "  - $SERVICE... "
    if [ -d "$SERVICE" ]; then
        if [ -f "$SERVICE/Dockerfile" ]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠${NC} (Dockerfile missing)"
        fi
    else
        echo -e "${RED}✗${NC} (directory not found)"
    fi
done

# Check frontend
echo ""
echo -n "Checking frontend... "
if [ -d "frontend" ]; then
    if [ -f "frontend/Dockerfile" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠${NC} (Dockerfile missing)"
    fi
else
    echo -e "${RED}✗${NC}"
fi

# Check .gitignore
echo ""
echo -n "Checking .gitignore for CI/CD patterns... "
if [ -f ".gitignore" ]; then
    if grep -q "*.kubeconfig" ".gitignore" && grep -q "production-values.yaml" ".gitignore"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠${NC} (some patterns missing)"
    fi
else
    echo -e "${YELLOW}⚠${NC} (.gitignore not found)"
fi

# Check for sensitive files that should not be committed
echo ""
echo "Checking for sensitive files:"

SENSITIVE_FILES=(
    "*.kubeconfig"
    "production-values.yaml"
    "staging-values.yaml"
    "*.b64"
    "*kubeconfig*.yaml"
)

FOUND_SENSITIVE=0
for PATTERN in "${SENSITIVE_FILES[@]}"; do
    if find . -name "$PATTERN" -not -path "./.git/*" -not -name "*.template.yaml" 2>/dev/null | grep -q .; then
        echo -e "  ${RED}✗${NC} Found: $PATTERN"
        echo "    WARNING: Sensitive files found! Add to .gitignore"
        FOUND_SENSITIVE=1
    fi
done

if [ $FOUND_SENSITIVE -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No sensitive files found"
fi

# Check documentation
echo ""
echo "Checking documentation:"
echo -n "  - Workflows README... "
if [ -f ".github/workflows/README.md" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC}"
fi

echo -n "  - Secrets setup guide... "
if [ -f ".github/SETUP_SECRETS.md" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC}"
fi

echo -n "  - Production values template... "
if [ -f ".github/production-values.template.yaml" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC}"
fi

# Check Git status
echo ""
echo "Checking Git status:"
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -n "  - Git repository... "
    echo -e "${GREEN}✓${NC}"

    # Check if there are uncommitted changes to workflow files
    if git diff --name-only | grep -q ".github/"; then
        echo -e "  ${YELLOW}⚠${NC} Uncommitted changes in .github/ directory"
        echo "    Run: git add .github/ && git commit -m 'Add CI/CD workflows'"
    fi
else
    echo -e "  ${RED}✗${NC} Not a Git repository"
fi

# Check required tools
echo ""
echo "Checking required tools (local development):"

TOOLS=("docker" "kubectl" "helm" "git")

for TOOL in "${TOOLS[@]}"; do
    echo -n "  - $TOOL... "
    if command -v $TOOL &> /dev/null; then
        VERSION=$($TOOL version --short 2>/dev/null || $TOOL version 2>/dev/null | head -n1 || echo "installed")
        echo -e "${GREEN}✓${NC} ($VERSION)"
    else
        echo -e "${YELLOW}⚠${NC} (not installed)"
    fi
done

# Summary
echo ""
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [ $FOUND_SENSITIVE -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All checks passed!"
    echo ""
    echo "Next steps:"
    echo "1. Review .github/workflows/README.md"
    echo "2. Set up GitHub secrets (see .github/SETUP_SECRETS.md)"
    echo "3. Configure GitHub environments (staging, production-approval, production)"
    echo "4. Test CI pipeline: git push origin main"
    echo "5. Test staging deployment"
    echo "6. Test production deployment with version tag: git tag v1.0.0"
else
    echo -e "${YELLOW}⚠${NC} Setup complete with warnings"
    echo ""
    echo "Action required:"
    echo "1. Remove or gitignore sensitive files"
    echo "2. Review warnings above"
    echo "3. Complete setup before pushing to GitHub"
fi

echo ""
echo "Documentation:"
echo "  - Workflows: .github/workflows/README.md"
echo "  - Secrets: .github/SETUP_SECRETS.md"
echo "  - Production template: .github/production-values.template.yaml"
echo ""

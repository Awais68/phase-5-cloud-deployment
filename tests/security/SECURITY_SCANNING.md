# Security Scanning Guide

## Overview

This guide covers security scanning for the Todo App microservices:
- Container scanning (Trivy)
- Dependency scanning (pip-audit, osv-scanner)
- Code security (Bandit)
- API security (OWASP ZAP)

---

## 1. Container Scanning with Trivy

### Installation
```bash
# Linux
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# macOS
brew install trivy

# Docker
docker pull aquasec/trivy
```

### Scan Container Images
```bash
# Scan local image
trivy image todo-api:latest

# Scan with severity filter
trivy image --severity CRITICAL,HIGH todo-api:latest

# Output as JSON
trivy image --format json --output trivy-report.json todo-api:latest

# Scan all service images
for service in todo-api recurring-task-service notification-service audit-log-service; do
  trivy image --severity HIGH,CRITICAL ${service}:latest
done
```

### Scan Dockerfile
```bash
trivy config backend/hf_deployment/todo_chatbot/Dockerfile
```

### Scan Kubernetes Manifests
```bash
trivy config k8s/
```

---

## 2. Dependency Scanning

### pip-audit
```bash
# Install
pip install pip-audit

# Scan requirements
pip-audit --requirement backend/hf_deployment/todo_chatbot/requirements.txt

# Output as JSON
pip-audit --requirement requirements.txt --format json --output pip-audit.json

# Scan installed packages
pip-audit

# Fix vulnerabilities (dry run)
pip-audit --fix --dry-run
```

### osv-scanner
```bash
# Install
curl -fsSL https://github.com/google/osv-scanner/releases/download/v1.5.0/osv-scanner_linux_amd64 -o osv-scanner
chmod +x osv-scanner

# Scan directory
./osv-scanner -r backend/

# Output as JSON
./osv-scanner -r backend/ --format json > osv-report.json
```

### safety
```bash
# Install
pip install safety

# Scan requirements
safety check --file requirements.txt

# Scan with full report
safety check --file requirements.txt --full-report

# JSON output
safety check --file requirements.txt --json > safety-report.json
```

---

## 3. Code Security with Bandit

### Installation
```bash
pip install bandit[toml]
```

### Basic Scan
```bash
# Scan backend directory
bandit -r backend/

# Scan with severity threshold
bandit -r backend/ --severity-level medium

# Exclude tests
bandit -r backend/ --exclude tests/

# JSON output
bandit -r backend/ -f json -o bandit-report.json
```

### Configuration (.bandit)
```ini
[bandit]
exclude_dirs = tests,.venv,venv
skips = B101,B601
severity = medium
```

### CI/CD Integration
```bash
# Exit with non-zero if issues found
bandit -r backend/ --severity-level high --exit-zero || exit 1
```

---

## 4. API Security with OWASP ZAP

### Docker Setup
```bash
# Pull ZAP image
docker pull zaproxy/zap-stable
```

### Baseline Scan (Passive)
```bash
# Start your API
docker compose up -d

# Run baseline scan
docker run --rm -v $(pwd):/zap/wrk:rw \
  --network=host \
  zaproxy/zap-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap-report.html \
  -J zap-report.json
```

### Full Scan (Active)
```bash
# WARNING: Active scan can modify data
docker run --rm -v $(pwd):/zap/wrk:rw \
  --network=host \
  zaproxy/zap-stable zap-full-scan.py \
  -t http://localhost:8000 \
  -r zap-full-report.html
```

### API Scan (OpenAPI)
```bash
# Scan using OpenAPI spec
docker run --rm -v $(pwd):/zap/wrk:rw \
  --network=host \
  zaproxy/zap-stable zap-api-scan.py \
  -t http://localhost:8000/openapi.json \
  -f openapi \
  -r zap-api-report.html
```

### ZAP Rules Configuration
Create `.zap/rules.tsv`:
```
10021	IGNORE	(X-Content-Type-Options Header Missing)
10036	IGNORE	(Server Leaks Version Information)
10038	WARN	(Content Security Policy Header Not Set)
```

---

## 5. Infrastructure Security

### Kubernetes Security Scan
```bash
# Using kubesec
docker run -i kubesec/kubesec:v2 scan /dev/stdin < k8s/deployment.yaml

# Using kube-bench (CIS Benchmarks)
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job.batch/kube-bench
```

### Helm Chart Security
```bash
# Scan Helm charts
trivy config k8s/helm/todo-app/

# Check Helm chart security
helm lint k8s/helm/todo-app/ --strict
```

---

## 6. Secret Detection

### TruffleHog
```bash
# Install
pip install trufflehog

# Scan repository
trufflehog git file://. --only-verified

# Scan specific branch
trufflehog git https://github.com/org/repo --branch main
```

### git-secrets
```bash
# Install
brew install git-secrets  # macOS

# Setup
git secrets --install
git secrets --register-aws

# Scan
git secrets --scan
```

---

## 7. Automated Security Reports

### Generate Combined Report
```bash
#!/bin/bash
# run-security-scans.sh

REPORT_DIR="security-reports/$(date +%Y%m%d)"
mkdir -p $REPORT_DIR

echo "Running security scans..."

# Container scan
trivy image todo-api:latest --format json > $REPORT_DIR/trivy.json

# Dependency scan
pip-audit --format json > $REPORT_DIR/pip-audit.json

# Code scan
bandit -r backend/ -f json > $REPORT_DIR/bandit.json

# Generate summary
echo "Security Scan Summary - $(date)" > $REPORT_DIR/summary.txt
echo "==================================" >> $REPORT_DIR/summary.txt
echo "Trivy: $(jq '.Results | length' $REPORT_DIR/trivy.json) findings" >> $REPORT_DIR/summary.txt
echo "pip-audit: $(jq '. | length' $REPORT_DIR/pip-audit.json) findings" >> $REPORT_DIR/summary.txt
echo "Bandit: $(jq '.results | length' $REPORT_DIR/bandit.json) findings" >> $REPORT_DIR/summary.txt

echo "Reports saved to $REPORT_DIR"
```

---

## 8. Security Best Practices Checklist

### Container Security
- [ ] Use minimal base images (alpine, distroless)
- [ ] Run as non-root user
- [ ] No hardcoded secrets in images
- [ ] Regular image updates
- [ ] Image signing (cosign)

### Dependency Security
- [ ] Pin dependency versions
- [ ] Regular dependency updates
- [ ] Automated vulnerability scanning in CI
- [ ] Security advisories monitoring

### Code Security
- [ ] Input validation
- [ ] Output encoding
- [ ] Parameterized queries
- [ ] Proper error handling
- [ ] No hardcoded credentials

### API Security
- [ ] Authentication required
- [ ] Authorization checks
- [ ] Rate limiting
- [ ] HTTPS only
- [ ] Security headers
- [ ] CORS configuration

### Infrastructure Security
- [ ] Network policies
- [ ] Pod security policies
- [ ] Secrets management (Vault, K8s secrets)
- [ ] TLS everywhere
- [ ] Audit logging

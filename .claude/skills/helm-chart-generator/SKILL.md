---
name: helm-chart-generator
description: |
  Use when users need to create or generate Helm charts for Kubernetes deployments.
  Triggers: "create Helm chart", "generate Helm templates", "package for Kubernetes",
  "multi-environment deployment", "Helm values files", "Kubernetes packaging".
  NOT for: kubectl manifests without Helm, Kustomize overlays, or Helm chart debugging.
---

# Helm Chart Generator

Generate production-ready Helm charts for Kubernetes microservices with multi-environment support.

## When to Use

User requests ANY of:
- "Create a Helm chart for [app]"
- "Generate Kubernetes deployment with Helm"
- "Set up multi-environment values files"
- "Package [services] for Kubernetes"
- "Add autoscaling/ingress/Dapr to Helm chart"

## Quick Start

**Run the generator script:**

```bash
python3 scripts/generate_helm_chart.py <app-name> \
  --services frontend backend notification-service \
  --autoscaling \
  --ingress \
  --tls \
  --dapr \
  --monitoring \
  --output ./helm
```

**Script parameters:**
- `app_name`: Application name (required)
- `--services`: List of microservices (space-separated)
- `--autoscaling`: Enable HPA templates
- `--ingress`: Enable Ingress with path-based routing
- `--tls`: Add TLS configuration to Ingress
- `--dapr`: Add Dapr sidecar annotations
- `--monitoring`: Add Prometheus/Grafana config
- `--output`: Output directory (default: `./helm`)
- `--version`: Chart version (default: `0.1.0`)

## Generated Structure

```
<app-name>/
├── Chart.yaml                      # Chart metadata
├── values.yaml                     # Base values (production defaults)
├── values-dev.yaml                 # Development overrides
├── values-staging.yaml             # Staging overrides
├── values-prod.yaml                # Production overrides
└── templates/
    ├── _helpers.tpl                # Template helpers
    ├── configmap.yaml              # Application config
    ├── secret.yaml                 # Secrets template
    ├── serviceaccount.yaml         # ServiceAccount
    ├── deployment-<service>.yaml   # Per-service Deployment
    ├── service-<service>.yaml      # Per-service Service
    ├── hpa.yaml                    # HorizontalPodAutoscaler (optional)
    └── ingress.yaml                # Ingress (optional)
```

## Common Workflows

### 1. Generate Basic Chart

For a simple app with frontend and backend:

```bash
python3 scripts/generate_helm_chart.py my-app \
  --services frontend backend \
  --output ./charts
```

### 2. Full-Featured Microservices

For production microservices with all features:

```bash
python3 scripts/generate_helm_chart.py todo-app \
  --services frontend backend notification-service recurring-task-service audit-log-service \
  --autoscaling \
  --ingress \
  --tls \
  --dapr \
  --monitoring
```

### 3. Customize Generated Chart

After generation:

1. **Update values**: Edit `values.yaml` with actual registry, domain, resource limits
2. **Configure secrets**: Set `database.connectionString` in environment values files
3. **Adjust resources**: Tune CPU/memory requests/limits per service
4. **Review HPA**: Modify min/max replicas and target CPU percentages
5. **Configure Ingress**: Update host, paths, TLS secret names

### 4. Deploy to Environments

```bash
# Development
helm install my-app ./helm/my-app \
  -f ./helm/my-app/values-dev.yaml \
  -n dev --create-namespace

# Staging
helm upgrade --install my-app ./helm/my-app \
  -f ./helm/my-app/values-staging.yaml \
  --set image.backend.tag=v1.2.3 \
  -n staging

# Production
helm upgrade --install my-app ./helm/my-app \
  -f ./helm/my-app/values-prod.yaml \
  --wait --timeout=10m \
  -n production
```

## Key Features

### Security Built-In

Generated templates include:
- Non-root user (UID 1000)
- Dropped ALL capabilities
- Read-only root filesystem
- SecurityContext on pod and container levels

### Resource Management

Each service gets:
- CPU/memory requests for scheduling
- CPU/memory limits to prevent resource exhaustion
- Configurable per-service via values

### Health Checks

Every deployment includes:
- **Liveness probe**: Restarts unhealthy containers
- **Readiness probe**: Removes from load balancer when not ready
- Configurable paths and delays

### ConfigMap/Secret Checksums

Automatic rolling updates when ConfigMap or Secret changes:
```yaml
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

### Multi-Environment Values

- **values.yaml**: Production defaults (high replicas, autoscaling)
- **values-dev.yaml**: Minimal resources, no autoscaling, no TLS
- **values-staging.yaml**: Mid-tier resources, autoscaling enabled
- **values-prod.yaml**: Full resources, monitoring, TLS

### Dapr Integration

When `--dapr` is enabled:
```yaml
dapr.io/enabled: "true"
dapr.io/app-id: "<service-name>"
dapr.io/app-port: "8000"
dapr.io/log-level: "info"
```

### Autoscaling (HPA)

Per-service HPA configuration:
```yaml
autoscaling:
  backend:
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 75
```

### Ingress with Path-Based Routing

Example routing:
- `/` → frontend service
- `/api` → backend service

Supports TLS with cert-manager integration.

## Testing Charts

Before deploying:

```bash
# Lint
helm lint ./helm/my-app

# Dry-run
helm install my-app ./helm/my-app --dry-run --debug

# Render templates
helm template my-app ./helm/my-app -f values-prod.yaml

# Validate with kubectl
helm template my-app ./helm/my-app | kubectl apply --dry-run=client -f -
```

## Best Practices Reference

For detailed best practices, see `references/helm-best-practices.md`:
- Security hardening
- Resource allocation strategies
- HPA configuration patterns
- External database integration (Neon)
- Kafka configuration
- Service dependency handling

## Common Customizations

### Change Image Registry

```yaml
# values.yaml
global:
  registry: ghcr.io/myorg
```

### Add Environment Variables

Edit `templates/configmap.yaml` or add to deployment env section.

### Configure External Database

```yaml
# values-prod.yaml
database:
  external: true
  connectionString: "postgresql://user:pass@neon.tech:5432/db"
```

### Adjust Resource Limits

```yaml
# values.yaml
services:
  backend:
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 2000m
        memory: 2Gi
```

### Enable Specific Features Per Environment

```yaml
# values-dev.yaml
autoscaling:
  enabled: false

# values-prod.yaml
autoscaling:
  enabled: true
```

## Troubleshooting

**Chart validation fails:**
- Run `helm lint ./helm/my-app --debug` to see detailed errors
- Check YAML indentation in templates
- Verify all `{{ .Values.* }}` references exist in values files

**Deployment stuck:**
- Check pod status: `kubectl get pods -n <namespace>`
- View events: `kubectl describe deployment <name> -n <namespace>`
- Check logs: `kubectl logs <pod-name> -n <namespace>`

**ImagePullBackOff:**
- Verify `global.registry` and image tags are correct
- Check `imagePullSecrets` if using private registry

**HPA not scaling:**
- Ensure metrics-server is installed: `kubectl top nodes`
- Verify resource requests are set (HPA requires them)
- Check HPA status: `kubectl describe hpa <name> -n <namespace>`

## Next Steps After Generation

1. **Review and customize** `values.yaml` with actual config
2. **Set secrets** via `--set` or separate secret management
3. **Lint the chart** with `helm lint`
4. **Test in dev** environment first
5. **Document** any custom values or special deployment steps
6. **Version control** the chart directory
7. **CI/CD integration** for automated deployments

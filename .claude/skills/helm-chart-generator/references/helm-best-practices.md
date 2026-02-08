# Helm Chart Best Practices

## Chart Structure Standards

### Security

- **SecurityContext**: Always set `runAsNonRoot: true`, `runAsUser: 1000`, drop ALL capabilities
- **Secrets**: Use external secret management (Sealed Secrets, External Secrets Operator) for production
- **RBAC**: Minimal ServiceAccount permissions, explicit role bindings
- **Network Policies**: Isolate pods, allow only necessary traffic

### Resource Management

- **Requests**: Set realistic CPU/memory requests for scheduling
- **Limits**: Define limits to prevent resource exhaustion
- **QoS**: Aim for Guaranteed or Burstable QoS class

### Health Checks

- **Liveness**: Restart unhealthy containers (longer initialDelaySeconds)
- **Readiness**: Remove from load balancer when not ready (shorter delay)
- **Startup**: For slow-starting apps (prevents premature liveness kills)

### ConfigMap/Secret Checksums

Include checksums in pod annotations to trigger rolling updates:
```yaml
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

### HPA Configuration

- **Min replicas**: Never set to 0 (cold start issues)
- **Target CPU**: 70-80% for predictable workloads
- **Scale-down**: Use `behavior` to prevent flapping

### Ingress

- **TLS**: Always enable for production (cert-manager integration)
- **Annotations**: Use for rate limiting, WAF, redirects
- **Paths**: Prefix-based routing for microservices

### Dapr Integration

- **Annotations**: `dapr.io/enabled`, `dapr.io/app-id`, `dapr.io/app-port`
- **Sidecar Resources**: Define resources for Dapr sidecar
- **Components**: Separate Dapr components from Helm templates

## Values File Organization

```yaml
global:           # Cross-cutting concerns
  environment:
  domain:
  registry:

services:         # Per-service config (indexed by name)
  backend:
    enabled:
    replicaCount:
    image:
    resources:

autoscaling:      # Feature flags with config
  enabled:
  backend:
    minReplicas:

ingress:
  enabled:
  className:
```

## Template Helpers

Essential helpers in `_helpers.tpl`:
- `chart.name`: Chart name
- `chart.fullname`: Release + chart name
- `chart.labels`: Standard labels
- `chart.selectorLabels`: Pod selector labels

## Multi-Environment Strategy

1. **Base values.yaml**: Production defaults
2. **values-dev.yaml**: Minimal resources, no autoscaling
3. **values-staging.yaml**: Mid-tier resources, autoscaling enabled
4. **values-prod.yaml**: Full resources, monitoring, TLS

## Deployment Commands

```bash
# Development
helm install app ./chart -f values-dev.yaml -n dev --create-namespace

# Staging (with specific image tag)
helm upgrade --install app ./chart \
  -f values-staging.yaml \
  --set image.backend.tag=v1.2.3 \
  -n staging

# Production (with wait and timeout)
helm upgrade --install app ./chart \
  -f values-prod.yaml \
  --wait --timeout=10m \
  -n production
```

## Testing

```bash
# Lint
helm lint ./chart

# Dry-run
helm install app ./chart --dry-run --debug

# Template rendering
helm template app ./chart -f values-prod.yaml

# Validate manifests
helm template app ./chart | kubectl apply --dry-run=client -f -
```

## Common Patterns

### External Database (Neon)

```yaml
database:
  external: true
  connectionString: ""  # Provided via --set or secrets

# In deployment
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: app-secrets
      key: database-url
```

### Kafka Integration

```yaml
kafka:
  bootstrapServers: "kafka:9092"
  topics:
    taskEvents: "task-events"

# ConfigMap
data:
  KAFKA_BOOTSTRAP_SERVERS: {{ .Values.kafka.bootstrapServers }}
```

### Service Dependencies

Use initContainers to wait for dependencies:
```yaml
initContainers:
- name: wait-for-db
  image: busybox
  command: ['sh', '-c', 'until nc -z postgres 5432; do sleep 2; done']
```

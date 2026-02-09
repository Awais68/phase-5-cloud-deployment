# Complete Observability Stack Deployment Guide

This guide provides step-by-step instructions for deploying a production-ready observability stack for the Todo microservices application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Steps](#deployment-steps)
4. [Configuration](#configuration)
5. [Access Points](#access-points)
6. [LogQL Queries](#logql-queries)
7. [Troubleshooting](#troubleshooting)
8. [Scaling to Production (OKE)](#scaling-to-production-oke)

---

## Prerequisites

### Required Tools

```bash
# Kubernetes CLI
kubectl version --client

# Helm package manager
helm version

# Running Kubernetes cluster
kubectl cluster-info

# Verify namespace access
kubectl auth can-i create deployment -n monitoring
```

### Minimum Cluster Resources

**Minikube (Development):**
- CPU: 4 cores
- Memory: 8 GB
- Disk: 20 GB

**OKE (Production):**
- Worker Nodes: 3+ nodes
- Node Size: 2 CPU, 8 GB RAM minimum per node
- Storage: Block volumes with high IOPS

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Observability Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Prometheus  │  │     Loki     │  │    Jaeger    │     │
│  │   (Metrics)  │  │    (Logs)    │  │   (Traces)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│         └─────────┬───────┴──────────────────┘              │
│                   │                                         │
│            ┌──────▼───────┐                                │
│            │    Grafana    │                                │
│            │ (Visualization)│                               │
│            └───────────────┘                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Scrapes/Collects
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                      │
├─────────────────────────────────────────────────────────────┤
│  Backend  │  Frontend  │  Notification  │  Recurring-Task   │
│  Audit-Log │                                                 │
│                                                              │
│  - Prometheus metrics endpoint (/metrics)                   │
│  - Structured JSON logs (stdout)                            │
│  - OpenTelemetry traces (gRPC to Jaeger)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Steps

### Step 1: Create Monitoring Namespace

```bash
kubectl create namespace monitoring
kubectl label namespace monitoring monitoring=enabled
```

### Step 2: Add Helm Repositories

```bash
# Prometheus stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Grafana Loki
helm repo add grafana https://grafana.github.io/helm-charts

# Jaeger
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts

# Update repositories
helm repo update
```

### Step 3: Deploy Prometheus + Grafana Stack

```bash
# Deploy kube-prometheus-stack (includes Prometheus, Grafana, AlertManager)
helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values helm-charts/todo-app/monitoring-values.yaml \
  --wait

# Verify deployment
kubectl get pods -n monitoring | grep prometheus
kubectl get pods -n monitoring | grep grafana
```

**Expected Output:**
```
kube-prometheus-kube-prome-operator-xxx   1/1   Running
kube-prometheus-kube-prome-prometheus-0   2/2   Running
monitoring-grafana-xxx                     3/3   Running
```

### Step 4: Deploy Loki Stack

```bash
# Deploy Loki for log aggregation
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --values k8s/monitoring/loki/loki-values.yaml \
  --wait

# Verify Loki deployment
kubectl get pods -n monitoring | grep loki
kubectl get pods -n monitoring | grep promtail
```

**Expected Output:**
```
loki-0                 1/1   Running
promtail-xxx           1/1   Running  (DaemonSet - 1 per node)
```

### Step 5: Deploy Jaeger Tracing

```bash
# Deploy Jaeger all-in-one
helm install jaeger jaegertracing/jaeger \
  --namespace monitoring \
  --values k8s/monitoring/jaeger/jaeger-values.yaml \
  --wait

# Verify Jaeger deployment
kubectl get pods -n monitoring | grep jaeger
```

**Expected Output:**
```
jaeger-xxx   1/1   Running
```

### Step 6: Apply Prometheus Alert Rules

```bash
# Apply application alerts
kubectl apply -f k8s/monitoring/prometheus/alerts/application-alerts.yaml

# Apply Kafka alerts
kubectl apply -f k8s/monitoring/prometheus/alerts/kafka-alerts.yaml

# Apply infrastructure alerts
kubectl apply -f k8s/monitoring/prometheus/alerts/infrastructure-alerts.yaml

# Verify alerts are loaded
kubectl get prometheusrules -n monitoring
```

### Step 7: Configure Grafana Datasources

The datasources are pre-configured in the Helm values. Verify they are working:

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &

# Open browser to http://localhost:3000
# Default credentials: admin / admin (configured in monitoring-values.yaml)

# Check datasources:
# Configuration → Data Sources
# Should see: Prometheus, Loki, Jaeger (all working)
```

### Step 8: Import Grafana Dashboards

**Option A: Via Grafana UI**
1. Navigate to Dashboards → Import
2. Upload JSON files from `k8s/monitoring/grafana/dashboards/`
3. Select Prometheus datasource
4. Click Import

**Option B: Via ConfigMap (Automated)**

```bash
# Create ConfigMap with dashboards
kubectl create configmap todo-app-dashboards \
  --from-file=k8s/monitoring/grafana/dashboards/ \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

# Label for Grafana discovery
kubectl label configmap todo-app-dashboards -n monitoring \
  grafana_dashboard=1

# Grafana will auto-load dashboards within 1-2 minutes
```

### Step 9: Deploy Application with Instrumentation

Ensure your application code includes the instrumentation from:
```
k8s/monitoring/instrumentation/python-fastapi-otel.py
```

Key requirements:
- Prometheus client library: `pip install prometheus_client`
- OpenTelemetry SDK: `pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc`
- FastAPI instrumentation: `pip install opentelemetry-instrumentation-fastapi`

Update your service environment variables:

```yaml
# In your Kubernetes deployment YAML
env:
- name: JAEGER_ENDPOINT
  value: "http://jaeger-collector.monitoring.svc.cluster.local:4317"
- name: SERVICE_NAME
  value: "backend"  # or notification, recurring-task, audit-log, frontend
- name: ENVIRONMENT
  value: "development"
```

### Step 10: Verify End-to-End Observability

**Check Metrics:**
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090 &

# Open http://localhost:9090
# Query: rate(http_requests_total[5m])
# Should see metrics from all services
```

**Check Logs:**
```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 &

# Open http://localhost:3000 → Explore → Loki
# Query: {app="backend"}
# Should see structured JSON logs
```

**Check Traces:**
```bash
# Port-forward to Jaeger
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686 &

# Open http://localhost:16686
# Select service: backend
# Click "Find Traces"
# Should see distributed traces
```

---

## Configuration

### ServiceMonitor Labels

Ensure your application services have proper labels for Prometheus scraping:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  labels:
    app: backend
    monitoring: enabled
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: backend
  ports:
  - name: http
    port: 8000
    targetPort: 8000
```

### Structured Logging Format

All services must log in JSON format to stdout:

```json
{
  "timestamp": "2026-02-08T23:45:12.123Z",
  "level": "INFO",
  "service": "backend",
  "message": "Task created successfully",
  "correlation_id": "abc-123-def",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "user_id": "user-123",
  "task_id": "task-456"
}
```

---

## Access Points

### Local Development (Minikube)

**Grafana (Main UI):**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80
# http://localhost:3000 (admin / admin)
```

**Prometheus (Metrics):**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
# http://localhost:9090
```

**Jaeger (Traces):**
```bash
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
# http://localhost:16686
```

**AlertManager (Alerts):**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093
# http://localhost:9093
```

### Production (OKE with Ingress)

```yaml
# Already configured in grafana-ingress.yaml
# Access via: https://grafana.yourdomain.com
```

---

## LogQL Queries

### Common Log Queries (Loki)

**1. All logs from a service:**
```logql
{app="backend"}
```

**2. Error logs only:**
```logql
{app="backend"} | json | level="ERROR"
```

**3. Logs with specific correlation ID:**
```logql
{app="backend"} | json | correlation_id="abc-123-def"
```

**4. Logs from all services with errors:**
```logql
{namespace="default"} | json | level=~"ERROR|CRITICAL"
```

**5. HTTP 5xx errors:**
```logql
{app="backend"} | json | status=~"5.."
```

**6. Slow requests (duration > 1s):**
```logql
{app="backend"} | json | duration_ms > 1000
```

**7. Kafka event publishing failures:**
```logql
{app=~"backend|notification|recurring-task"} | json | topic!="" | status="failed"
```

**8. Database errors:**
```logql
{app="backend"} | json | line_format "{{.message}}" | "database" | level="ERROR"
```

**9. Authentication failures:**
```logql
{app="backend"} | json | endpoint=~".*/auth/.*" | status=~"401|403"
```

**10. Top 10 error messages:**
```logql
sum by (message) (count_over_time({app="backend"} | json | level="ERROR" [5m]))
```

**11. Logs with trace context:**
```logql
{app="backend"} | json | trace_id!=""
```

**12. Notification failures by channel:**
```logql
{app="notification"} | json | notification_channel!="" | status="failed"
```

**13. Audit log entries:**
```logql
{app="audit-log"} | json | line_format "{{.user_id}} performed {{.action}} on {{.resource}}"
```

**14. Request rate calculation:**
```logql
sum(rate({app="backend"} | json | endpoint!="" [5m])) by (endpoint)
```

**15. Error rate percentage:**
```logql
(sum(rate({app="backend"} | json | status=~"5.." [5m])) /
 sum(rate({app="backend"} | json | status!="" [5m]))) * 100
```

---

## Troubleshooting

### Issue: Prometheus Not Scraping Services

**Symptoms:** Metrics not appearing in Grafana, empty graphs

**Diagnosis:**
```bash
# Check ServiceMonitor resources
kubectl get servicemonitor -n monitoring

# Check Prometheus targets
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
# Visit http://localhost:9090/targets
```

**Solutions:**
1. Verify ServiceMonitor labels match service labels
2. Check service annotations: `prometheus.io/scrape: "true"`
3. Ensure metrics endpoint is reachable: `curl http://<pod-ip>:8000/metrics`
4. Check Prometheus logs: `kubectl logs -n monitoring kube-prometheus-kube-prome-prometheus-0 prometheus`

---

### Issue: Promtail Not Collecting Logs

**Symptoms:** No logs in Loki, empty results in Grafana Explore

**Diagnosis:**
```bash
# Check Promtail pods
kubectl get pods -n monitoring | grep promtail

# Check Promtail logs
kubectl logs -n monitoring -l app=promtail

# Check Loki connectivity
kubectl exec -n monitoring -it <promtail-pod> -- wget -O- http://loki:3100/ready
```

**Solutions:**
1. Verify Promtail DaemonSet is running on all nodes
2. Check volume mounts for `/var/log/pods`
3. Verify Loki service is reachable
4. Check for permission issues accessing log files

---

### Issue: Jaeger Not Receiving Traces

**Symptoms:** No traces in Jaeger UI, empty service list

**Diagnosis:**
```bash
# Check Jaeger pods
kubectl get pods -n monitoring | grep jaeger

# Check Jaeger collector logs
kubectl logs -n monitoring <jaeger-pod> -c jaeger-collector

# Test OTLP endpoint
kubectl run test-curl --image=curlimages/curl --rm -it -- \
  curl -v http://jaeger-collector.monitoring.svc.cluster.local:4317
```

**Solutions:**
1. Verify application is configured with correct Jaeger endpoint:
   `JAEGER_ENDPOINT=http://jaeger-collector.monitoring.svc.cluster.local:4317`
2. Check OpenTelemetry SDK initialization in application code
3. Verify network policies allow traffic to Jaeger
4. Check application logs for OTLP export errors

---

### Issue: Grafana Dashboards Not Showing Data

**Symptoms:** Dashboards load but panels show "No data"

**Diagnosis:**
```bash
# Check datasources in Grafana
# UI: Configuration → Data Sources → Test each datasource

# Check time range (default: last 1 hour)

# Test query directly in Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
# Try query: up
```

**Solutions:**
1. Verify datasource configuration (URL, access mode)
2. Check time range includes data period
3. Validate PromQL queries in Prometheus UI first
4. Check for label mismatches in queries

---

### Issue: High Memory Usage in Prometheus

**Symptoms:** Prometheus pod OOMKilled, high memory consumption

**Diagnosis:**
```bash
# Check Prometheus memory usage
kubectl top pod -n monitoring | grep prometheus

# Check metrics cardinality
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
# Visit http://localhost:9090/tsdb-status
```

**Solutions:**
1. Reduce retention period: `retention: 7d` → `retention: 3d`
2. Implement metric relabeling to drop high-cardinality labels
3. Increase memory limits in Helm values
4. Use recording rules for expensive queries

---

## Scaling to Production (OKE)

### High Availability Configuration

**Prometheus (HA):**
```yaml
prometheus:
  prometheusSpec:
    replicas: 2
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi
          storageClassName: oci-bv  # OKE block volume
```

**Loki (Distributed Mode):**
```yaml
loki:
  replicaCount: 3
  persistence:
    enabled: true
    size: 50Gi
    storageClassName: oci-bv

  # Use object storage (OCI Object Storage)
  storage:
    type: s3
    s3:
      bucketnames: loki-chunks
      region: us-phoenix-1
      endpoint: https://objectstorage.us-phoenix-1.oraclecloud.com
```

**Jaeger (Production Components):**
```yaml
strategy: production

collector:
  enabled: true
  replicaCount: 3

query:
  enabled: true
  replicaCount: 2

agent:
  enabled: true
  daemonset: true

# Elasticsearch storage
storage:
  type: elasticsearch
  elasticsearch:
    host: elasticsearch.monitoring.svc.cluster.local
    port: 9200
```

### External Access via LoadBalancer

```yaml
# Grafana LoadBalancer
apiVersion: v1
kind: Service
metadata:
  name: grafana-external
  namespace: monitoring
spec:
  type: LoadBalancer
  selector:
    app.kubernetes.io/name: grafana
  ports:
  - port: 80
    targetPort: 3000
```

### Authentication and Security

**Grafana:**
```yaml
grafana:
  adminPassword: <strong-password>

  grafana.ini:
    auth.generic_oauth:
      enabled: true
      client_id: <oauth-client-id>
      client_secret: <oauth-client-secret>

    security:
      admin_user: admin
      admin_password: <strong-password>
      cookie_secure: true
```

**Prometheus:**
```yaml
prometheus:
  prometheusSpec:
    # Enable basic auth
    basicAuth:
      enabled: true

    # External URL for federation
    externalUrl: https://prometheus.yourdomain.com
```

---

## Monitoring Best Practices

### 1. Metric Naming Conventions

Follow Prometheus naming conventions:
- Counter: `<metric>_total` (e.g., `http_requests_total`)
- Gauge: `<metric>` (e.g., `memory_usage_bytes`)
- Histogram: `<metric>_bucket`, `<metric>_sum`, `<metric>_count`

### 2. Label Cardinality

**Good (low cardinality):**
- `service`, `endpoint`, `status`, `method`

**Bad (high cardinality - avoid):**
- `user_id`, `task_id`, `correlation_id`, `timestamp`

### 3. Sampling Strategy

**Jaeger Sampling:**
- Development: 100% (sample all traces)
- Staging: 50%
- Production: 10-20% (or adaptive sampling)

### 4. Alert Fatigue Prevention

- Use appropriate thresholds and durations
- Group related alerts
- Implement escalation policies
- Include runbook links in annotations

### 5. Cost Optimization

- Set appropriate retention periods
- Use recording rules for expensive queries
- Implement log sampling for high-volume services
- Archive old data to object storage

---

## Next Steps

1. **Customize Dashboards:** Tailor dashboards to your specific KPIs
2. **Configure AlertManager:** Set up notification channels (Slack, PagerDuty, email)
3. **Implement SLIs/SLOs:** Define and track service level objectives
4. **Create Runbooks:** Document incident response procedures
5. **Set Up Log Aggregation:** Configure log retention and archival policies
6. **Enable Grafana Alerting:** Create alert rules in Grafana for unified alerting

---

## Support and Resources

- **Prometheus Docs:** https://prometheus.io/docs/
- **Grafana Docs:** https://grafana.com/docs/
- **Loki Docs:** https://grafana.com/docs/loki/
- **Jaeger Docs:** https://www.jaegertracing.io/docs/
- **OpenTelemetry Docs:** https://opentelemetry.io/docs/

For issues specific to this deployment, check the troubleshooting section or review logs:

```bash
# Prometheus operator logs
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus-operator

# Grafana logs
kubectl logs -n monitoring -l app.kubernetes.io/name=grafana

# Loki logs
kubectl logs -n monitoring -l app=loki
```

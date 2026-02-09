# Observability Stack for Todo Microservices

Complete production-ready observability solution with Prometheus, Grafana, Loki, and Jaeger for comprehensive monitoring, logging, and tracing.

## Quick Start

### One-Command Deployment

```bash
./deploy-observability.sh
```

This script will:
1. Create monitoring namespace
2. Add Helm repositories
3. Deploy Prometheus + Grafana
4. Deploy Loki + Promtail
5. Deploy Jaeger
6. Apply alert rules
7. Import Grafana dashboards
8. Create access script

### Manual Deployment

See [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md) for detailed step-by-step instructions.

## Directory Structure

```
k8s/monitoring/
├── loki/
│   ├── loki-values.yaml           # Loki stack Helm values
│   └── promtail-values.yaml       # Promtail standalone config
├── jaeger/
│   └── jaeger-values.yaml         # Jaeger tracing Helm values
├── grafana/
│   └── dashboards/
│       ├── main-overview.json     # Main application overview
│       ├── kafka-events.json      # Kafka/event metrics
│       ├── notification-service.json
│       ├── recurring-tasks.json
│       ├── audit-log.json
│       └── frontend-performance.json
├── prometheus/
│   └── alerts/
│       ├── application-alerts.yaml     # Service health alerts
│       ├── kafka-alerts.yaml           # Kafka/event alerts
│       └── infrastructure-alerts.yaml  # Pod/node alerts
├── instrumentation/
│   └── python-fastapi-otel.py     # Application instrumentation example
├── deploy-observability.sh        # Automated deployment script
├── DEPLOYMENT-GUIDE.md            # Comprehensive deployment guide
└── README.md                      # This file
```

## Components

### Prometheus
- **Purpose:** Metrics collection and alerting
- **Port:** 9090
- **Access:** `kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090`
- **Config:** Via `monitoring-values.yaml` in main Helm chart

### Grafana
- **Purpose:** Visualization and dashboards
- **Port:** 3000
- **Access:** `kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80`
- **Credentials:** admin / admin (change in production!)
- **Pre-configured datasources:** Prometheus, Loki, Jaeger

### Loki
- **Purpose:** Log aggregation and querying
- **Port:** 3100
- **Query:** Via Grafana Explore UI
- **Collection:** Promtail DaemonSet on every node
- **Format:** Structured JSON logs from applications

### Jaeger
- **Purpose:** Distributed tracing
- **Port:** 16686 (UI), 4317 (OTLP gRPC), 4318 (OTLP HTTP)
- **Access:** `kubectl port-forward -n monitoring svc/jaeger-query 16686:16686`
- **Protocol:** OpenTelemetry (OTLP)

## Dashboards

### 1. Main Application Overview
**File:** `grafana/dashboards/main-overview.json`

**Panels:**
- Request rate by service
- Error rate percentage (gauge)
- Latency percentiles (P50, P95, P99)
- Response status distribution
- Database query latency
- Connection pool usage

**Use Case:** Overall system health monitoring

---

### 2. Kafka Events Dashboard
**File:** `grafana/dashboards/kafka-events.json`

**Panels:**
- Events published per topic (stacked)
- Events consumed per topic (stacked)
- Consumer group lag table
- Event publishing latency (P95)
- Event processing latency (P95)
- Publishing success vs failures
- Consumption success vs failures

**Use Case:** Event-driven architecture monitoring

---

### 3. Notification Service Dashboard
**Panels:**
- Notifications sent per channel (email, push, websocket)
- Success rate by channel
- Failure rate by channel
- Delivery latency percentiles
- Queue depth (pending notifications)
- External API call latency

**Use Case:** Notification delivery monitoring

---

### 4. Recurring Tasks Dashboard
**Panels:**
- Tasks generated per hour/day
- Generation latency
- Lag behind schedule (seconds)
- Task distribution by frequency
- Processing errors
- Backlog size

**Use Case:** Scheduled task generation monitoring

---

### 5. Audit Log Dashboard
**Panels:**
- Write rate (events/sec)
- Query latency
- Storage usage
- Failed writes
- Retention compliance
- Top operations by user

**Use Case:** Compliance and audit trail monitoring

---

### 6. Frontend Performance Dashboard
**Panels:**
- Page load times
- API call performance by endpoint
- Client-side errors
- Resource loading times
- User session duration
- Browser distribution

**Use Case:** User experience monitoring

## Alert Rules

### Application Alerts (`prometheus/alerts/application-alerts.yaml`)

**Critical Alerts:**
- High error rate (>5% for 5min)
- Service unavailable
- Database connection pool exhaustion
- High task creation failure rate
- High notification failure rate
- Audit log write failures (compliance!)

**Warning Alerts:**
- High latency P95 (>500ms)
- High latency P99 (>1s)
- Low request rate (possible issue)
- High database latency
- Recurring task generation lag

**SLO Alerts:**
- Fast error budget burn (14.4x rate)
- Slow error budget burn (6x rate)

---

### Kafka Alerts (`prometheus/alerts/kafka-alerts.yaml`)

**Critical Alerts:**
- Critical consumer lag (>10,000 messages)
- High event publish failure rate (>5%)
- High event processing failure rate (>5%)
- Consumer not consuming (has lag but zero rate)
- Kafka broker down
- Offline partitions

**Warning Alerts:**
- High consumer lag (>1,000 messages)
- Consumer lag increasing
- Event publishing latency high
- Under-replicated partitions
- Audit events lagging (compliance risk)

---

### Infrastructure Alerts (`prometheus/alerts/infrastructure-alerts.yaml`)

**Critical Alerts:**
- Pod crash looping
- Near memory limit (>95%)
- Deployment rollout stuck
- No pods running for deployment
- PersistentVolume full (>95%)
- Node not ready

**Warning Alerts:**
- Pod not ready
- Pod pending too long
- Container OOMKilled
- High CPU usage (>90%)
- High memory usage (>90%)
- PV nearly full (>85%)
- Node memory/disk pressure

## Application Instrumentation

### Required Dependencies

```bash
pip install prometheus_client
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-otlp-proto-grpc
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-sqlalchemy
```

### Environment Variables

```yaml
env:
- name: JAEGER_ENDPOINT
  value: "http://jaeger-collector.monitoring.svc.cluster.local:4317"
- name: SERVICE_NAME
  value: "backend"  # Change per service
- name: ENVIRONMENT
  value: "development"
```

### Key Metrics to Expose

**HTTP Metrics:**
- `http_requests_total` (Counter) - labels: method, endpoint, status
- `http_request_duration_seconds` (Histogram) - labels: method, endpoint
- `http_active_requests` (Gauge) - labels: method, endpoint

**Database Metrics:**
- `db_operations_total` (Counter) - labels: operation, table, status
- `db_operation_duration_seconds` (Histogram) - labels: operation, table
- `db_connection_pool_active` (Gauge)
- `db_connection_pool_max` (Gauge)

**Kafka Metrics:**
- `kafka_events_published_total` (Counter) - labels: topic, event_type, status
- `kafka_events_consumed_total` (Counter) - labels: topic, event_type, status
- `kafka_event_publish_duration_seconds` (Histogram)
- `kafka_event_processing_duration_seconds` (Histogram)

**Business Metrics (Examples):**
- `task_operations_total` - labels: operation, status
- `notifications_sent_total` - labels: channel, status
- `recurring_task_generation_lag_seconds`
- `audit_log_writes_total` - labels: status

### Structured Logging Format

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
  "task_id": "task-456",
  "endpoint": "/tasks",
  "method": "POST",
  "status": 201,
  "duration_ms": 45.23
}
```

## Common Tasks

### Access Grafana

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80
# Open http://localhost:3000 (admin/admin)
```

### Query Logs in Loki

```logql
# All logs from backend service
{app="backend"}

# Error logs only
{app="backend"} | json | level="ERROR"

# Logs with correlation ID
{app="backend"} | json | correlation_id="abc-123"

# Slow requests (>1s)
{app="backend"} | json | duration_ms > 1000
```

### Check Prometheus Targets

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
# Visit http://localhost:9090/targets
```

### View Traces in Jaeger

```bash
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
# Open http://localhost:16686
# Select service, click "Find Traces"
```

### Check Alert Status

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093
# Open http://localhost:9093
```

### Update Dashboards

```bash
# Edit dashboard JSON files in grafana/dashboards/
# Then reimport via Grafana UI or update ConfigMap:

kubectl create configmap todo-app-dashboards \
  --from-file=grafana/dashboards/ \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Scale for Production (OKE)

Edit Helm values for high availability:

```yaml
prometheus:
  prometheusSpec:
    replicas: 2
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          resources:
            requests:
              storage: 100Gi
```

Redeploy:
```bash
helm upgrade kube-prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f updated-values.yaml
```

## Troubleshooting

### Metrics Not Appearing

1. Check ServiceMonitor exists: `kubectl get servicemonitor -n monitoring`
2. Verify service annotations: `kubectl get svc <service> -o yaml`
3. Check Prometheus targets: http://localhost:9090/targets
4. Verify metrics endpoint: `curl http://<pod-ip>:8000/metrics`

### No Logs in Loki

1. Check Promtail pods: `kubectl get pods -n monitoring | grep promtail`
2. Check Promtail logs: `kubectl logs -n monitoring -l app=promtail`
3. Verify log format is JSON and goes to stdout
4. Check Loki connectivity: `kubectl logs -n monitoring -l app=loki`

### No Traces in Jaeger

1. Verify Jaeger endpoint in app: `http://jaeger-collector.monitoring.svc.cluster.local:4317`
2. Check OpenTelemetry SDK initialization
3. Check Jaeger collector logs: `kubectl logs -n monitoring <jaeger-pod>`
4. Verify network policies allow traffic

### Dashboard Shows No Data

1. Verify datasource configuration in Grafana
2. Check time range includes data
3. Test queries in Prometheus/Loki directly
4. Check for label mismatches in queries

## Performance Tuning

### High Prometheus Memory Usage

- Reduce retention: `retention: 3d`
- Implement metric relabeling
- Use recording rules for expensive queries
- Increase memory limits

### High Loki Storage Usage

- Reduce retention: `retention_period: 72h`
- Implement log sampling for high-volume services
- Use object storage for long-term retention

### Slow Queries

- Use recording rules for complex queries
- Add indexes for frequently queried labels
- Reduce time range
- Use downsampling for historical data

## Security Considerations

### Production Checklist

- [ ] Change Grafana admin password
- [ ] Enable TLS for all services
- [ ] Configure OAuth/SSO for Grafana
- [ ] Implement RBAC for Kubernetes resources
- [ ] Enable Prometheus authentication
- [ ] Secure Jaeger UI with authentication
- [ ] Use secrets for sensitive configuration
- [ ] Enable audit logging
- [ ] Configure network policies
- [ ] Implement rate limiting

## Support

For issues or questions:
1. Check [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md) for detailed documentation
2. Review pod logs: `kubectl logs -n monitoring <pod-name>`
3. Check Prometheus/Grafana/Jaeger documentation
4. Review instrumentation code in `instrumentation/python-fastapi-otel.py`

## Contributing

When adding new dashboards or alerts:
1. Follow naming conventions
2. Add descriptive comments
3. Test thoroughly in development
4. Update this README
5. Include example queries/screenshots

## License

Internal use only - Todo App project

# Observability Stack Verification Checklist

Use this checklist to verify that your observability stack is properly deployed and functioning.

## Pre-Deployment Verification

- [ ] Kubernetes cluster is accessible
  ```bash
  kubectl cluster-info
  ```

- [ ] Helm is installed and configured
  ```bash
  helm version
  ```

- [ ] Sufficient cluster resources available
  ```bash
  kubectl top nodes
  ```

- [ ] Monitoring namespace created
  ```bash
  kubectl get namespace monitoring
  ```

## Post-Deployment Component Checks

### Prometheus

- [ ] Prometheus pods are running
  ```bash
  kubectl get pods -n monitoring -l app=prometheus
  ```

- [ ] Prometheus is scraping targets
  ```bash
  kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
  # Visit http://localhost:9090/targets
  # All targets should show "UP"
  ```

- [ ] Prometheus metrics are being collected
  ```bash
  # Query: up
  # Should show all monitored services
  ```

- [ ] ServiceMonitors are created
  ```bash
  kubectl get servicemonitor -n monitoring
  ```

- [ ] PrometheusRules (alerts) are loaded
  ```bash
  kubectl get prometheusrules -n monitoring
  ```

### Grafana

- [ ] Grafana pod is running
  ```bash
  kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana
  ```

- [ ] Grafana is accessible
  ```bash
  kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80
  # Visit http://localhost:3000
  # Login with admin/admin
  ```

- [ ] Prometheus datasource is configured and working
  ```
  Configuration → Data Sources → Prometheus → Test
  Should show: "Data source is working"
  ```

- [ ] Loki datasource is configured and working
  ```
  Configuration → Data Sources → Loki → Test
  Should show: "Data source is working"
  ```

- [ ] Jaeger datasource is configured and working
  ```
  Configuration → Data Sources → Jaeger → Test
  Should show: "Data source is working"
  ```

- [ ] Dashboards are imported
  ```
  Dashboards → Browse
  Should see:
  - Todo App - Main Overview
  - Todo App - Kafka Events
  - (Other imported dashboards)
  ```

- [ ] Dashboard panels show data
  ```
  Open "Todo App - Main Overview"
  Check that graphs display metrics (not "No data")
  ```

### Loki

- [ ] Loki pod is running
  ```bash
  kubectl get pods -n monitoring -l app=loki
  ```

- [ ] Promtail DaemonSet is running on all nodes
  ```bash
  kubectl get daemonset -n monitoring promtail
  # DESIRED should equal CURRENT and READY
  ```

- [ ] Promtail is collecting logs
  ```bash
  kubectl logs -n monitoring -l app=promtail --tail=20
  # Should show log collection activity
  ```

- [ ] Logs are queryable in Grafana
  ```
  Explore → Select Loki datasource
  Query: {namespace="default"}
  Should show logs from application pods
  ```

- [ ] Structured JSON logs are parsed correctly
  ```
  Query: {app="backend"} | json
  Should show parsed JSON fields (level, service, message, etc.)
  ```

### Jaeger

- [ ] Jaeger pod is running
  ```bash
  kubectl get pods -n monitoring -l app.kubernetes.io/name=jaeger
  ```

- [ ] Jaeger UI is accessible
  ```bash
  kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
  # Visit http://localhost:16686
  ```

- [ ] Services are visible in Jaeger
  ```
  Jaeger UI → Service dropdown
  Should show: backend, notification, recurring-task, etc.
  ```

- [ ] Traces are being collected
  ```
  Select a service → Click "Find Traces"
  Should show trace data
  ```

- [ ] Trace context propagation is working
  ```
  Select a trace → View details
  Should show multiple spans across services
  ```

### AlertManager

- [ ] AlertManager pod is running
  ```bash
  kubectl get pods -n monitoring -l app=alertmanager
  ```

- [ ] AlertManager UI is accessible
  ```bash
  kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093
  # Visit http://localhost:9093
  ```

- [ ] Alerts are loaded (check in Prometheus)
  ```
  Prometheus UI → Alerts
  Should show configured alert rules
  ```

## Application Instrumentation Checks

### Backend Service

- [ ] Backend service has `/metrics` endpoint
  ```bash
  kubectl port-forward -n default svc/backend 8000:8000
  curl http://localhost:8000/metrics
  # Should return Prometheus metrics
  ```

- [ ] Backend metrics are being scraped
  ```
  Prometheus UI → Targets
  Find backend service → Should show "UP"
  ```

- [ ] Backend logs are structured JSON
  ```bash
  kubectl logs -n default -l app=backend --tail=5
  # Should show JSON-formatted logs
  ```

- [ ] Backend traces are visible in Jaeger
  ```
  Jaeger UI → Service: backend → Find Traces
  Should show traces
  ```

### Notification Service

- [ ] Notification service metrics endpoint accessible
- [ ] Notification metrics scraped by Prometheus
- [ ] Notification logs in Loki
- [ ] Notification traces in Jaeger
- [ ] Notification-specific metrics visible:
  ```promql
  notifications_sent_total
  ```

### Recurring-Task Service

- [ ] Recurring-task service metrics endpoint accessible
- [ ] Recurring-task metrics scraped by Prometheus
- [ ] Recurring-task logs in Loki
- [ ] Recurring-task traces in Jaeger
- [ ] Recurring-task specific metrics visible:
  ```promql
  recurring_task_generation_lag_seconds
  ```

### Audit-Log Service

- [ ] Audit-log service metrics endpoint accessible
- [ ] Audit-log metrics scraped by Prometheus
- [ ] Audit-log logs in Loki
- [ ] Audit-log traces in Jaeger
- [ ] Audit-log specific metrics visible:
  ```promql
  audit_log_writes_total
  ```

### Frontend Service

- [ ] Frontend service metrics endpoint accessible
- [ ] Frontend metrics scraped by Prometheus
- [ ] Frontend logs in Loki
- [ ] Frontend traces in Jaeger (if applicable)

## Functional Tests

### Test 1: Metrics Collection

- [ ] Create a test task via API
  ```bash
  curl -X POST http://backend:8000/tasks \
    -H "Content-Type: application/json" \
    -d '{"title": "Test Task", "user_id": "test-user"}'
  ```

- [ ] Verify metrics in Prometheus
  ```promql
  # Query in Prometheus UI:
  rate(http_requests_total{service="backend",endpoint="/tasks"}[5m])
  # Should show non-zero rate
  ```

- [ ] Check dashboard updates
  ```
  Grafana → Main Overview Dashboard
  "Request Rate by Service" panel should show backend activity
  ```

### Test 2: Log Collection

- [ ] Generate test logs
  ```bash
  # Create multiple tasks to generate logs
  for i in {1..10}; do
    curl -X POST http://backend:8000/tasks \
      -H "Content-Type: application/json" \
      -d "{\"title\": \"Test Task $i\", \"user_id\": \"test-user\"}"
  done
  ```

- [ ] Query logs in Grafana
  ```logql
  {app="backend"} | json | line_format "{{.level}} - {{.message}}"
  ```

- [ ] Verify correlation IDs are present
  ```logql
  {app="backend"} | json | correlation_id!=""
  ```

### Test 3: Distributed Tracing

- [ ] Trigger a multi-service flow
  ```bash
  # Create a task that triggers:
  # backend → kafka → recurring-task → notification
  curl -X POST http://backend:8000/tasks \
    -H "Content-Type: application/json" \
    -d '{"title": "Recurring Task", "user_id": "test-user", "recurrence": "daily"}'
  ```

- [ ] Find trace in Jaeger
  ```
  Jaeger UI → Service: backend → Find Traces
  Look for trace with multiple spans
  ```

- [ ] Verify trace completeness
  ```
  Trace should show:
  - HTTP request to backend
  - Database insert
  - Kafka event publish
  - Event consumption by recurring-task
  - Notification send
  ```

### Test 4: Alert Firing

- [ ] Trigger a test alert (simulate error)
  ```bash
  # Generate 5xx errors to trigger HighErrorRate alert
  for i in {1..100}; do
    curl -X POST http://backend:8000/invalid-endpoint
  done
  ```

- [ ] Check alert status in Prometheus
  ```
  Prometheus UI → Alerts
  Look for "HighErrorRate" alert
  Should transition from "inactive" → "pending" → "firing"
  ```

- [ ] Verify alert in AlertManager
  ```
  AlertManager UI → Should show active alert
  ```

- [ ] Check Grafana alerting
  ```
  Grafana → Alerting → Alert rules
  Should show fired alerts
  ```

## Performance Checks

### Prometheus Performance

- [ ] Prometheus memory usage is reasonable
  ```bash
  kubectl top pod -n monitoring | grep prometheus
  # Should be under 2Gi for Minikube, adjust for OKE
  ```

- [ ] Prometheus storage is not full
  ```bash
  kubectl exec -n monitoring kube-prometheus-kube-prome-prometheus-0 -c prometheus -- \
    df -h /prometheus
  # Should show available space
  ```

- [ ] Query performance is acceptable
  ```
  Run complex query in Prometheus UI:
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
  Should complete in < 5 seconds
  ```

### Loki Performance

- [ ] Loki memory usage is reasonable
  ```bash
  kubectl top pod -n monitoring | grep loki
  ```

- [ ] Log queries are responsive
  ```
  Grafana Explore → Loki → Query: {app="backend"}
  Should return results in < 3 seconds
  ```

### Jaeger Performance

- [ ] Jaeger memory usage is reasonable
  ```bash
  kubectl top pod -n monitoring | grep jaeger
  ```

- [ ] Trace queries are responsive
  ```
  Jaeger UI → Find Traces
  Should load traces in < 2 seconds
  ```

## Security Checks

- [ ] Grafana admin password has been changed from default
  ```
  Login to Grafana → Should not accept "admin" as password
  ```

- [ ] Sensitive data is not logged
  ```
  Check logs for passwords, tokens, API keys
  Should NOT be present in plain text
  ```

- [ ] Metrics do not expose PII
  ```
  Check Prometheus metrics
  Should NOT contain user emails, passwords, etc.
  ```

- [ ] Network policies are in place (if applicable)
  ```bash
  kubectl get networkpolicy -n monitoring
  ```

## Integration Checks

### Kafka Integration

- [ ] Kafka events are being published
  ```promql
  rate(kafka_events_published_total[5m])
  # Should show non-zero rate
  ```

- [ ] Kafka consumer lag is tracked
  ```promql
  kafka_consumergroup_lag
  # Should return data
  ```

- [ ] Kafka metrics dashboard shows data
  ```
  Grafana → Kafka Events Dashboard
  All panels should display metrics
  ```

### Database Integration

- [ ] Database operations are tracked
  ```promql
  rate(db_operations_total[5m])
  # Should show non-zero rate
  ```

- [ ] Database query latency is measured
  ```promql
  histogram_quantile(0.95, rate(db_operation_duration_seconds_bucket[5m]))
  # Should return data
  ```

- [ ] Connection pool metrics are available
  ```promql
  db_connection_pool_active / db_connection_pool_max
  # Should return ratio
  ```

## Documentation Checks

- [ ] README.md is complete and accurate
- [ ] DEPLOYMENT-GUIDE.md contains all deployment steps
- [ ] Alert runbooks are accessible
- [ ] Dashboard descriptions are clear
- [ ] Instrumentation examples are provided

## Troubleshooting Readiness

- [ ] Can access Prometheus UI
- [ ] Can access Grafana UI
- [ ] Can access Jaeger UI
- [ ] Can access AlertManager UI
- [ ] Know how to check pod logs
- [ ] Know how to check Prometheus targets
- [ ] Know how to query Loki
- [ ] Know how to view traces

## Production Readiness (OKE)

- [ ] High availability configured (replica count > 1)
- [ ] Persistent storage configured with block volumes
- [ ] Resource limits are appropriate for production
- [ ] Retention periods are set correctly
- [ ] Authentication is enabled
- [ ] TLS is configured for external access
- [ ] Backups are configured
- [ ] Monitoring of monitoring is set up (meta-monitoring)

## Final Sign-Off

- [ ] All critical alerts are configured
- [ ] All dashboards are imported and functional
- [ ] All services are instrumented
- [ ] Documentation is complete
- [ ] Team is trained on using the observability stack
- [ ] Runbooks are created for common issues
- [ ] On-call rotation is established

---

## Verification Script

Run this script to perform automated checks:

```bash
#!/bin/bash
# Quick verification script

echo "Checking Prometheus..."
kubectl get pods -n monitoring -l app=prometheus | grep Running && echo "✓ Prometheus running"

echo "Checking Grafana..."
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana | grep Running && echo "✓ Grafana running"

echo "Checking Loki..."
kubectl get pods -n monitoring -l app=loki | grep Running && echo "✓ Loki running"

echo "Checking Jaeger..."
kubectl get pods -n monitoring -l app.kubernetes.io/name=jaeger | grep Running && echo "✓ Jaeger running"

echo "Checking ServiceMonitors..."
kubectl get servicemonitor -n monitoring && echo "✓ ServiceMonitors created"

echo "Checking PrometheusRules..."
kubectl get prometheusrules -n monitoring && echo "✓ Alert rules loaded"

echo "All checks complete!"
```

Save as `verify-deployment.sh` and run:
```bash
chmod +x verify-deployment.sh
./verify-deployment.sh
```

# Load Testing Guide

## Overview

This directory contains Locust load testing scripts for the Todo App microservices.

## Quick Start

### Install Dependencies

```bash
pip install locust
```

### Run Load Tests

#### Web UI Mode (Recommended for development)
```bash
# Start Locust with web UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open http://localhost:8089 in browser
# Configure users and spawn rate
# Click "Start Swarming"
```

#### Headless Mode (CI/CD)
```bash
# Run for 5 minutes with 100 users
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m \
    --headless \
    --csv=results/load-test
```

### Test Specific Services

```bash
# Main API only
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --class-picker \
    --users=50

# Recurring Task Service
locust -f tests/load/locustfile.py \
    --host=http://localhost:8002 \
    --class-picker
```

## User Classes

| User Class | Target Service | Description |
|------------|----------------|-------------|
| `TodoAPIUser` | Main API (8000) | Task CRUD operations |
| `RecurringTaskUser` | Recurring Service (8002) | Recurring task creation |
| `NotificationServiceUser` | Notification Service (8003) | Notification endpoints |
| `AuditServiceUser` | Audit Service (8004) | Audit log queries |

## Test Scenarios

### Scenario 1: Normal Load
- Users: 50
- Spawn Rate: 5/s
- Duration: 10 minutes

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=50 \
    --spawn-rate=5 \
    --run-time=10m \
    --headless
```

### Scenario 2: Stress Test
- Users: 200
- Spawn Rate: 20/s
- Duration: 15 minutes

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=200 \
    --spawn-rate=20 \
    --run-time=15m \
    --headless
```

### Scenario 3: Spike Test
- Start with 10 users
- Spike to 500 users
- Return to 10 users

Use the web UI for manual spike testing.

### Scenario 4: Endurance Test
- Users: 30
- Duration: 1 hour

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=30 \
    --spawn-rate=2 \
    --run-time=1h \
    --headless \
    --csv=results/endurance
```

## Expected Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Response Time (p95) | < 500ms | < 2000ms |
| Response Time (p99) | < 1000ms | < 5000ms |
| Error Rate | < 1% | < 5% |
| Throughput | > 100 req/s | > 50 req/s |

## Distributed Load Testing

### Master Node
```bash
locust -f tests/load/locustfile.py --master
```

### Worker Nodes
```bash
locust -f tests/load/locustfile.py --worker --master-host=<master-ip>
```

## Kubernetes Load Testing

### Deploy Locust to K8s
```bash
# Deploy master
kubectl apply -f k8s/locust/master-deployment.yaml

# Scale workers
kubectl scale deployment locust-worker --replicas=5
```

## Analyzing Results

CSV reports are generated with:
- `*_stats.csv` - Request statistics
- `*_stats_history.csv` - Statistics over time
- `*_failures.csv` - Failed requests
- `*_exceptions.csv` - Exceptions

### Generate HTML Report
```bash
# After running with --csv flag
python -c "
import pandas as pd
df = pd.read_csv('results/load-test_stats.csv')
print(df.to_html())
" > results/report.html
```

## Integration with CI/CD

See `.github/workflows/load-test.yml` for automated load testing in CI/CD pipelines.

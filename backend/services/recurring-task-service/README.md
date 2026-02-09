# Recurring Task Service

Microservice for managing recurring tasks with automatic instance generation based on iCalendar RRULE format.

## Features

- **iCalendar RRULE Support**: Industry-standard recurrence format (RFC 5545)
- **Automatic Instance Generation**: Creates task instances ahead of time
- **Idempotent Event Processing**: Redis-based deduplication
- **Database-Level Uniqueness**: Prevents duplicate instances
- **Flexible Patterns**: Daily, weekly, monthly, yearly, and complex patterns
- **Dapr Integration**: Event-driven architecture with pub/sub
- **Production Ready**: Comprehensive logging, error handling, and observability

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│   Task Service  │         │  Recurring Task      │
│                 │────────▶│  Service             │
│ Creates         │  Event  │                      │
│ recurring task  │         │ 1. Receives event    │
└─────────────────┘         │ 2. Generates dates   │
                            │ 3. Creates instances │
                            └──────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────────┐
                            │  TaskInstance        │
                            │  (Database)          │
                            │                      │
                            │ - recurring_task_id  │
                            │ - due_date           │
                            │ - is_generated       │
                            └──────────────────────┘
```

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings
```

### Configuration

Key settings in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/tasks

# Redis (for idempotency)
REDIS_URL=redis://localhost:6379/0

# Instance generation
FUTURE_INSTANCES_HORIZON_DAYS=90
MAX_INSTANCES_PER_GENERATION=12

# Dapr
DAPR_PUBSUB_NAME=task-pubsub
RECURRING_TASK_EVENTS_TOPIC=recurring-task-events
```

### Running

```bash
# Development
uvicorn app.main:app --reload --port 8003

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

### Docker

```bash
# Build
docker build -t recurring-task-service .

# Run
docker run -p 8003:8003 recurring-task-service
```

### Kubernetes

```bash
# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=recurring-task-service
```

## Usage

### Creating a Recurring Task

```python
POST /api/recurring-tasks

{
  "title": "Weekly team meeting",
  "description": "Every Monday at 10 AM",
  "rrule": "FREQ=WEEKLY;BYDAY=MO",
  "start_date": "2025-02-10T10:00:00Z",
  "end_date": "2025-12-31T23:59:59Z"
}
```

### Common RRULE Patterns

```python
# Every day
"FREQ=DAILY"

# Every weekday
"FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"

# Every other Friday
"FREQ=WEEKLY;INTERVAL=2;BYDAY=FR"

# 15th of every month
"FREQ=MONTHLY;BYMONTHDAY=15"

# First Monday of month
"FREQ=MONTHLY;BYDAY=1MO"

# Last day of month
"FREQ=MONTHLY;BYMONTHDAY=-1"

# Quarterly (first Friday of Mar/Jun/Sep/Dec)
"FREQ=MONTHLY;BYDAY=1FR;BYMONTH=3,6,9,12"
```

See `docs/RRULE_QUICK_REFERENCE.md` for more patterns.

## Documentation

- **[Recurrence Guide](docs/RECURRENCE_GUIDE.md)**: Complete guide to RRULE patterns
- **[Quick Reference](docs/RRULE_QUICK_REFERENCE.md)**: Handy reference card
- **[Examples](examples/rrule_examples.py)**: Runnable code examples

## Components

### Models

- **RecurringTask**: Stores recurring task definition with RRULE
- **TaskInstance**: Individual occurrences scheduled for generation
- **RecurringTaskEvent**: Event payload for pub/sub

### Services

- **RecurrenceEngine** (`app/services/recurrence_engine.py`)
  - Parses RRULE strings
  - Generates future occurrence dates
  - Validates RRULE format
  - Calculates next occurrences

- **InstanceGenerator** (`app/services/instance_generator.py`)
  - Creates TaskInstance records
  - Handles idempotency
  - Batch inserts with conflict handling
  - Updates recurring task metadata

### API Routes

- `POST /api/recurring-tasks` - Create recurring task
- `GET /api/recurring-tasks` - List recurring tasks
- `GET /api/recurring-tasks/{id}` - Get recurring task
- `PUT /api/recurring-tasks/{id}` - Update recurring task
- `DELETE /api/recurring-tasks/{id}` - Delete recurring task
- `POST /events/recurring-task` - Dapr event handler

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Test recurrence engine
pytest tests/test_recurrence_engine.py -v

# Test specific pattern
pytest tests/test_recurrence_engine.py::TestWeeklyPatterns -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Run Examples

```bash
python examples/rrule_examples.py
```

## Development

### Project Structure

```
recurring-task-service/
├── app/
│   ├── api/
│   │   └── recurring_events.py      # Dapr event handlers
│   ├── models/
│   │   └── recurring_task.py        # Data models
│   ├── services/
│   │   ├── recurrence_engine.py     # RRULE logic
│   │   └── instance_generator.py    # Instance creation
│   ├── config/
│   │   └── settings.py              # Configuration
│   └── main.py                      # FastAPI app
├── tests/
│   └── test_recurrence_engine.py    # Unit tests
├── examples/
│   └── rrule_examples.py            # Usage examples
├── docs/
│   ├── RECURRENCE_GUIDE.md          # Complete guide
│   └── RRULE_QUICK_REFERENCE.md     # Quick reference
├── requirements.txt                  # Dependencies
└── README.md                         # This file
```

### Key Dependencies

- **FastAPI**: Web framework
- **SQLModel**: ORM for PostgreSQL
- **python-dateutil**: RRULE parsing and generation
- **Dapr**: Event-driven integration
- **Redis**: Idempotency tracking
- **structlog**: Structured logging

### Adding New Patterns

1. Add test case in `tests/test_recurrence_engine.py`
2. Verify pattern works with `examples/rrule_examples.py`
3. Document in `docs/RECURRENCE_GUIDE.md`
4. Update quick reference if common pattern

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `FUTURE_INSTANCES_HORIZON_DAYS` | How far ahead to generate | 90 |
| `MAX_INSTANCES_PER_GENERATION` | Max instances per run | 12 |
| `IDEMPOTENCY_TTL_SECONDS` | Redis key TTL | 86400 (24h) |
| `DAPR_PUBSUB_NAME` | Dapr pub/sub component | task-pubsub |
| `RECURRING_TASK_EVENTS_TOPIC` | Topic name | recurring-task-events |

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Observability

### Logging

Structured logging with `structlog`:

```python
logger.info(
    "instances_generated",
    recurring_task_id=task.id,
    count=len(instances),
    horizon_days=90
)
```

### Metrics

Prometheus metrics exposed on `/metrics`:

- `recurring_tasks_total` - Total recurring tasks
- `instances_generated_total` - Total instances generated
- `event_processing_duration_seconds` - Event processing time

### Health Checks

- `GET /health` - Service health
- `GET /ready` - Readiness probe

## Deployment

### Docker Compose

```yaml
services:
  recurring-task-service:
    image: recurring-task-service:latest
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
    depends_on:
      - postgres
      - redis
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check deployment
kubectl get pods -l app=recurring-task-service
kubectl logs -f deployment/recurring-task-service

# Scale
kubectl scale deployment/recurring-task-service --replicas=3
```

### Environment-Specific Configs

- `k8s/base/` - Base configuration
- `k8s/overlays/dev/` - Development
- `k8s/overlays/staging/` - Staging
- `k8s/overlays/prod/` - Production

## Troubleshooting

### No instances generated

**Cause**: `start_date` in past, already generated

**Solution**:
```python
# Generate from last generation point
dates = engine.generate_future_instances(
    rrule_str=task.rrule,
    start_date=task.start_date,
    horizon_days=90
)
```

### Wrong time of day

**Cause**: Missing time component in `start_date`

**Solution**:
```python
# Always include time
start_date = datetime(2025, 2, 10, 9, 0)  # 9 AM
```

### Too many instances

**Cause**: Large horizon with high frequency

**Solution**:
```python
# Use reasonable limits
horizon_days = 90        # 3 months
max_instances = 12       # Cap at 12
```

### Invalid RRULE error

**Cause**: Malformed RRULE string

**Solution**:
```python
# Validate before saving
if not engine.validate_rrule(rrule_str):
    raise ValueError("Invalid RRULE")
```

## Performance

### Optimization Tips

1. **Limit horizon**: Don't generate too far into future
2. **Batch inserts**: Use `ON CONFLICT DO NOTHING` for idempotency
3. **Index properly**: Ensure indices on `(recurring_task_id, due_date)`
4. **Use Redis**: Cache processed event IDs
5. **Pagination**: Paginate API responses for large result sets

### Expected Performance

- Generate 100 daily instances: ~50ms
- Generate 100 monthly instances: ~30ms
- Event processing (with DB insert): ~100-200ms

## Security

- Validate all RRULE inputs
- Use prepared statements (SQLModel handles this)
- Rate limit API endpoints
- Implement authentication/authorization
- Don't expose internal IDs in errors

## Roadmap

- [ ] Skip single occurrence API
- [ ] Modify future occurrences
- [ ] Timezone support
- [ ] Calendar export (iCal format)
- [ ] Web UI for pattern builder
- [ ] Advanced patterns (exceptions, holidays)
- [ ] Analytics dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## License

MIT License - see LICENSE file

## Support

- Documentation: `docs/`
- Examples: `examples/`
- Issues: GitHub Issues
- Slack: #recurring-tasks

## References

- **RFC 5545 (iCalendar)**: https://datatracker.ietf.org/doc/html/rfc5545
- **python-dateutil**: https://dateutil.readthedocs.io/en/stable/rrule.html
- **RRULE Tool**: https://icalendar.org/rrule-tool.html
- **Dapr Docs**: https://docs.dapr.io/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

**Made with ❤️ for reliable recurring task management**

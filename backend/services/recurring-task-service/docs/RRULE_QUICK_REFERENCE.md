# RRULE Quick Reference Card

## Format

```
FREQ=<frequency>;[INTERVAL=n];[BYDAY=days];[BYMONTHDAY=n];[UNTIL=date];[COUNT=n]
```

## Common Patterns

### Daily

| Pattern | RRULE |
|---------|-------|
| Every day | `FREQ=DAILY` |
| Every 2 days | `FREQ=DAILY;INTERVAL=2` |
| Every 3 days | `FREQ=DAILY;INTERVAL=3` |
| Every weekday | `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR` |

### Weekly

| Pattern | RRULE |
|---------|-------|
| Every Monday | `FREQ=WEEKLY;BYDAY=MO` |
| Every Mon/Wed/Fri | `FREQ=WEEKLY;BYDAY=MO,WE,FR` |
| Every other Friday | `FREQ=WEEKLY;INTERVAL=2;BYDAY=FR` |
| Bi-weekly Tuesday | `FREQ=WEEKLY;INTERVAL=2;BYDAY=TU` |

### Monthly

| Pattern | RRULE |
|---------|-------|
| 1st of month | `FREQ=MONTHLY;BYMONTHDAY=1` |
| 15th of month | `FREQ=MONTHLY;BYMONTHDAY=15` |
| Last day of month | `FREQ=MONTHLY;BYMONTHDAY=-1` |
| First Monday | `FREQ=MONTHLY;BYDAY=1MO` |
| Third Thursday | `FREQ=MONTHLY;BYDAY=3TH` |
| Last Friday | `FREQ=MONTHLY;BYDAY=-1FR` |

### Quarterly

| Pattern | RRULE |
|---------|-------|
| 1st of every 3 months | `FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=1` |
| First Friday of Mar/Jun/Sep/Dec | `FREQ=MONTHLY;BYDAY=1FR;BYMONTH=3,6,9,12` |
| Last day of quarter | `FREQ=MONTHLY;BYMONTHDAY=-1;BYMONTH=3,6,9,12` |

### Yearly

| Pattern | RRULE |
|---------|-------|
| Same date each year | `FREQ=YEARLY` |
| Nov 5th each year | `FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5` |

## Parameters

| Parameter | Values | Example |
|-----------|--------|---------|
| `FREQ` | DAILY, WEEKLY, MONTHLY, YEARLY | `FREQ=WEEKLY` |
| `INTERVAL` | Integer (default 1) | `INTERVAL=2` |
| `BYDAY` | MO,TU,WE,TH,FR,SA,SU | `BYDAY=MO,WE,FR` |
| `BYMONTHDAY` | 1-31 or -1 (last day) | `BYMONTHDAY=15` |
| `BYMONTH` | 1-12 | `BYMONTH=3,6,9,12` |
| `COUNT` | Integer | `COUNT=10` |
| `UNTIL` | ISO date (YYYYMMDDTHHMMSSZ) | `UNTIL=20261231T235959Z` |
| `BYSETPOS` | Position in set | `BYSETPOS=3` |

## Weekday Codes

- `MO` = Monday (0)
- `TU` = Tuesday (1)
- `WE` = Wednesday (2)
- `TH` = Thursday (3)
- `FR` = Friday (4)
- `SA` = Saturday (5)
- `SU` = Sunday (6)

Prefix with position: `1MO` (first Monday), `-1FR` (last Friday)

## Python Usage

### Basic Generation

```python
from app.services.recurrence_engine import RecurrenceEngine
from datetime import datetime

engine = RecurrenceEngine()

dates = engine.generate_future_instances(
    rrule_str="FREQ=WEEKLY;BYDAY=MO,WE,FR",
    start_date=datetime(2025, 2, 10, 9, 0),
    horizon_days=30,
    max_instances=12
)
```

### Validation

```python
is_valid = engine.validate_rrule("FREQ=DAILY;INTERVAL=2")
```

### Next Occurrence

```python
next_date = engine.calculate_next_occurrence(
    rrule_str="FREQ=MONTHLY;BYMONTHDAY=15",
    start_date=datetime(2025, 1, 15),
    after_date=datetime(2025, 6, 20)
)
```

### Simple RRULE Creation

```python
rrule = engine.create_rrule_from_simple(
    frequency='weekly',
    interval=1,
    day_of_week=0  # Monday
)
# Returns: "FREQ=WEEKLY;BYDAY=MO"
```

## API Endpoint

### Create Recurring Task

```bash
POST /api/recurring-tasks
Content-Type: application/json

{
  "title": "Weekly team meeting",
  "rrule": "FREQ=WEEKLY;BYDAY=MO",
  "start_date": "2025-02-10T10:00:00Z",
  "end_date": "2025-12-31T23:59:59Z"
}
```

## Real-World Examples

### Daily Standup (Weekdays)
```
FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
Start: 2025-02-10T09:30:00
```

### Sprint Planning (Bi-weekly Monday)
```
FREQ=WEEKLY;INTERVAL=2;BYDAY=MO
Start: 2025-02-10T14:00:00
```

### Monthly Report (1st of month)
```
FREQ=MONTHLY;BYMONTHDAY=1
Start: 2025-02-01T09:00:00
```

### Quarterly Review (Last Friday)
```
FREQ=MONTHLY;BYDAY=-1FR;BYMONTH=3,6,9,12
Start: 2025-01-01T15:00:00
```

### Weekly Backup (Sunday midnight)
```
FREQ=WEEKLY;BYDAY=SU
Start: 2025-02-09T00:00:00
```

## Tips

1. **Always include time in `start_date`**
   ```python
   # Good
   start_date = datetime(2025, 2, 10, 9, 0)

   # Bad (defaults to 00:00:00)
   start_date = datetime(2025, 2, 10)
   ```

2. **Use reasonable horizons**
   - 30 days = ~1 month ahead
   - 90 days = ~3 months ahead (default)
   - 365 days = ~1 year ahead (risky for high-frequency)

3. **Limit instances**
   - Default: 12 instances per generation
   - Prevents database bloat

4. **Validate before saving**
   ```python
   if not engine.validate_rrule(rrule_str):
       raise ValueError("Invalid RRULE")
   ```

5. **Test complex patterns**
   - Use https://icalendar.org/rrule-tool.html
   - Or run `examples/rrule_examples.py`

## Common Mistakes

❌ Missing FREQ
```
BYDAY=MO  # Invalid
```

✅ Include FREQ
```
FREQ=WEEKLY;BYDAY=MO  # Valid
```

❌ No time in start_date
```python
start_date = datetime(2025, 2, 10)  # 00:00:00
```

✅ Include time
```python
start_date = datetime(2025, 2, 10, 9, 0)  # 09:00:00
```

❌ Too large horizon
```python
horizon_days=3650  # 10 years!
```

✅ Reasonable horizon
```python
horizon_days=90  # 3 months
```

## Testing

```bash
# Run examples
cd backend/services/recurring-task-service
python examples/rrule_examples.py

# Run tests
pytest tests/test_recurrence_engine.py -v

# Test specific pattern
pytest tests/test_recurrence_engine.py::TestWeeklyPatterns::test_weekly_multiple_days -v
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No instances generated | `start_date` in past | Use `after_date` or update `last_generated` |
| Wrong time of day | Missing time in `start_date` | Include time: `datetime(2025, 2, 10, 9, 0)` |
| Too many instances | Large horizon + high frequency | Use `max_instances` cap and smaller horizon |
| Invalid RRULE error | Malformed RRULE string | Validate with `engine.validate_rrule()` |

## References

- RFC 5545: https://datatracker.ietf.org/doc/html/rfc5545
- python-dateutil: https://dateutil.readthedocs.io/en/stable/rrule.html
- RRULE Tool: https://icalendar.org/rrule-tool.html
- Full Guide: `docs/RECURRENCE_GUIDE.md`
- Examples: `examples/rrule_examples.py`

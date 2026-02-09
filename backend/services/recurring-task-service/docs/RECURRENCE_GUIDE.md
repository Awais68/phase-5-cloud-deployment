# Recurrence Rules Guide for Recurring Task Service

## Overview

This guide explains how to use recurrence rules (RRULE) in the Recurring Task Service. The service uses the iCalendar RRULE format (RFC 5545) via Python's `python-dateutil` library, the same standard used by Google Calendar, Outlook, and Apple Calendar.

## Quick Start

### 1. Basic Daily Recurrence

```python
# Every day
rrule = "FREQ=DAILY"

# Every 3 days
rrule = "FREQ=DAILY;INTERVAL=3"

# Every weekday (Monday-Friday)
rrule = "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
```

### 2. Weekly Recurrence

```python
# Every Monday
rrule = "FREQ=WEEKLY;BYDAY=MO"

# Every Monday and Wednesday
rrule = "FREQ=WEEKLY;BYDAY=MO,WE"

# Every other Friday
rrule = "FREQ=WEEKLY;INTERVAL=2;BYDAY=FR"
```

### 3. Monthly Recurrence

```python
# 15th of every month
rrule = "FREQ=MONTHLY;BYMONTHDAY=15"

# Last day of month
rrule = "FREQ=MONTHLY;BYMONTHDAY=-1"

# First Monday of every month
rrule = "FREQ=MONTHLY;BYDAY=1MO"

# Third Thursday of every month
rrule = "FREQ=MONTHLY;BYDAY=3TH;BYSETPOS=3"
```

### 4. Yearly Recurrence

```python
# Every November 5th
rrule = "FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5"

# Every first Friday of March, June, September, December
rrule = "FREQ=MONTHLY;BYDAY=1FR;BYMONTH=3,6,9,12"
```

## Architecture Overview

### Database Models

```
RecurringTask
├── id (primary key)
├── user_id (foreign key to users)
├── title
├── description
├── rrule (iCalendar RRULE string)
├── start_date (recurrence anchor date)
├── end_date (optional end date)
├── is_active
├── last_generated (timestamp of last generation)
├── next_occurrence (next scheduled occurrence)
└── timestamps (created_at, updated_at)

TaskInstance
├── id (primary key)
├── recurring_task_id (foreign key)
├── task_id (foreign key to actual task)
├── due_date (when this instance is due)
├── is_generated (whether task was created)
├── generated_at (when task was generated)
└── created_at

Unique constraint: (recurring_task_id, due_date)
```

### Service Components

1. **RecurrenceEngine** (`app/services/recurrence_engine.py`)
   - Parses RRULE strings using `dateutil.rrule`
   - Generates future occurrence dates
   - Validates RRULE format
   - Helper methods for simple frequency conversion

2. **InstanceGenerator** (`app/services/instance_generator.py`)
   - Creates TaskInstance records
   - Handles idempotency via Redis
   - Batch inserts with conflict handling
   - Updates recurring task metadata

3. **Event Handlers** (`app/api/recurring_events.py`)
   - Dapr pub/sub subscriptions
   - Processes recurring task events
   - Triggers instance generation

## How It Works

### 1. Creation Flow

```
User creates recurring task
    ↓
Task Service validates RRULE
    ↓
Publishes "recurring_task.created" event
    ↓
Recurring Task Service receives event
    ↓
RecurrenceEngine calculates future dates
    ↓
InstanceGenerator creates TaskInstance records
    ↓
Background worker creates actual Task records
```

### 2. Generation Logic

The `RecurrenceEngine.generate_future_instances()` method:

```python
def generate_future_instances(
    rrule_str: str,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    horizon_days: int = 90,           # Look ahead 90 days
    max_instances: int = 12,          # Max 12 instances per generation
) -> List[datetime]:
    """
    Generate future task instance dates within horizon window.

    Example:
        rrule_str = "FREQ=WEEKLY;BYDAY=MO,WE,FR"
        start_date = 2025-02-10 09:00
        horizon_days = 30

        Returns: [2025-02-10, 2025-02-12, 2025-02-14, 2025-02-17, ...]
    """
```

**Key Features:**
- Respects `end_date` if provided
- Limits generation to `horizon_days` (default 90)
- Caps at `max_instances` (default 12)
- Avoids duplicates via unique constraint

### 3. Idempotency

Event processing is idempotent via Redis:

```python
# Check if event was already processed
key = f"recurring:event:{event_id}"
if await redis.exists(key):
    return []  # Already processed

# Process event...

# Mark as processed with TTL
await redis.setex(key, ttl_seconds, "1")
```

Database-level idempotency via unique constraint:

```sql
-- Prevents duplicate instances
UNIQUE (recurring_task_id, due_date)
```

## Common Patterns

### Pattern 1: Daily Tasks

```python
# Every morning at 9 AM
recurring_task = RecurringTask(
    title="Daily standup reminder",
    rrule="FREQ=DAILY",
    start_date=datetime(2025, 2, 10, 9, 0),
)
```

### Pattern 2: Weekday Tasks

```python
# Every weekday
recurring_task = RecurringTask(
    title="Check email",
    rrule="FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
    start_date=datetime(2025, 2, 10, 8, 0),
)
```

### Pattern 3: Bi-weekly Meetings

```python
# Every other Tuesday at 2 PM
recurring_task = RecurringTask(
    title="Sprint planning",
    rrule="FREQ=WEEKLY;INTERVAL=2;BYDAY=TU",
    start_date=datetime(2025, 2, 11, 14, 0),
)
```

### Pattern 4: Monthly Reports

```python
# First business day of month (simplified)
recurring_task = RecurringTask(
    title="Monthly report",
    rrule="FREQ=MONTHLY;BYMONTHDAY=1",
    start_date=datetime(2025, 3, 1, 9, 0),
)
```

### Pattern 5: Quarterly Reviews

```python
# First Friday of Mar/Jun/Sep/Dec
recurring_task = RecurringTask(
    title="Quarterly review",
    rrule="FREQ=MONTHLY;BYDAY=1FR;BYMONTH=3,6,9,12",
    start_date=datetime(2025, 3, 7, 10, 0),
)
```

### Pattern 6: Custom Intervals

```python
# Every 10 days
recurring_task = RecurringTask(
    title="Backup check",
    rrule="FREQ=DAILY;INTERVAL=10",
    start_date=datetime(2025, 2, 10),
)
```

## RRULE Reference

### Frequency Values

- `DAILY` - Every day(s)
- `WEEKLY` - Every week(s)
- `MONTHLY` - Every month(s)
- `YEARLY` - Every year(s)

### Common Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `FREQ` | Recurrence frequency (required) | `FREQ=DAILY` |
| `INTERVAL` | How often to repeat (default 1) | `INTERVAL=2` (every other) |
| `COUNT` | Number of occurrences | `COUNT=10` |
| `UNTIL` | End date (ISO format) | `UNTIL=20261231T000000Z` |
| `BYDAY` | Days of week | `BYDAY=MO,WE,FR` |
| `BYMONTHDAY` | Day of month (1-31, -1 for last) | `BYMONTHDAY=15` |
| `BYSETPOS` | Position in set | `BYSETPOS=3` (third occurrence) |
| `BYMONTH` | Months of year (1-12) | `BYMONTH=3,6,9,12` |

### Weekday Codes

- `MO` - Monday
- `TU` - Tuesday
- `WE` - Wednesday
- `TH` - Thursday
- `FR` - Friday
- `SA` - Saturday
- `SU` - Sunday

You can prefix with a number for position:
- `1MO` - First Monday
- `2TU` - Second Tuesday
- `-1FR` - Last Friday

## API Usage

### Creating a Recurring Task

```python
POST /api/recurring-tasks

{
    "title": "Weekly team meeting",
    "description": "Every Monday at 10 AM",
    "rrule": "FREQ=WEEKLY;BYDAY=MO",
    "start_date": "2025-02-10T10:00:00Z",
    "end_date": "2025-12-31T23:59:59Z"  # Optional
}
```

### Validating RRULE

```python
from app.services.recurrence_engine import RecurrenceEngine

engine = RecurrenceEngine()

# Validate format
is_valid = engine.validate_rrule("FREQ=DAILY;INTERVAL=1")
print(is_valid)  # True
```

### Generating Instances Manually

```python
from datetime import datetime
from app.services.recurrence_engine import RecurrenceEngine

engine = RecurrenceEngine()

# Generate next 30 days
future_dates = engine.generate_future_instances(
    rrule_str="FREQ=WEEKLY;BYDAY=MO,WE,FR",
    start_date=datetime(2025, 2, 10, 9, 0),
    horizon_days=30,
    max_instances=12
)

print([d.strftime("%Y-%m-%d") for d in future_dates])
# ['2025-02-10', '2025-02-12', '2025-02-14', '2025-02-17', ...]
```

### Calculate Next Occurrence

```python
next_date = engine.calculate_next_occurrence(
    rrule_str="FREQ=MONTHLY;BYMONTHDAY=15",
    start_date=datetime(2025, 1, 15),
    after_date=datetime(2025, 2, 20)
)
print(next_date)  # 2025-03-15 00:00:00
```

## Advanced Examples

### Complex Weekly Pattern

```python
# Every Monday, Wednesday, Friday at 9 AM for 20 occurrences
rrule = "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=20"
start_date = datetime(2025, 2, 10, 9, 0)
```

### Last Day Patterns

```python
# Last day of every month
rrule = "FREQ=MONTHLY;BYMONTHDAY=-1"

# Last Friday of every month
rrule = "FREQ=MONTHLY;BYDAY=-1FR"
```

### Multiple Intervals

```python
# First and third Monday of every month
rrule = "FREQ=MONTHLY;BYDAY=1MO,3MO"

# Every 15th and 30th of month
rrule = "FREQ=MONTHLY;BYMONTHDAY=15,30"
```

### Combining Filters

```python
# Every Tuesday and Thursday in January, April, July, October
rrule = "FREQ=MONTHLY;BYDAY=TU,TH;BYMONTH=1,4,7,10"
```

## Configuration

Settings in `app/config/settings.py`:

```python
class Settings(BaseSettings):
    # Instance generation
    future_instances_horizon_days: int = 90    # Look ahead 90 days
    max_instances_per_generation: int = 12     # Max instances per run

    # Idempotency
    idempotency_ttl_seconds: int = 86400       # 24 hours

    # Dapr
    dapr_pubsub_name: str = "task-pubsub"
    recurring_task_events_topic: str = "recurring-task-events"
```

## Best Practices

### 1. Use `start_date` as Anchor

The `start_date` defines the time of day and starting point:

```python
# Wrong: Just using date
start_date = datetime(2025, 2, 10)  # Defaults to 00:00:00

# Right: Include time
start_date = datetime(2025, 2, 10, 9, 0)  # 9:00 AM
```

### 2. Limit Horizon

Don't generate too far into the future:

```python
# Good: 90 days ahead
horizon_days = 90

# Risky: 1 year ahead (365 days)
horizon_days = 365  # Could create hundreds of instances
```

### 3. Use `end_date` or `COUNT`

Prevent infinite generation:

```python
# Option 1: End date
end_date = datetime(2025, 12, 31)

# Option 2: Count in RRULE
rrule = "FREQ=DAILY;COUNT=30"
```

### 4. Validate Before Saving

```python
from app.services.recurrence_engine import RecurrenceEngine

def validate_recurring_task(rrule: str) -> bool:
    engine = RecurrenceEngine()
    if not engine.validate_rrule(rrule):
        raise ValueError("Invalid RRULE format")
    return True
```

### 5. Test Complex Patterns

Always test complex patterns before deployment:

```python
# Test generation
dates = engine.generate_future_instances(
    rrule_str="FREQ=MONTHLY;BYDAY=3TH",
    start_date=datetime(2025, 1, 1),
    horizon_days=365,
    max_instances=12
)

print("Generated dates:")
for date in dates:
    print(f"  {date.strftime('%Y-%m-%d %A')}")
```

## Troubleshooting

### Issue 1: No Instances Generated

**Cause:** `start_date` is in the past and `last_generated` was already set.

**Solution:** Use `after_date` parameter or update `last_generated`:

```python
# Generate from specific date
future_dates = engine.generate_future_instances(
    rrule_str=rrule,
    start_date=recurring_task.start_date,
    after_date=recurring_task.last_generated,  # Start after last generation
    horizon_days=90
)
```

### Issue 2: Wrong Time of Day

**Cause:** `start_date` doesn't include time component.

**Solution:** Always include time in `start_date`:

```python
# Wrong
start_date = datetime(2025, 2, 10)  # 00:00:00

# Right
start_date = datetime(2025, 2, 10, 9, 0)  # 09:00:00
```

### Issue 3: Too Many Instances

**Cause:** Large horizon or high frequency without limits.

**Solution:** Use `max_instances` cap and reasonable horizon:

```python
# Good limits
horizon_days = 90        # 3 months
max_instances = 12       # Max 12 instances
```

### Issue 4: Invalid RRULE

**Cause:** Malformed RRULE string.

**Solution:** Validate before saving:

```python
try:
    engine.validate_rrule(rrule_str)
except Exception as e:
    logger.error("Invalid RRULE", rrule=rrule_str, error=str(e))
    raise ValueError(f"Invalid RRULE: {e}")
```

## Testing

### Unit Tests

```python
import pytest
from datetime import datetime
from app.services.recurrence_engine import RecurrenceEngine

def test_daily_recurrence():
    engine = RecurrenceEngine()
    dates = engine.generate_future_instances(
        rrule_str="FREQ=DAILY",
        start_date=datetime(2025, 2, 10),
        horizon_days=7,
        max_instances=5
    )
    assert len(dates) == 5
    assert dates[0] == datetime(2025, 2, 10)
    assert dates[1] == datetime(2025, 2, 11)

def test_weekly_pattern():
    engine = RecurrenceEngine()
    dates = engine.generate_future_instances(
        rrule_str="FREQ=WEEKLY;BYDAY=MO,WE,FR",
        start_date=datetime(2025, 2, 10),  # Monday
        horizon_days=14,
        max_instances=6
    )
    assert len(dates) == 6
    # Verify days are Mon/Wed/Fri
    for date in dates:
        assert date.weekday() in [0, 2, 4]

def test_monthly_pattern():
    engine = RecurrenceEngine()
    dates = engine.generate_future_instances(
        rrule_str="FREQ=MONTHLY;BYMONTHDAY=15",
        start_date=datetime(2025, 1, 15),
        horizon_days=180,
        max_instances=6
    )
    assert len(dates) == 6
    # Verify all on 15th
    for date in dates:
        assert date.day == 15
```

## References

- **RFC 5545 (iCalendar):** https://datatracker.ietf.org/doc/html/rfc5545
- **python-dateutil docs:** https://dateutil.readthedocs.io/en/stable/rrule.html
- **RRULE Tool (visual):** https://icalendar.org/rrule-tool.html
- **RRULE Validator:** https://jakubroztocil.github.io/rrule/

## Quick Reference Table

| Goal | RRULE String |
|------|-------------|
| Every day | `FREQ=DAILY` |
| Every weekday | `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR` |
| Every other week on Friday | `FREQ=WEEKLY;INTERVAL=2;BYDAY=FR` |
| Last day of month | `FREQ=MONTHLY;BYMONTHDAY=-1` |
| First Monday of month | `FREQ=MONTHLY;BYDAY=1MO` |
| 15th of every month | `FREQ=MONTHLY;BYMONTHDAY=15` |
| Every Nov 5th | `FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5` |
| Every 3 months on the 1st | `FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=1` |
| Third Thursday of month | `FREQ=MONTHLY;BYDAY=3TH` |
| Every Mon/Wed/Fri | `FREQ=WEEKLY;BYDAY=MO,WE,FR` |

---

**Need Help?**

- Check logs: `kubectl logs -f deployment/recurring-task-service`
- Validate RRULE: Use `RecurrenceEngine.validate_rrule()`
- Test patterns: Use RRULE online tools before implementing
- Review instances: Query `task_instances` table

**Common Questions:**

Q: How do I skip a single occurrence?
A: Mark the TaskInstance as `is_generated=True` without creating a task.

Q: Can I modify past instances?
A: No, instances are immutable. Create a new recurring task with different rules.

Q: How do I stop a recurring task?
A: Set `is_active=False` or update `end_date` to now.
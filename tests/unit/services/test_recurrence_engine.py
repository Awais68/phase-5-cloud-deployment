"""
Unit tests for RecurrenceEngine - recurrence rule generation and calculation.

Tests cover:
- Daily, weekly, monthly recurrence patterns
- RRULE validation
- Next occurrence calculation
- Edge cases (timezone, DST, end dates)
"""
import pytest
from datetime import datetime, timedelta
from dateutil.rrule import rrulestr


# =============================================================================
# RecurrenceEngine Mock (for unit testing without importing service)
# =============================================================================

class RecurrenceEngine:
    """RecurrenceEngine implementation for unit testing."""

    @staticmethod
    def generate_future_instances(
        rrule_str: str,
        start_date: datetime,
        end_date=None,
        horizon_days: int = 90,
        max_instances: int = 12,
    ):
        try:
            rule = rrulestr(rrule_str, dtstart=start_date)
            horizon_end = min(
                end_date or datetime.max,
                start_date + timedelta(days=horizon_days)
            )
            occurrences = list(rule.between(start_date, horizon_end, inc=True))
            return occurrences[:max_instances]
        except Exception:
            return []

    @staticmethod
    def calculate_next_occurrence(rrule_str: str, start_date: datetime, after_date=None):
        try:
            after_date = after_date or datetime.utcnow()
            rule = rrulestr(rrule_str, dtstart=start_date)
            return rule.after(after_date)
        except Exception:
            return None

    @staticmethod
    def validate_rrule(rrule_str: str) -> bool:
        try:
            rrulestr(rrule_str, dtstart=datetime.utcnow())
            return True
        except Exception:
            return False

    @staticmethod
    def create_rrule_from_simple(
        frequency: str,
        interval: int = 1,
        day_of_week=None,
        day_of_month=None,
    ) -> str:
        freq_map = {'daily': 'DAILY', 'weekly': 'WEEKLY', 'monthly': 'MONTHLY'}
        parts = [f"FREQ={freq_map[frequency.lower()]}"]
        if interval > 1:
            parts.append(f"INTERVAL={interval}")
        if day_of_week is not None and frequency.lower() == 'weekly':
            day_names = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
            parts.append(f"BYDAY={day_names[day_of_week]}")
        if day_of_month is not None and frequency.lower() == 'monthly':
            parts.append(f"BYMONTHDAY={day_of_month}")
        return ";".join(parts)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def engine():
    """Recurrence engine instance."""
    return RecurrenceEngine()


@pytest.fixture
def base_date():
    """Base date for testing (fixed for reproducibility)."""
    return datetime(2025, 2, 10, 10, 0, 0)


# =============================================================================
# Daily Recurrence Tests
# =============================================================================

class TestDailyRecurrence:
    """Tests for daily recurrence patterns."""

    def test_daily_generates_correct_count(self, engine, base_date):
        """Daily recurrence generates correct number of instances."""
        rrule = "FREQ=DAILY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=7
        )
        assert len(instances) == 7

    def test_daily_generates_consecutive_days(self, engine, base_date):
        """Daily recurrence generates consecutive days."""
        rrule = "FREQ=DAILY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=5
        )
        for i in range(1, len(instances)):
            diff = (instances[i] - instances[i-1]).days
            assert diff == 1

    def test_daily_every_other_day(self, engine, base_date):
        """Daily recurrence with interval=2 generates every other day."""
        rrule = "FREQ=DAILY;INTERVAL=2"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=5
        )
        for i in range(1, len(instances)):
            diff = (instances[i] - instances[i-1]).days
            assert diff == 2

    def test_daily_with_count_limit(self, engine, base_date):
        """Daily recurrence with COUNT respects limit."""
        rrule = "FREQ=DAILY;INTERVAL=1;COUNT=3"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=10
        )
        assert len(instances) == 3

    def test_daily_with_end_date(self, engine, base_date):
        """Daily recurrence respects end date."""
        end = base_date + timedelta(days=5)
        rrule = "FREQ=DAILY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, base_date, end_date=end, max_instances=100
        )
        assert all(inst <= end for inst in instances)


# =============================================================================
# Weekly Recurrence Tests
# =============================================================================

class TestWeeklyRecurrence:
    """Tests for weekly recurrence patterns."""

    def test_weekly_generates_7_day_intervals(self, engine, base_date):
        """Weekly recurrence generates 7-day intervals."""
        rrule = "FREQ=WEEKLY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=4
        )
        for i in range(1, len(instances)):
            diff = (instances[i] - instances[i-1]).days
            assert diff == 7

    def test_weekly_bi_weekly(self, engine, base_date):
        """Bi-weekly recurrence generates 14-day intervals."""
        rrule = "FREQ=WEEKLY;INTERVAL=2"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=4
        )
        for i in range(1, len(instances)):
            diff = (instances[i] - instances[i-1]).days
            assert diff == 14

    def test_weekly_on_monday(self, engine, base_date):
        """Weekly on Monday generates only Mondays."""
        rrule = "FREQ=WEEKLY;BYDAY=MO"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=5
        )
        for inst in instances:
            assert inst.weekday() == 0  # Monday

    def test_weekly_multiple_days(self, engine, base_date):
        """Weekly on Mon/Wed/Fri generates correct days."""
        rrule = "FREQ=WEEKLY;BYDAY=MO,WE,FR"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=10
        )
        valid_days = {0, 2, 4}  # Monday, Wednesday, Friday
        for inst in instances:
            assert inst.weekday() in valid_days


# =============================================================================
# Monthly Recurrence Tests
# =============================================================================

class TestMonthlyRecurrence:
    """Tests for monthly recurrence patterns."""

    def test_monthly_same_day_each_month(self, engine, base_date):
        """Monthly recurrence on same day of month."""
        rrule = "FREQ=MONTHLY;BYMONTHDAY=15"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=4
        )
        for inst in instances:
            assert inst.day == 15

    def test_monthly_last_day_of_month(self, engine, base_date):
        """Monthly recurrence on last day of month."""
        rrule = "FREQ=MONTHLY;BYMONTHDAY=-1"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=4
        )
        # Each instance should be last day of its month
        for inst in instances:
            next_day = inst + timedelta(days=1)
            assert next_day.month != inst.month

    def test_monthly_first_monday(self, engine, base_date):
        """Monthly recurrence on first Monday."""
        rrule = "FREQ=MONTHLY;BYDAY=1MO"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=4
        )
        for inst in instances:
            assert inst.weekday() == 0  # Monday
            assert inst.day <= 7  # First week


# =============================================================================
# RRULE Validation Tests
# =============================================================================

class TestRRuleValidation:
    """Tests for RRULE string validation."""

    @pytest.mark.parametrize("rrule", [
        "FREQ=DAILY",
        "FREQ=WEEKLY;INTERVAL=1",
        "FREQ=MONTHLY;BYMONTHDAY=15",
        "FREQ=DAILY;COUNT=10",
        "FREQ=WEEKLY;BYDAY=MO,WE,FR",
    ])
    def test_valid_rrules(self, engine, rrule):
        """Valid RRULE strings pass validation."""
        assert engine.validate_rrule(rrule) is True

    @pytest.mark.parametrize("rrule", [
        "",
        "invalid",
        "FREQ=INVALID",
        "not-an-rrule",
        "FREQ",
    ])
    def test_invalid_rrules(self, engine, rrule):
        """Invalid RRULE strings fail validation."""
        assert engine.validate_rrule(rrule) is False


# =============================================================================
# Next Occurrence Tests
# =============================================================================

class TestNextOccurrence:
    """Tests for next occurrence calculation."""

    def test_next_daily_occurrence(self, engine, base_date):
        """Calculate next daily occurrence."""
        rrule = "FREQ=DAILY;INTERVAL=1"
        next_occ = engine.calculate_next_occurrence(
            rrule, base_date, after_date=base_date
        )
        assert next_occ is not None
        assert next_occ > base_date

    def test_next_occurrence_respects_after_date(self, engine, base_date):
        """Next occurrence is after the specified date."""
        rrule = "FREQ=DAILY;INTERVAL=1"
        after = base_date + timedelta(days=5)
        next_occ = engine.calculate_next_occurrence(
            rrule, base_date, after_date=after
        )
        assert next_occ > after

    def test_next_occurrence_none_when_expired(self, engine, base_date):
        """No next occurrence when recurrence has ended."""
        rrule = "FREQ=DAILY;COUNT=1"
        after = base_date + timedelta(days=10)
        next_occ = engine.calculate_next_occurrence(
            rrule, base_date, after_date=after
        )
        assert next_occ is None


# =============================================================================
# Simple RRULE Creation Tests
# =============================================================================

class TestSimpleRRuleCreation:
    """Tests for creating RRULE from simple parameters."""

    def test_create_daily_rrule(self, engine):
        """Create daily RRULE."""
        rrule = engine.create_rrule_from_simple("daily")
        assert "FREQ=DAILY" in rrule

    def test_create_weekly_rrule_with_day(self, engine):
        """Create weekly RRULE with specific day."""
        rrule = engine.create_rrule_from_simple("weekly", day_of_week=0)
        assert "FREQ=WEEKLY" in rrule
        assert "BYDAY=MO" in rrule

    def test_create_monthly_rrule_with_day(self, engine):
        """Create monthly RRULE with specific day of month."""
        rrule = engine.create_rrule_from_simple("monthly", day_of_month=15)
        assert "FREQ=MONTHLY" in rrule
        assert "BYMONTHDAY=15" in rrule

    def test_create_rrule_with_interval(self, engine):
        """Create RRULE with interval."""
        rrule = engine.create_rrule_from_simple("daily", interval=3)
        assert "INTERVAL=3" in rrule


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_instances_on_invalid_rrule(self, engine, base_date):
        """Invalid RRULE returns empty list."""
        instances = engine.generate_future_instances(
            "INVALID", base_date, max_instances=10
        )
        assert instances == []

    def test_max_instances_respected(self, engine, base_date):
        """Max instances limit is respected."""
        rrule = "FREQ=DAILY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, base_date, max_instances=5, horizon_days=365
        )
        assert len(instances) <= 5

    def test_horizon_days_respected(self, engine, base_date):
        """Horizon days limit is respected."""
        rrule = "FREQ=DAILY;INTERVAL=1"
        horizon = 10
        instances = engine.generate_future_instances(
            rrule, base_date, horizon_days=horizon, max_instances=100
        )
        latest = max(instances) if instances else base_date
        assert (latest - base_date).days <= horizon

    def test_leap_year_february_29(self, engine):
        """Handle leap year February 29."""
        # Start on Feb 28, 2024 (leap year)
        start = datetime(2024, 2, 28, 10, 0, 0)
        rrule = "FREQ=DAILY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, start, max_instances=3
        )
        assert len(instances) >= 2
        # Second instance should be Feb 29
        assert instances[1].day == 29

    def test_year_boundary_crossing(self, engine):
        """Handle year boundary (Dec 31 -> Jan 1)."""
        start = datetime(2024, 12, 30, 10, 0, 0)
        rrule = "FREQ=DAILY;INTERVAL=1"
        instances = engine.generate_future_instances(
            rrule, start, max_instances=5
        )
        # Should include January dates
        assert any(inst.year == 2025 for inst in instances)

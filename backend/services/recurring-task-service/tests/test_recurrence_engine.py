"""
Unit tests for RecurrenceEngine.

Tests RRULE parsing, generation, and validation.
"""
import pytest
from datetime import datetime, timedelta
from app.services.recurrence_engine import RecurrenceEngine


@pytest.fixture
def engine():
    """Provide RecurrenceEngine instance."""
    return RecurrenceEngine()


class TestDailyPatterns:
    """Test daily recurrence patterns."""

    def test_simple_daily(self, engine):
        """Test simple daily recurrence."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY",
            start_date=datetime(2025, 2, 10, 9, 0),
            horizon_days=7,
            max_instances=5
        )
        assert len(dates) == 5
        assert dates[0] == datetime(2025, 2, 10, 9, 0)
        assert dates[1] == datetime(2025, 2, 11, 9, 0)
        assert dates[4] == datetime(2025, 2, 14, 9, 0)

    def test_daily_with_interval(self, engine):
        """Test daily with interval."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY;INTERVAL=3",
            start_date=datetime(2025, 2, 10, 9, 0),
            horizon_days=15,
            max_instances=5
        )
        assert len(dates) == 5
        assert dates[0].day == 10
        assert dates[1].day == 13
        assert dates[2].day == 16

    def test_daily_with_count(self, engine):
        """Test daily with count limit."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY;COUNT=3",
            start_date=datetime(2025, 2, 10, 9, 0),
            horizon_days=30,
            max_instances=10
        )
        # Should respect RRULE count
        assert len(dates) == 3


class TestWeeklyPatterns:
    """Test weekly recurrence patterns."""

    def test_weekly_single_day(self, engine):
        """Test weekly on single day."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=WEEKLY;BYDAY=MO",
            start_date=datetime(2025, 2, 10, 10, 0),  # Monday
            horizon_days=30,
            max_instances=4
        )
        assert len(dates) == 4
        # All should be Mondays (weekday 0)
        for date in dates:
            assert date.weekday() == 0

    def test_weekly_multiple_days(self, engine):
        """Test weekly on multiple days."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=WEEKLY;BYDAY=MO,WE,FR",
            start_date=datetime(2025, 2, 10, 9, 0),  # Monday
            horizon_days=14,
            max_instances=6
        )
        assert len(dates) == 6
        # Should be Mon (0), Wed (2), Fri (4)
        for date in dates:
            assert date.weekday() in [0, 2, 4]

    def test_biweekly(self, engine):
        """Test bi-weekly pattern."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=WEEKLY;INTERVAL=2;BYDAY=TU",
            start_date=datetime(2025, 2, 11, 14, 0),  # Tuesday
            horizon_days=60,
            max_instances=4
        )
        assert len(dates) == 4
        # All Tuesdays (weekday 1)
        for date in dates:
            assert date.weekday() == 1
        # 14 days apart
        assert (dates[1] - dates[0]).days == 14

    def test_weekdays_only(self, engine):
        """Test weekdays only pattern."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
            start_date=datetime(2025, 2, 10, 9, 0),
            horizon_days=14,
            max_instances=10
        )
        assert len(dates) == 10
        # No weekends (5=Sat, 6=Sun)
        for date in dates:
            assert date.weekday() not in [5, 6]


class TestMonthlyPatterns:
    """Test monthly recurrence patterns."""

    def test_monthly_by_day(self, engine):
        """Test monthly on specific day."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYMONTHDAY=15",
            start_date=datetime(2025, 1, 15, 14, 0),
            horizon_days=180,
            max_instances=6
        )
        assert len(dates) == 6
        # All on 15th
        for date in dates:
            assert date.day == 15

    def test_monthly_last_day(self, engine):
        """Test last day of month."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYMONTHDAY=-1",
            start_date=datetime(2025, 1, 31, 23, 59),
            horizon_days=180,
            max_instances=6
        )
        assert len(dates) == 6
        # Check last day logic
        expected_days = [31, 28, 31, 30, 31, 30]  # Jan-Jun 2025
        for i, date in enumerate(dates):
            assert date.day == expected_days[i]

    def test_monthly_first_monday(self, engine):
        """Test first Monday of month."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYDAY=1MO",
            start_date=datetime(2025, 2, 3, 10, 0),  # First Mon of Feb
            horizon_days=180,
            max_instances=6
        )
        assert len(dates) == 6
        # All Mondays
        for date in dates:
            assert date.weekday() == 0
        # All in first week (day <= 7)
        for date in dates:
            assert date.day <= 7

    def test_monthly_third_thursday(self, engine):
        """Test third Thursday of month."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYDAY=3TH",
            start_date=datetime(2025, 1, 16, 15, 0),  # Third Thu of Jan
            horizon_days=180,
            max_instances=6
        )
        assert len(dates) == 6
        # All Thursdays
        for date in dates:
            assert date.weekday() == 3
        # All in third week (day 15-21)
        for date in dates:
            assert 15 <= date.day <= 21

    def test_quarterly(self, engine):
        """Test quarterly pattern."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=1",
            start_date=datetime(2025, 1, 1, 9, 0),
            horizon_days=365,
            max_instances=4
        )
        assert len(dates) == 4
        # All on 1st
        for date in dates:
            assert date.day == 1
        # Months: Jan, Apr, Jul, Oct
        assert dates[0].month == 1
        assert dates[1].month == 4
        assert dates[2].month == 7
        assert dates[3].month == 10


class TestYearlyPatterns:
    """Test yearly recurrence patterns."""

    def test_yearly_simple(self, engine):
        """Test simple yearly recurrence."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=YEARLY",
            start_date=datetime(2025, 3, 15, 0, 0),
            horizon_days=1100,  # ~3 years
            max_instances=3
        )
        assert len(dates) == 3
        # All on March 15
        for date in dates:
            assert date.month == 3
            assert date.day == 15

    def test_yearly_specific_date(self, engine):
        """Test yearly on specific date."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5",
            start_date=datetime(2025, 11, 5, 9, 0),
            horizon_days=1100,
            max_instances=3
        )
        assert len(dates) == 3
        # All on Nov 5
        for date in dates:
            assert date.month == 11
            assert date.day == 5


class TestComplexPatterns:
    """Test complex recurrence patterns."""

    def test_quarterly_first_friday(self, engine):
        """Test quarterly first Friday."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYDAY=1FR;BYMONTH=3,6,9,12",
            start_date=datetime(2025, 3, 7, 10, 0),
            horizon_days=365,
            max_instances=4
        )
        assert len(dates) == 4
        # All Fridays
        for date in dates:
            assert date.weekday() == 4
        # Correct months
        assert dates[0].month == 3
        assert dates[1].month == 6
        assert dates[2].month == 9
        assert dates[3].month == 12

    def test_multiple_days_of_month(self, engine):
        """Test multiple days of month."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYMONTHDAY=5,15,25",
            start_date=datetime(2025, 2, 5, 9, 0),
            horizon_days=90,
            max_instances=9
        )
        assert len(dates) == 9
        # Days should be 5, 15, or 25
        for date in dates:
            assert date.day in [5, 15, 25]


class TestEndDate:
    """Test recurrence with end dates."""

    def test_with_end_date(self, engine):
        """Test recurrence respects end_date."""
        end_date = datetime(2025, 2, 20, 23, 59)
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY",
            start_date=datetime(2025, 2, 10, 9, 0),
            end_date=end_date,
            horizon_days=365,
            max_instances=100
        )
        # Should stop at end_date
        assert all(d <= end_date for d in dates)
        assert len(dates) == 11  # Feb 10-20 inclusive

    def test_horizon_before_end_date(self, engine):
        """Test horizon limits before end_date."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY",
            start_date=datetime(2025, 2, 10, 9, 0),
            end_date=datetime(2025, 12, 31, 23, 59),
            horizon_days=7,  # Only 7 days
            max_instances=100
        )
        # Should be limited by horizon
        assert len(dates) == 7


class TestNextOccurrence:
    """Test calculating next occurrence."""

    def test_next_after_date(self, engine):
        """Test next occurrence after specific date."""
        next_dt = engine.calculate_next_occurrence(
            rrule_str="FREQ=MONTHLY;BYMONTHDAY=15",
            start_date=datetime(2025, 1, 15),
            after_date=datetime(2025, 6, 20)
        )
        assert next_dt is not None
        assert next_dt.year == 2025
        assert next_dt.month == 7
        assert next_dt.day == 15

    def test_next_with_weekly(self, engine):
        """Test next with weekly pattern."""
        next_dt = engine.calculate_next_occurrence(
            rrule_str="FREQ=WEEKLY;BYDAY=MO",
            start_date=datetime(2025, 2, 10),  # Monday
            after_date=datetime(2025, 2, 12)    # Wednesday
        )
        assert next_dt is not None
        # Next Monday after Feb 12 is Feb 17
        assert next_dt.day == 17
        assert next_dt.weekday() == 0


class TestValidation:
    """Test RRULE validation."""

    def test_valid_rrules(self, engine):
        """Test validation of valid RRULEs."""
        valid = [
            "FREQ=DAILY",
            "FREQ=WEEKLY;BYDAY=MO,WE,FR",
            "FREQ=MONTHLY;BYMONTHDAY=15",
            "FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5",
            "FREQ=DAILY;INTERVAL=2;COUNT=10",
        ]
        for rrule in valid:
            assert engine.validate_rrule(rrule), f"Should be valid: {rrule}"

    def test_invalid_rrules(self, engine):
        """Test validation rejects invalid RRULEs."""
        invalid = [
            "INVALID",
            "FREQ=UNKNOWN",
            "BYDAY=MO",  # Missing FREQ
            "",
        ]
        for rrule in invalid:
            assert not engine.validate_rrule(rrule), f"Should be invalid: {rrule}"


class TestSimpleRRuleCreation:
    """Test creating RRULE from simple parameters."""

    def test_daily_simple(self, engine):
        """Test creating daily RRULE."""
        rrule = engine.create_rrule_from_simple(
            frequency='daily',
            interval=1
        )
        assert rrule == "FREQ=DAILY"

    def test_daily_with_interval(self, engine):
        """Test daily with interval."""
        rrule = engine.create_rrule_from_simple(
            frequency='daily',
            interval=3
        )
        assert rrule == "FREQ=DAILY;INTERVAL=3"

    def test_weekly_with_day(self, engine):
        """Test weekly with specific day."""
        rrule = engine.create_rrule_from_simple(
            frequency='weekly',
            interval=1,
            day_of_week=0  # Monday
        )
        assert rrule == "FREQ=WEEKLY;BYDAY=MO"

    def test_monthly_with_day(self, engine):
        """Test monthly with specific day."""
        rrule = engine.create_rrule_from_simple(
            frequency='monthly',
            interval=1,
            day_of_month=15
        )
        assert rrule == "FREQ=MONTHLY;BYMONTHDAY=15"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_result(self, engine):
        """Test when no occurrences in horizon."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=YEARLY",
            start_date=datetime(2025, 1, 1),
            horizon_days=30,  # Too short for yearly
            max_instances=10
        )
        # Should have at least start_date
        assert len(dates) >= 1

    def test_max_instances_limit(self, engine):
        """Test max_instances cap is respected."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY",
            start_date=datetime(2025, 2, 10),
            horizon_days=365,
            max_instances=5
        )
        assert len(dates) == 5

    def test_start_date_preserves_time(self, engine):
        """Test that start_date time is preserved."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=DAILY",
            start_date=datetime(2025, 2, 10, 14, 30, 0),
            horizon_days=3,
            max_instances=3
        )
        # All should have same time
        for date in dates:
            assert date.hour == 14
            assert date.minute == 30

    def test_leap_year_feb_29(self, engine):
        """Test handling of Feb 29 in leap years."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYMONTHDAY=29",
            start_date=datetime(2024, 1, 29),  # 2024 is leap year
            horizon_days=365,
            max_instances=12
        )
        # Feb 29 should be included in 2024
        feb_dates = [d for d in dates if d.month == 2]
        assert any(d.day == 29 for d in feb_dates)


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_daily_standup(self, engine):
        """Test daily standup pattern."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
            start_date=datetime(2025, 2, 10, 9, 30),
            horizon_days=14,
            max_instances=10
        )
        assert len(dates) == 10
        # No weekends
        for date in dates:
            assert date.weekday() < 5

    def test_sprint_planning(self, engine):
        """Test bi-weekly sprint planning."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=WEEKLY;INTERVAL=2;BYDAY=MO",
            start_date=datetime(2025, 2, 10, 14, 0),
            horizon_days=90,
            max_instances=6
        )
        assert len(dates) == 6
        # 14 days apart
        for i in range(len(dates) - 1):
            delta = (dates[i + 1] - dates[i]).days
            assert delta == 14

    def test_monthly_report(self, engine):
        """Test monthly report on 1st."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYMONTHDAY=1",
            start_date=datetime(2025, 2, 1, 9, 0),
            horizon_days=180,
            max_instances=6
        )
        assert len(dates) == 6
        # All on 1st
        for date in dates:
            assert date.day == 1

    def test_quarterly_review(self, engine):
        """Test quarterly review pattern."""
        dates = engine.generate_future_instances(
            rrule_str="FREQ=MONTHLY;BYDAY=-1FR;BYMONTH=3,6,9,12",
            start_date=datetime(2025, 1, 1, 15, 0),
            horizon_days=365,
            max_instances=4
        )
        assert len(dates) == 4
        # All Fridays
        for date in dates:
            assert date.weekday() == 4
        # Correct months
        assert [d.month for d in dates] == [3, 6, 9, 12]

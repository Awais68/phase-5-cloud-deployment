"""
Practical RRULE examples for recurring task service.

Run this file to see various recurrence patterns in action.
"""
from datetime import datetime, timedelta
from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY, YEARLY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_occurrences(rule, title: str, count: int = 5):
    """Print first N occurrences of a rule."""
    print(f"\n{title}")
    print("-" * 70)
    occurrences = list(rule[:count])
    for i, dt in enumerate(occurrences, 1):
        print(f"  {i}. {dt.strftime('%Y-%m-%d %A %H:%M')}")


def example_daily_patterns():
    """Daily recurrence patterns."""
    print_section("DAILY PATTERNS")

    start = datetime(2025, 2, 10, 9, 0)  # Monday at 9 AM

    # Example 1: Every day
    rule = rrule(DAILY, dtstart=start, count=5)
    print_occurrences(rule, "1. Every day at 9 AM")
    print(f"   RRULE: FREQ=DAILY")

    # Example 2: Every 3 days
    rule = rrule(DAILY, interval=3, dtstart=start, count=5)
    print_occurrences(rule, "2. Every 3 days")
    print(f"   RRULE: FREQ=DAILY;INTERVAL=3")

    # Example 3: Using rrulestr (string parsing)
    rule = rrulestr("FREQ=DAILY;COUNT=5", dtstart=start)
    print_occurrences(rule, "3. Daily for 5 occurrences (using rrulestr)")
    print(f"   RRULE: FREQ=DAILY;COUNT=5")


def example_weekly_patterns():
    """Weekly recurrence patterns."""
    print_section("WEEKLY PATTERNS")

    start = datetime(2025, 2, 10, 10, 0)  # Monday at 10 AM

    # Example 1: Every Monday
    rule = rrule(WEEKLY, byweekday=MO, dtstart=start, count=4)
    print_occurrences(rule, "1. Every Monday at 10 AM")
    print(f"   RRULE: FREQ=WEEKLY;BYDAY=MO")

    # Example 2: Every Monday, Wednesday, Friday
    rule = rrule(WEEKLY, byweekday=(MO, WE, FR), dtstart=start, count=6)
    print_occurrences(rule, "2. Every Mon/Wed/Fri")
    print(f"   RRULE: FREQ=WEEKLY;BYDAY=MO,WE,FR")

    # Example 3: Every other week on Tuesday
    rule = rrule(WEEKLY, interval=2, byweekday=TU, dtstart=start, count=4)
    print_occurrences(rule, "3. Bi-weekly on Tuesday")
    print(f"   RRULE: FREQ=WEEKLY;INTERVAL=2;BYDAY=TU")

    # Example 4: Weekdays only
    rule = rrule(WEEKLY, byweekday=(MO, TU, WE, TH, FR), dtstart=start, count=10)
    print_occurrences(rule, "4. Every weekday (Mon-Fri)")
    print(f"   RRULE: FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR")


def example_monthly_patterns():
    """Monthly recurrence patterns."""
    print_section("MONTHLY PATTERNS")

    start = datetime(2025, 1, 15, 14, 0)  # Jan 15 at 2 PM

    # Example 1: 15th of every month
    rule = rrule(MONTHLY, bymonthday=15, dtstart=start, count=6)
    print_occurrences(rule, "1. 15th of every month")
    print(f"   RRULE: FREQ=MONTHLY;BYMONTHDAY=15")

    # Example 2: Last day of month
    rule = rrule(MONTHLY, bymonthday=-1, dtstart=start, count=6)
    print_occurrences(rule, "2. Last day of every month")
    print(f"   RRULE: FREQ=MONTHLY;BYMONTHDAY=-1")

    # Example 3: First Monday of month
    rule = rrule(MONTHLY, byweekday=MO, bysetpos=1, dtstart=start, count=6)
    print_occurrences(rule, "3. First Monday of every month")
    print(f"   RRULE: FREQ=MONTHLY;BYDAY=1MO")

    # Example 4: Third Thursday of month
    rule = rrule(MONTHLY, byweekday=TH, bysetpos=3, dtstart=start, count=6)
    print_occurrences(rule, "4. Third Thursday of every month")
    print(f"   RRULE: FREQ=MONTHLY;BYDAY=3TH")

    # Example 5: Last Friday of month
    rule = rrule(MONTHLY, byweekday=FR, bysetpos=-1, dtstart=start, count=6)
    print_occurrences(rule, "5. Last Friday of every month")
    print(f"   RRULE: FREQ=MONTHLY;BYDAY=-1FR")

    # Example 6: Every 3 months on the 1st
    rule = rrule(MONTHLY, interval=3, bymonthday=1, dtstart=start, count=4)
    print_occurrences(rule, "6. Quarterly on the 1st")
    print(f"   RRULE: FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=1")


def example_yearly_patterns():
    """Yearly recurrence patterns."""
    print_section("YEARLY PATTERNS")

    start = datetime(2025, 1, 1, 9, 0)

    # Example 1: Every year on Nov 5
    rule = rrule(YEARLY, bymonth=11, bymonthday=5, dtstart=start, count=3)
    print_occurrences(rule, "1. Every November 5th")
    print(f"   RRULE: FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5")

    # Example 2: Birthday (every year on specific date)
    birth_start = datetime(2025, 3, 15, 0, 0)
    rule = rrule(YEARLY, dtstart=birth_start, count=5)
    print_occurrences(rule, "2. Annual event (e.g., birthday)")
    print(f"   RRULE: FREQ=YEARLY")


def example_complex_patterns():
    """Complex and combined patterns."""
    print_section("COMPLEX PATTERNS")

    start = datetime(2025, 2, 1, 10, 0)

    # Example 1: First Friday of Mar/Jun/Sep/Dec (quarterly)
    rule = rrule(
        MONTHLY,
        byweekday=FR,
        bysetpos=1,
        bymonth=[3, 6, 9, 12],
        dtstart=start,
        count=8
    )
    print_occurrences(rule, "1. Quarterly: First Friday of Mar/Jun/Sep/Dec")
    print(f"   RRULE: FREQ=MONTHLY;BYDAY=1FR;BYMONTH=3,6,9,12")

    # Example 2: Every Tuesday and Thursday in specific months
    rule = rrule(
        MONTHLY,
        byweekday=(TU, TH),
        bymonth=[1, 4, 7, 10],
        dtstart=start,
        count=10
    )
    print_occurrences(rule, "2. Every Tue/Thu in Jan/Apr/Jul/Oct")
    print(f"   RRULE: FREQ=MONTHLY;BYDAY=TU,TH;BYMONTH=1,4,7,10")

    # Example 3: Multiple specific days of month
    rule = rrule(
        MONTHLY,
        bymonthday=[5, 15, 25],
        dtstart=start,
        count=9
    )
    print_occurrences(rule, "3. 5th, 15th, and 25th of every month")
    print(f"   RRULE: FREQ=MONTHLY;BYMONTHDAY=5,15,25")


def example_with_until():
    """Examples using UNTIL (end date)."""
    print_section("WITH END DATE (UNTIL)")

    start = datetime(2025, 2, 10, 9, 0)
    until = datetime(2025, 3, 31, 23, 59, 59)

    # Example 1: Daily until end of March
    rule = rrule(DAILY, dtstart=start, until=until)
    occurrences = list(rule)
    print(f"\n1. Daily from {start.date()} until {until.date()}")
    print(f"   Total occurrences: {len(occurrences)}")
    print(f"   First: {occurrences[0].strftime('%Y-%m-%d')}")
    print(f"   Last: {occurrences[-1].strftime('%Y-%m-%d')}")
    print(f"   RRULE: FREQ=DAILY;UNTIL={until.strftime('%Y%m%dT%H%M%SZ')}")

    # Example 2: Weekly meetings for 2 months
    rule = rrule(WEEKLY, byweekday=MO, dtstart=start, until=until)
    occurrences = list(rule)
    print(f"\n2. Weekly Monday meetings")
    print(f"   Total occurrences: {len(occurrences)}")
    for i, dt in enumerate(occurrences, 1):
        print(f"   {i}. {dt.strftime('%Y-%m-%d %A')}")


def example_between_dates():
    """Using between() to get occurrences in a date range."""
    print_section("OCCURRENCES BETWEEN DATES")

    start = datetime(2025, 1, 1, 9, 0)
    rule = rrule(WEEKLY, byweekday=(MO, WE, FR), dtstart=start)

    # Get occurrences in February 2025
    feb_start = datetime(2025, 2, 1)
    feb_end = datetime(2025, 2, 28, 23, 59, 59)

    feb_occurrences = rule.between(feb_start, feb_end, inc=True)

    print(f"\nOccurrences between {feb_start.date()} and {feb_end.date()}")
    print(f"Rule: Every Mon/Wed/Fri")
    print(f"Total: {len(feb_occurrences)}")
    for dt in feb_occurrences:
        print(f"  - {dt.strftime('%Y-%m-%d %A')}")


def example_after_before():
    """Using after() and before() methods."""
    print_section("NEXT AND PREVIOUS OCCURRENCES")

    start = datetime(2025, 1, 15, 10, 0)
    rule = rrule(MONTHLY, bymonthday=15, dtstart=start)

    reference_date = datetime(2025, 6, 20)

    # Get next occurrence after June 20
    next_occurrence = rule.after(reference_date)
    print(f"\nNext occurrence after {reference_date.date()}:")
    print(f"  {next_occurrence.strftime('%Y-%m-%d %A')}")

    # Get previous occurrence before June 20
    prev_occurrence = rule.before(reference_date)
    print(f"\nPrevious occurrence before {reference_date.date()}:")
    print(f"  {prev_occurrence.strftime('%Y-%m-%d %A')}")


def example_real_world_scenarios():
    """Real-world use case examples."""
    print_section("REAL-WORLD SCENARIOS")

    # Scenario 1: Daily standup (weekdays)
    print("\n1. DAILY STANDUP")
    print("   Description: Team standup every weekday at 9:30 AM")
    start = datetime(2025, 2, 10, 9, 30)
    rule = rrule(WEEKLY, byweekday=(MO, TU, WE, TH, FR), dtstart=start, count=10)
    print(f"   RRULE: FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR")
    for i, dt in enumerate(list(rule)[:5], 1):
        print(f"   {i}. {dt.strftime('%Y-%m-%d %A %H:%M')}")

    # Scenario 2: Sprint planning (bi-weekly)
    print("\n2. SPRINT PLANNING")
    print("   Description: Every other Monday at 2 PM")
    start = datetime(2025, 2, 10, 14, 0)
    rule = rrule(WEEKLY, interval=2, byweekday=MO, dtstart=start, count=6)
    print(f"   RRULE: FREQ=WEEKLY;INTERVAL=2;BYDAY=MO")
    for i, dt in enumerate(list(rule), 1):
        print(f"   {i}. {dt.strftime('%Y-%m-%d %A %H:%M')}")

    # Scenario 3: Monthly report (first business day approximation)
    print("\n3. MONTHLY REPORT")
    print("   Description: 1st of every month at 9 AM")
    start = datetime(2025, 2, 1, 9, 0)
    rule = rrule(MONTHLY, bymonthday=1, dtstart=start, count=6)
    print(f"   RRULE: FREQ=MONTHLY;BYMONTHDAY=1")
    for i, dt in enumerate(list(rule), 1):
        print(f"   {i}. {dt.strftime('%Y-%m-%d %A %H:%M')}")

    # Scenario 4: Quarterly review
    print("\n4. QUARTERLY REVIEW")
    print("   Description: Last Friday of Mar/Jun/Sep/Dec at 3 PM")
    start = datetime(2025, 1, 1, 15, 0)
    rule = rrule(
        MONTHLY,
        byweekday=FR,
        bysetpos=-1,
        bymonth=[3, 6, 9, 12],
        dtstart=start,
        count=8
    )
    print(f"   RRULE: FREQ=MONTHLY;BYDAY=-1FR;BYMONTH=3,6,9,12")
    for i, dt in enumerate(list(rule), 1):
        print(f"   {i}. {dt.strftime('%Y-%m-%d %A %H:%M')}")

    # Scenario 5: Weekly backup check
    print("\n5. BACKUP VERIFICATION")
    print("   Description: Every Sunday at midnight")
    start = datetime(2025, 2, 9, 0, 0)  # Sunday
    rule = rrule(WEEKLY, byweekday=SU, dtstart=start, count=4)
    print(f"   RRULE: FREQ=WEEKLY;BYDAY=SU")
    for i, dt in enumerate(list(rule), 1):
        print(f"   {i}. {dt.strftime('%Y-%m-%d %A %H:%M')}")


def example_validation():
    """Validate RRULE strings."""
    print_section("RRULE VALIDATION")

    valid_rules = [
        "FREQ=DAILY",
        "FREQ=WEEKLY;BYDAY=MO,WE,FR",
        "FREQ=MONTHLY;BYMONTHDAY=15",
        "FREQ=YEARLY;BYMONTH=11;BYMONTHDAY=5",
    ]

    invalid_rules = [
        "FREQ=UNKNOWN",
        "BYDAY=MO",  # Missing FREQ
        "FREQ=DAILY;INVALID=123",
    ]

    print("\nVALID RRULE STRINGS:")
    for rrule_str in valid_rules:
        try:
            rule = rrulestr(rrule_str, dtstart=datetime.now())
            print(f"  ✓ {rrule_str}")
        except Exception as e:
            print(f"  ✗ {rrule_str} - Error: {e}")

    print("\nINVALID RRULE STRINGS:")
    for rrule_str in invalid_rules:
        try:
            rule = rrulestr(rrule_str, dtstart=datetime.now())
            print(f"  ✓ {rrule_str} (unexpectedly valid)")
        except Exception as e:
            print(f"  ✗ {rrule_str} - Error: {type(e).__name__}")


def example_helper_function():
    """Example helper function for creating RRULEs."""
    print_section("HELPER FUNCTION EXAMPLE")

    def create_simple_rrule(frequency: str, interval: int = 1, **kwargs) -> str:
        """
        Create RRULE string from simple parameters.

        Args:
            frequency: 'daily', 'weekly', 'monthly', 'yearly'
            interval: How often to repeat (default 1)
            **kwargs: Additional parameters like day_of_week, day_of_month, etc.

        Returns:
            RRULE string
        """
        freq_map = {
            'daily': 'DAILY',
            'weekly': 'WEEKLY',
            'monthly': 'MONTHLY',
            'yearly': 'YEARLY',
        }

        parts = [f"FREQ={freq_map[frequency.lower()]}"]

        if interval > 1:
            parts.append(f"INTERVAL={interval}")

        # Handle weekday
        if 'day_of_week' in kwargs:
            days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
            day_code = days[kwargs['day_of_week']]
            parts.append(f"BYDAY={day_code}")

        # Handle multiple weekdays
        if 'days_of_week' in kwargs:
            days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
            day_codes = [days[d] for d in kwargs['days_of_week']]
            parts.append(f"BYDAY={','.join(day_codes)}")

        # Handle day of month
        if 'day_of_month' in kwargs:
            parts.append(f"BYMONTHDAY={kwargs['day_of_month']}")

        return ";".join(parts)

    # Examples
    print("\n1. Daily:")
    rrule_str = create_simple_rrule('daily')
    print(f"   {rrule_str}")

    print("\n2. Every 3 days:")
    rrule_str = create_simple_rrule('daily', interval=3)
    print(f"   {rrule_str}")

    print("\n3. Every Monday:")
    rrule_str = create_simple_rrule('weekly', day_of_week=0)
    print(f"   {rrule_str}")

    print("\n4. Mon/Wed/Fri:")
    rrule_str = create_simple_rrule('weekly', days_of_week=[0, 2, 4])
    print(f"   {rrule_str}")

    print("\n5. 15th of every month:")
    rrule_str = create_simple_rrule('monthly', day_of_month=15)
    print(f"   {rrule_str}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  RRULE EXAMPLES FOR RECURRING TASK SERVICE")
    print("=" * 70)

    example_daily_patterns()
    example_weekly_patterns()
    example_monthly_patterns()
    example_yearly_patterns()
    example_complex_patterns()
    example_with_until()
    example_between_dates()
    example_after_before()
    example_real_world_scenarios()
    example_validation()
    example_helper_function()

    print("\n" + "=" * 70)
    print("  END OF EXAMPLES")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

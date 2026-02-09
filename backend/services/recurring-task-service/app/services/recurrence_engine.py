"""
Recurrence calculation engine using python-dateutil.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from dateutil.rrule import rrulestr, rrule, DAILY, WEEKLY, MONTHLY
import structlog

logger = structlog.get_logger()


class RecurrenceEngine:
    """Calculate future task occurrences based on RRULE."""

    @staticmethod
    def generate_future_instances(
        rrule_str: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        horizon_days: int = 90,
        max_instances: int = 12,
    ) -> List[datetime]:
        """
        Generate future task instance dates.

        Args:
            rrule_str: iCalendar RRULE string (e.g., "FREQ=DAILY;INTERVAL=1")
            start_date: Starting date for recurrence
            end_date: Optional end date
            horizon_days: How many days ahead to generate (default 90)
            max_instances: Maximum instances to generate (default 12)

        Returns:
            List of datetime objects representing future occurrences
        """
        try:
            # Parse RRULE
            rule = rrulestr(rrule_str, dtstart=start_date)

            # Calculate horizon
            horizon_end = min(
                end_date or datetime.max,
                start_date + timedelta(days=horizon_days)
            )

            # Generate occurrences
            occurrences = list(rule.between(start_date, horizon_end, inc=True))

            # Limit to max_instances
            occurrences = occurrences[:max_instances]

            logger.info(
                "generated_instances",
                rrule=rrule_str,
                start_date=start_date,
                count=len(occurrences)
            )

            return occurrences

        except Exception as e:
            logger.error(
                "failed_to_generate_instances",
                rrule=rrule_str,
                error=str(e)
            )
            return []

    @staticmethod
    def calculate_next_occurrence(
        rrule_str: str,
        start_date: datetime,
        after_date: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Calculate the next occurrence after a given date.

        Args:
            rrule_str: iCalendar RRULE string
            start_date: Starting date for recurrence
            after_date: Calculate next occurrence after this date (default: now)

        Returns:
            Next occurrence datetime or None
        """
        try:
            after_date = after_date or datetime.utcnow()
            rule = rrulestr(rrule_str, dtstart=start_date)
            next_dt = rule.after(after_date)

            logger.debug(
                "calculated_next_occurrence",
                rrule=rrule_str,
                after_date=after_date,
                next_occurrence=next_dt
            )

            return next_dt

        except Exception as e:
            logger.error(
                "failed_to_calculate_next",
                rrule=rrule_str,
                error=str(e)
            )
            return None

    @staticmethod
    def validate_rrule(rrule_str: str) -> bool:
        """
        Validate RRULE string format.

        Args:
            rrule_str: iCalendar RRULE string

        Returns:
            True if valid, False otherwise
        """
        try:
            rrulestr(rrule_str, dtstart=datetime.utcnow())
            return True
        except Exception:
            return False

    @staticmethod
    def create_rrule_from_simple(
        frequency: str,
        interval: int = 1,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None,
    ) -> str:
        """
        Create RRULE string from simple frequency parameters.

        Args:
            frequency: 'daily', 'weekly', or 'monthly'
            interval: Recurrence interval (default 1)
            day_of_week: For weekly (0=Monday, 6=Sunday)
            day_of_month: For monthly (1-31)

        Returns:
            RRULE string
        """
        freq_map = {
            'daily': 'DAILY',
            'weekly': 'WEEKLY',
            'monthly': 'MONTHLY',
        }

        parts = [f"FREQ={freq_map[frequency.lower()]}"]

        if interval > 1:
            parts.append(f"INTERVAL={interval}")

        if frequency.lower() == 'weekly' and day_of_week is not None:
            days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
            parts.append(f"BYDAY={days[day_of_week]}")

        if frequency.lower() == 'monthly' and day_of_month is not None:
            parts.append(f"BYMONTHDAY={day_of_month}")

        return ";".join(parts)

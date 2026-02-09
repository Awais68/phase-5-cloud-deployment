"""
Task instance generator with idempotency.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
import redis.asyncio as aioredis
import structlog

from app.models.recurring_task import RecurringTask, TaskInstance
from app.services.recurrence_engine import RecurrenceEngine
from app.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


class InstanceGenerator:
    """Generate task instances from recurring tasks."""

    def __init__(self, db_session: AsyncSession, redis_client: aioredis.Redis):
        self.db = db_session
        self.redis = redis_client
        self.engine = RecurrenceEngine()

    async def generate_instances_for_recurring_task(
        self,
        recurring_task: RecurringTask,
        event_id: Optional[str] = None,
    ) -> List[TaskInstance]:
        """
        Generate task instances for a recurring task.

        Args:
            recurring_task: RecurringTask object
            event_id: Event ID for idempotency (optional)

        Returns:
            List of created TaskInstance objects
        """
        # Check idempotency
        if event_id and await self._is_processed(event_id):
            logger.info(
                "event_already_processed",
                event_id=event_id,
                recurring_task_id=recurring_task.id
            )
            return []

        # Calculate future occurrences
        future_dates = self.engine.generate_future_instances(
            rrule_str=recurring_task.rrule,
            start_date=recurring_task.start_date,
            end_date=recurring_task.end_date,
            horizon_days=settings.future_instances_horizon_days,
            max_instances=settings.max_instances_per_generation,
        )

        if not future_dates:
            logger.warning(
                "no_future_occurrences",
                recurring_task_id=recurring_task.id
            )
            return []

        # Create instances with idempotency
        instances = await self._create_instances_batch(
            recurring_task_id=recurring_task.id,
            due_dates=future_dates
        )

        # Update recurring task metadata
        if instances:
            recurring_task.last_generated = datetime.utcnow()
            recurring_task.next_occurrence = future_dates[0] if future_dates else None
            await self.db.commit()

        # Mark event as processed
        if event_id:
            await self._mark_processed(event_id)

        logger.info(
            "instances_generated",
            recurring_task_id=recurring_task.id,
            count=len(instances)
        )

        return instances

    async def _create_instances_batch(
        self,
        recurring_task_id: int,
        due_dates: List[datetime]
    ) -> List[TaskInstance]:
        """
        Create task instances in batch with ON CONFLICT handling.

        Args:
            recurring_task_id: ID of recurring task
            due_dates: List of due dates

        Returns:
            List of created TaskInstance objects
        """
        # Prepare insert values
        values = [
            {
                "recurring_task_id": recurring_task_id,
                "due_date": due_date,
                "is_generated": False,
            }
            for due_date in due_dates
        ]

        # Use INSERT ... ON CONFLICT DO NOTHING for idempotency
        stmt = insert(TaskInstance).values(values).on_conflict_do_nothing(
            index_elements=["recurring_task_id", "due_date"]
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Fetch created instances
        result = await self.db.execute(
            select(TaskInstance).where(
                and_(
                    TaskInstance.recurring_task_id == recurring_task_id,
                    TaskInstance.due_date.in_(due_dates)
                )
            )
        )

        return result.scalars().all()

    async def _is_processed(self, event_id: str) -> bool:
        """Check if event has already been processed."""
        key = f"recurring:event:{event_id}"
        return await self.redis.exists(key) > 0

    async def _mark_processed(self, event_id: str) -> None:
        """Mark event as processed with TTL."""
        key = f"recurring:event:{event_id}"
        await self.redis.setex(
            key,
            settings.idempotency_ttl_seconds,
            "1"
        )

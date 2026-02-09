"""
Dapr subscription endpoints for recurring task events.
"""
from fastapi import APIRouter, Depends, HTTPException
from cloudevents.http import CloudEvent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
import structlog

from app.models.recurring_task import RecurringTask, RecurringTaskEvent
from app.services.instance_generator import InstanceGenerator
from app.config.settings import get_settings

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


@router.post("/dapr/subscribe")
async def subscribe():
    """Dapr subscription configuration."""
    return [
        {
            "pubsubname": settings.dapr_pubsub_name,
            "topic": settings.task_events_topic,
            "route": "/events/task"
        },
        {
            "pubsubname": settings.dapr_pubsub_name,
            "topic": settings.recurring_task_events_topic,
            "route": "/events/recurring-task"
        }
    ]


@router.post("/events/task")
async def handle_task_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Handle task events (created/updated).

    Checks if task has recurring rules and generates instances.
    """
    try:
        data = event.data
        event_type = data.get("event_type")
        task_id = data.get("task_id")

        logger.info(
            "received_task_event",
            event_type=event_type,
            task_id=task_id,
            event_id=event.get_id()
        )

        # Only process if task has recurring information
        if "rrule" not in data or not data["rrule"]:
            logger.debug("task_not_recurring", task_id=task_id)
            return {"status": "ignored"}

        # TODO: Fetch or create RecurringTask from task data
        # For now, just log
        logger.info(
            "processing_recurring_task",
            task_id=task_id,
            rrule=data.get("rrule")
        )

        return {"status": "processed"}

    except Exception as e:
        logger.error(
            "failed_to_handle_task_event",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/recurring-task")
async def handle_recurring_task_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Handle recurring task events (created/updated/deleted).

    Generates task instances based on recurrence rules.
    """
    try:
        data = event.data
        event_id = event.get_id()

        # Parse event
        task_event = RecurringTaskEvent(**data)

        logger.info(
            "received_recurring_task_event",
            event_type=task_event.event_type,
            recurring_task_id=task_event.recurring_task_id,
            event_id=event_id
        )

        # Handle based on event type
        if task_event.event_type in ["created", "updated"]:
            # Fetch recurring task
            result = await db.execute(
                select(RecurringTask).where(
                    RecurringTask.id == task_event.recurring_task_id
                )
            )
            recurring_task = result.scalar_one_or_none()

            if not recurring_task:
                logger.warning(
                    "recurring_task_not_found",
                    recurring_task_id=task_event.recurring_task_id
                )
                return {"status": "not_found"}

            # Generate instances
            generator = InstanceGenerator(db, redis)
            instances = await generator.generate_instances_for_recurring_task(
                recurring_task=recurring_task,
                event_id=event_id
            )

            logger.info(
                "instances_generated_for_event",
                recurring_task_id=recurring_task.id,
                count=len(instances)
            )

            return {
                "status": "processed",
                "instances_generated": len(instances)
            }

        elif task_event.event_type == "deleted":
            # TODO: Mark existing instances as cancelled
            logger.info(
                "recurring_task_deleted",
                recurring_task_id=task_event.recurring_task_id
            )
            return {"status": "processed"}

        else:
            logger.warning("unknown_event_type", event_type=task_event.event_type)
            return {"status": "ignored"}

    except Exception as e:
        logger.error(
            "failed_to_handle_recurring_task_event",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

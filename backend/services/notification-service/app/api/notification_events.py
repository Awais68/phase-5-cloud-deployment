"""
Dapr subscription endpoints for notification events.
"""
from fastapi import APIRouter, Depends, HTTPException
from cloudevents.http import CloudEvent
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import structlog

from app.models.notification import NotificationEvent
from app.services.notification_service import NotificationService
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
            "topic": settings.reminder_events_topic,
            "route": "/events/reminder"
        },
        {
            "pubsubname": settings.dapr_pubsub_name,
            "topic": settings.task_events_topic,
            "route": "/events/task"
        }
    ]


@router.post("/events/reminder")
async def handle_reminder_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Handle reminder events.

    Sends notifications when task reminders are due.
    """
    try:
        data = event.data
        event_id = event.get_id()

        logger.info(
            "received_reminder_event",
            event_id=event_id,
            user_id=data.get("user_id"),
            task_id=data.get("task_id")
        )

        # Create notification event
        notification_event = NotificationEvent(
            event_id=event_id,
            event_type="reminder",
            user_id=data["user_id"],
            task_id=data.get("task_id"),
            subject=f"Task Reminder: {data.get('task_title', 'Task')}",
            message=data.get("message", "Your task is due soon!"),
            template_name="reminder.html",
            template_data={
                "task_title": data.get("task_title"),
                "task_description": data.get("task_description"),
                "due_date": data.get("due_date"),
            }
        )

        # Process notification
        service = NotificationService(db, redis)
        result = await service.process_notification_event(notification_event)

        logger.info(
            "reminder_notification_processed",
            event_id=event_id,
            result=result
        )

        return {"status": "processed", "result": result}

    except Exception as e:
        logger.error(
            "failed_to_handle_reminder_event",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/task")
async def handle_task_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Handle task events (completed, overdue, assigned).

    Sends notifications for task status changes.
    """
    try:
        data = event.data
        event_id = event.get_id()
        event_type = data.get("event_type")

        logger.info(
            "received_task_event",
            event_id=event_id,
            event_type=event_type,
            task_id=data.get("task_id")
        )

        # Only process specific event types
        if event_type not in ["completed", "overdue", "assigned"]:
            logger.debug("ignoring_task_event", event_type=event_type)
            return {"status": "ignored"}

        # Create notification event
        subject_map = {
            "completed": f"Task Completed: {data.get('task_title', 'Task')}",
            "overdue": f"Task Overdue: {data.get('task_title', 'Task')}",
            "assigned": f"New Task Assigned: {data.get('task_title', 'Task')}",
        }

        notification_event = NotificationEvent(
            event_id=event_id,
            event_type=event_type,
            user_id=data["user_id"],
            task_id=data.get("task_id"),
            subject=subject_map.get(event_type, "Task Update"),
            message=data.get("message", "Task status has changed"),
            template_name=f"{event_type}.html",
            template_data={
                "task_title": data.get("task_title"),
                "task_description": data.get("task_description"),
                "timestamp": data.get("timestamp"),
            }
        )

        # Process notification
        service = NotificationService(db, redis)
        result = await service.process_notification_event(notification_event)

        logger.info(
            "task_notification_processed",
            event_id=event_id,
            event_type=event_type,
            result=result
        )

        return {"status": "processed", "result": result}

    except Exception as e:
        logger.error(
            "failed_to_handle_task_event",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

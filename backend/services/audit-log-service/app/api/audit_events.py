"""
Dapr subscription endpoints for audit log events.
"""
from fastapi import APIRouter, Depends, HTTPException
from cloudevents.http import CloudEvent
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import structlog

from app.models.audit_event import AuditEventCreate
from app.services.audit_service import AuditService
from app.config.settings import get_settings

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


@router.post("/dapr/subscribe")
async def subscribe():
    """Dapr subscription configuration for all domain events."""
    return [
        {
            "pubsubname": settings.dapr_pubsub_name,
            "topic": settings.task_events_topic,
            "route": "/events/task"
        },
        {
            "pubsubname": settings.dapr_pubsub_name,
            "topic": settings.user_events_topic,
            "route": "/events/user"
        },
        {
            "pubsubname": settings.dapr_pubsub_name,
            "topic": settings.notification_events_topic,
            "route": "/events/notification"
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
    """Handle task domain events for audit trail."""
    try:
        data = event.data
        event_id = event.get_id()

        logger.info(
            "received_task_event",
            event_id=event_id,
            event_type=data.get("event_type"),
            task_id=data.get("task_id")
        )

        # Create audit event
        audit_event = AuditEventCreate(
            event_id=event_id,
            event_type=data.get("event_type", "unknown"),
            entity_type="task",
            entity_id=data["task_id"],
            user_id=data.get("user_id"),
            user_email=data.get("user_email"),
            action=data.get("action", data.get("event_type", "UNKNOWN").upper()),
            before_state=data.get("before_state"),
            after_state=data.get("after_state"),
            metadata=data.get("metadata", {}),
            request_id=data.get("request_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
        )

        # Store audit event
        service = AuditService(db, redis)
        result = await service.create_audit_event(audit_event)

        return {
            "status": "processed" if result else "duplicate",
            "audit_id": result.id if result else None
        }

    except Exception as e:
        logger.error(
            "failed_to_handle_task_event",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/user")
async def handle_user_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """Handle user domain events for audit trail."""
    try:
        data = event.data
        event_id = event.get_id()

        logger.info(
            "received_user_event",
            event_id=event_id,
            event_type=data.get("event_type"),
            user_id=data.get("user_id")
        )

        audit_event = AuditEventCreate(
            event_id=event_id,
            event_type=data.get("event_type", "unknown"),
            entity_type="user",
            entity_id=data["user_id"],
            user_id=data.get("actor_id"),  # Who performed the action
            user_email=data.get("user_email"),
            action=data.get("action", data.get("event_type", "UNKNOWN").upper()),
            before_state=data.get("before_state"),
            after_state=data.get("after_state"),
            metadata=data.get("metadata", {}),
            request_id=data.get("request_id"),
        )

        service = AuditService(db, redis)
        result = await service.create_audit_event(audit_event)

        return {
            "status": "processed" if result else "duplicate",
            "audit_id": result.id if result else None
        }

    except Exception as e:
        logger.error("failed_to_handle_user_event", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/notification")
async def handle_notification_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """Handle notification events for audit trail."""
    try:
        data = event.data
        event_id = event.get_id()

        audit_event = AuditEventCreate(
            event_id=event_id,
            event_type=data.get("event_type", "notification_sent"),
            entity_type="notification",
            entity_id=data.get("notification_id", 0),
            user_id=data.get("user_id"),
            action="NOTIFY",
            after_state=data,
            metadata=data.get("metadata", {}),
        )

        service = AuditService(db, redis)
        result = await service.create_audit_event(audit_event)

        return {
            "status": "processed" if result else "duplicate",
            "audit_id": result.id if result else None
        }

    except Exception as e:
        logger.error("failed_to_handle_notification_event", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/recurring-task")
async def handle_recurring_task_event(
    event: CloudEvent,
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """Handle recurring task events for audit trail."""
    try:
        data = event.data
        event_id = event.get_id()

        audit_event = AuditEventCreate(
            event_id=event_id,
            event_type=data.get("event_type", "unknown"),
            entity_type="recurring_task",
            entity_id=data.get("recurring_task_id", 0),
            user_id=data.get("user_id"),
            action=data.get("action", data.get("event_type", "UNKNOWN").upper()),
            before_state=data.get("before_state"),
            after_state=data.get("after_state"),
            metadata=data.get("metadata", {}),
        )

        service = AuditService(db, redis)
        result = await service.create_audit_event(audit_event)

        return {
            "status": "processed" if result else "duplicate",
            "audit_id": result.id if result else None
        }

    except Exception as e:
        logger.error("failed_to_handle_recurring_task_event", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

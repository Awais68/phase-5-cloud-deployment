"""
Notification service with multi-channel delivery and rate limiting.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
import structlog
from datetime import datetime, timedelta

from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationChannel,
    NotificationStatus,
    NotificationEvent,
)
from app.channels.email_channel import EmailChannel
from app.channels.websocket_channel import WebSocketChannel
from app.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


class NotificationService:
    """Multi-channel notification delivery service."""

    def __init__(self, db_session: AsyncSession, redis_client: aioredis.Redis):
        self.db = db_session
        self.redis = redis_client
        self.email_channel = EmailChannel()
        self.websocket_channel = WebSocketChannel(redis_client)

    async def process_notification_event(
        self,
        event: NotificationEvent
    ) -> dict:
        """
        Process notification event and deliver via appropriate channels.

        Args:
            event: NotificationEvent object

        Returns:
            Dict with delivery results
        """
        # Check idempotency
        if await self._is_event_processed(event.event_id):
            logger.info("event_already_processed", event_id=event.event_id)
            return {"status": "duplicate", "event_id": event.event_id}

        # Get user preferences
        preferences = await self._get_user_preferences(event.user_id)

        results = {"channels": {}}

        # Deliver via email
        if preferences.email_enabled and preferences.email:
            if await self._check_rate_limit(event.user_id, NotificationChannel.EMAIL):
                email_result = await self._send_email(event, preferences.email)
                results["channels"]["email"] = email_result
            else:
                results["channels"]["email"] = {"status": "rate_limited"}
                logger.warning("email_rate_limited", user_id=event.user_id)

        # Deliver via WebSocket
        if preferences.websocket_enabled:
            if await self._check_rate_limit(event.user_id, NotificationChannel.WEBSOCKET):
                websocket_result = await self._send_websocket(event)
                results["channels"]["websocket"] = websocket_result
            else:
                results["channels"]["websocket"] = {"status": "rate_limited"}
                logger.warning("websocket_rate_limited", user_id=event.user_id)

        # Mark event as processed
        await self._mark_event_processed(event.event_id)

        return results

    async def _send_email(
        self,
        event: NotificationEvent,
        to_email: str
    ) -> dict:
        """Send email notification."""
        try:
            # Create notification record
            notification = Notification(
                user_id=event.user_id,
                task_id=event.task_id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.PENDING,
                subject=event.subject,
                message=event.message,
                template_name=event.template_name,
                template_data=event.template_data,
                event_id=event.event_id,
                event_type=event.event_type,
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Send email
            success = await self.email_channel.send(
                to_email=to_email,
                subject=event.subject,
                message=event.message,
                template_name=event.template_name,
                template_data=event.template_data,
            )

            # Update notification status
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()

            await self.db.commit()

            return {
                "status": "sent" if success else "failed",
                "notification_id": notification.id
            }

        except Exception as e:
            logger.error("email_delivery_failed", error=str(e), exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _send_websocket(
        self,
        event: NotificationEvent
    ) -> dict:
        """Send WebSocket notification."""
        try:
            # Create notification record
            notification = Notification(
                user_id=event.user_id,
                task_id=event.task_id,
                channel=NotificationChannel.WEBSOCKET,
                status=NotificationStatus.PENDING,
                subject=event.subject,
                message=event.message,
                event_id=event.event_id,
                event_type=event.event_type,
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Broadcast via WebSocket
            success = await self.websocket_channel.broadcast(
                user_id=event.user_id,
                notification_data={
                    "type": event.event_type,
                    "subject": event.subject,
                    "message": event.message,
                    "task_id": event.task_id,
                    "timestamp": event.timestamp.isoformat(),
                }
            )

            # Update notification status
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()

            await self.db.commit()

            return {
                "status": "sent" if success else "failed",
                "notification_id": notification.id
            }

        except Exception as e:
            logger.error("websocket_delivery_failed", error=str(e), exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _get_user_preferences(self, user_id: int) -> NotificationPreference:
        """Get user notification preferences."""
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        preferences = result.scalar_one_or_none()

        # Return default preferences if not found
        if not preferences:
            return NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                websocket_enabled=True,
                push_enabled=False,
            )

        return preferences

    async def _check_rate_limit(
        self,
        user_id: int,
        channel: NotificationChannel
    ) -> bool:
        """Check if user has exceeded rate limit for channel."""
        key = f"ratelimit:{user_id}:{channel.value}"
        count = await self.redis.get(key)

        if count is None:
            await self.redis.setex(key, 60, "1")
            return True

        current_count = int(count)
        if current_count >= settings.rate_limit_per_user_per_minute:
            return False

        await self.redis.incr(key)
        return True

    async def _is_event_processed(self, event_id: str) -> bool:
        """Check if event has already been processed."""
        key = f"notification:event:{event_id}"
        return await self.redis.exists(key) > 0

    async def _mark_event_processed(self, event_id: str) -> None:
        """Mark event as processed with TTL."""
        key = f"notification:event:{event_id}"
        await self.redis.setex(
            key,
            settings.idempotency_ttl_seconds,
            "1"
        )

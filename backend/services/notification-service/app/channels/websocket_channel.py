"""
WebSocket notification channel using Redis pub/sub.
"""
from typing import Dict, Any
import redis.asyncio as aioredis
import json
import structlog

from app.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


class WebSocketChannel:
    """WebSocket notification channel via Redis pub/sub."""

    def __init__(self, redis_client: aioredis.Redis):
        """Initialize WebSocket channel."""
        self.redis = redis_client

    async def broadcast(
        self,
        user_id: int,
        notification_data: Dict[str, Any]
    ) -> bool:
        """
        Broadcast notification to user via WebSocket.

        Publishes to Redis channel: `websocket:user:{user_id}`

        Args:
            user_id: Target user ID
            notification_data: Notification payload

        Returns:
            True if published successfully, False otherwise
        """
        try:
            channel = f"websocket:user:{user_id}"
            message = json.dumps(notification_data)

            # Publish to Redis (subscribers will receive)
            await self.redis.publish(channel, message)

            logger.info(
                "websocket_notification_published",
                user_id=user_id,
                channel=channel
            )

            return True

        except Exception as e:
            logger.error(
                "websocket_publish_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return False

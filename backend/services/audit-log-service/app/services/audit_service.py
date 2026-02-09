"""
Audit log service with TimescaleDB storage.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, text
import redis.asyncio as aioredis
import structlog

from app.models.audit_event import AuditEvent, AuditEventCreate, AuditQueryParams
from app.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()


class AuditService:
    """Audit log service with append-only storage."""

    def __init__(self, db_session: AsyncSession, redis_client: aioredis.Redis):
        self.db = db_session
        self.redis = redis_client

    async def create_audit_event(
        self,
        event_data: AuditEventCreate
    ) -> Optional[AuditEvent]:
        """
        Create immutable audit event.

        Args:
            event_data: AuditEventCreate schema

        Returns:
            Created AuditEvent or None if duplicate
        """
        # Check idempotency
        if await self._is_event_processed(event_data.event_id):
            logger.info(
                "audit_event_already_exists",
                event_id=event_data.event_id
            )
            return None

        try:
            # Create audit event
            audit_event = AuditEvent(**event_data.model_dump())

            self.db.add(audit_event)
            await self.db.commit()
            await self.db.refresh(audit_event)

            # Mark as processed
            await self._mark_event_processed(event_data.event_id)

            logger.info(
                "audit_event_created",
                event_id=event_data.event_id,
                entity_type=event_data.entity_type,
                entity_id=event_data.entity_id,
                action=event_data.action
            )

            return audit_event

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "failed_to_create_audit_event",
                event_id=event_data.event_id,
                error=str(e),
                exc_info=True
            )
            return None

    async def query_audit_events(
        self,
        params: AuditQueryParams
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.

        Args:
            params: AuditQueryParams with filter criteria

        Returns:
            List of matching AuditEvent objects
        """
        try:
            # Build query
            query = select(AuditEvent)

            # Apply filters
            filters = []

            if params.entity_type:
                filters.append(AuditEvent.entity_type == params.entity_type)

            if params.entity_id:
                filters.append(AuditEvent.entity_id == params.entity_id)

            if params.user_id:
                filters.append(AuditEvent.user_id == params.user_id)

            if params.event_type:
                filters.append(AuditEvent.event_type == params.event_type)

            if params.action:
                filters.append(AuditEvent.action == params.action)

            if params.start_date:
                filters.append(AuditEvent.timestamp >= params.start_date)

            if params.end_date:
                filters.append(AuditEvent.timestamp <= params.end_date)

            if filters:
                query = query.where(and_(*filters))

            # Order by timestamp descending (most recent first)
            query = query.order_by(AuditEvent.timestamp.desc())

            # Apply pagination
            query = query.limit(params.limit).offset(params.offset)

            # Execute query
            result = await self.db.execute(query)
            events = result.scalars().all()

            logger.info(
                "audit_events_queried",
                count=len(events),
                filters=params.model_dump(exclude_none=True)
            )

            return events

        except Exception as e:
            logger.error(
                "failed_to_query_audit_events",
                error=str(e),
                exc_info=True
            )
            return []

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get complete history for an entity.

        Args:
            entity_type: Entity type (task, user, etc.)
            entity_id: Entity ID
            limit: Maximum results

        Returns:
            List of AuditEvent objects in chronological order
        """
        params = AuditQueryParams(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
        return await self.query_audit_events(params)

    async def get_user_activity(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get user activity in date range.

        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum results

        Returns:
            List of AuditEvent objects
        """
        params = AuditQueryParams(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return await self.query_audit_events(params)

    async def apply_retention_policy(self) -> int:
        """
        Delete audit events older than retention period.

        Returns:
            Number of deleted events
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.retention_days)

            # Delete old events
            result = await self.db.execute(
                text(
                    "DELETE FROM audit_events WHERE timestamp < :cutoff_date"
                ).bindparams(cutoff_date=cutoff_date)
            )

            await self.db.commit()

            deleted_count = result.rowcount

            logger.info(
                "retention_policy_applied",
                cutoff_date=cutoff_date,
                deleted_count=deleted_count
            )

            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "failed_to_apply_retention_policy",
                error=str(e),
                exc_info=True
            )
            return 0

    async def _is_event_processed(self, event_id: str) -> bool:
        """Check if event has already been processed."""
        key = f"audit:event:{event_id}"
        return await self.redis.exists(key) > 0

    async def _mark_event_processed(self, event_id: str) -> None:
        """Mark event as processed with TTL."""
        key = f"audit:event:{event_id}"
        await self.redis.setex(
            key,
            settings.idempotency_ttl_seconds,
            "1"
        )

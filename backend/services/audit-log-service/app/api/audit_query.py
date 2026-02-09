"""
Query API for audit logs.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from typing import Optional, List
from datetime import datetime

from app.models.audit_event import AuditEvent, AuditQueryParams
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/", response_model=List[dict])
async def query_audit_logs(
    entity_type: Optional[str] = Query(None, description="Entity type filter"),
    entity_id: Optional[int] = Query(None, description="Entity ID filter"),
    user_id: Optional[int] = Query(None, description="User ID filter"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    action: Optional[str] = Query(None, description="Action filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Query audit logs with filters.

    Returns audit events matching the specified criteria.
    """
    params = AuditQueryParams(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        event_type=event_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    service = AuditService(db, redis)
    events = await service.query_audit_events(params)

    return [event.model_dump() for event in events]


@router.get("/{entity_type}/{entity_id}", response_model=List[dict])
async def get_entity_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Get complete audit history for a specific entity.

    Returns all audit events for the specified entity in chronological order.
    """
    service = AuditService(db, redis)
    events = await service.get_entity_history(entity_type, entity_id, limit)

    return [event.model_dump() for event in events]


@router.get("/user/{user_id}/activity", response_model=List[dict])
async def get_user_activity(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(lambda: None),
    redis: aioredis.Redis = Depends(lambda: None),
):
    """
    Get user activity audit trail.

    Returns all actions performed by a user in the specified date range.
    """
    service = AuditService(db, redis)
    events = await service.get_user_activity(user_id, start_date, end_date, limit)

    return [event.model_dump() for event in events]

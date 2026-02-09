"""
Audit event models with TimescaleDB hypertable.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import ConfigDict


class AuditEvent(SQLModel, table=True):
    """
    Immutable audit event record.

    Stored in TimescaleDB hypertable for efficient time-series queries.
    """
    __tablename__ = "audit_events"

    # Primary key (auto-increment)
    id: Optional[int] = Field(default=None, primary_key=True)

    # Event identification
    event_id: str = Field(max_length=100, index=True, unique=True)
    event_type: str = Field(max_length=50, index=True)  # created, updated, deleted, etc.

    # Entity information
    entity_type: str = Field(max_length=50, index=True)  # task, user, notification, etc.
    entity_id: int = Field(index=True)

    # User who performed the action
    user_id: Optional[int] = Field(default=None, index=True)
    user_email: Optional[str] = Field(default=None, max_length=255)

    # Action details
    action: str = Field(max_length=50)  # CREATE, UPDATE, DELETE, etc.

    # State changes (JSONB for flexibility)
    before_state: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    after_state: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB)
    )

    # Request tracking
    request_id: Optional[str] = Field(default=None, max_length=100, index=True)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)

    # Timestamp (time-series key)
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        nullable=False
    )

    # Immutability marker
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEventCreate(SQLModel):
    """Schema for creating audit events."""
    event_id: str
    event_type: str
    entity_type: str
    entity_id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditQueryParams(SQLModel):
    """Query parameters for audit log search."""
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    event_type: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

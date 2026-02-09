"""
Notification models.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field, JSON, Column
from sqlalchemy.dialects.postgresql import JSONB


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    WEBSOCKET = "websocket"
    PUSH = "push"  # Future


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationPreference(SQLModel, table=True):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, unique=True)

    # Channel preferences
    email_enabled: bool = Field(default=True)
    websocket_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=False)

    # Email address
    email: Optional[str] = Field(default=None, max_length=255)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Notification(SQLModel, table=True):
    """Notification delivery record."""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id", index=True)

    # Channel and status
    channel: NotificationChannel = Field(index=True)
    status: NotificationStatus = Field(default=NotificationStatus.PENDING, index=True)

    # Content
    subject: str = Field(max_length=500)
    message: str
    template_name: Optional[str] = Field(default=None, max_length=100)
    template_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    # Delivery tracking
    sent_at: Optional[datetime] = Field(default=None)
    failed_at: Optional[datetime] = Field(default=None)
    retry_count: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)

    # Event tracking
    event_id: Optional[str] = Field(default=None, max_length=100, index=True)
    event_type: Optional[str] = Field(default=None, max_length=50)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationEvent(SQLModel):
    """Event payload for notification requests."""
    event_id: str
    event_type: str  # reminder, task_completed, task_overdue, task_assigned
    user_id: int
    task_id: Optional[int] = None

    # Notification content
    subject: str
    message: str
    template_name: Optional[str] = None
    template_data: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)

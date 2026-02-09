"""
RecurringTask models for recurring task service.
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class RecurringTask(SQLModel, table=True):
    """
    RecurringTask model for managing recurring tasks.

    Stores iCalendar RRULE format for maximum flexibility.
    """
    __tablename__ = "recurring_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=200, min_length=1)
    description: Optional[str] = Field(default="", max_length=1000)

    # iCalendar RRULE format (e.g., "FREQ=DAILY;INTERVAL=1")
    rrule: str = Field(max_length=500)

    # Start date for recurrence
    start_date: datetime = Field(default_factory=datetime.utcnow)

    # Optional end date
    end_date: Optional[datetime] = Field(default=None)

    # Track generation
    is_active: bool = Field(default=True)
    last_generated: Optional[datetime] = Field(default=None)
    next_occurrence: Optional[datetime] = Field(default=None, index=True)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskInstance(SQLModel, table=True):
    """
    Generated task instances from recurring tasks.

    Unique constraint on (recurring_task_id, due_date) prevents duplicates.
    """
    __tablename__ = "task_instances"

    id: Optional[int] = Field(default=None, primary_key=True)
    recurring_task_id: int = Field(foreign_key="recurring_tasks.id", index=True)
    task_id: Optional[int] = Field(foreign_key="tasks.id", index=True)

    # When this instance is due
    due_date: datetime = Field(index=True)

    # Status tracking
    is_generated: bool = Field(default=False)
    generated_at: Optional[datetime] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecurringTaskEvent(SQLModel):
    """Event payload for recurring task operations."""
    event_id: str
    event_type: str  # created, updated, deleted, disabled
    recurring_task_id: int
    user_id: int
    rrule: str
    start_date: datetime
    end_date: Optional[datetime] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

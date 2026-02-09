"""
Factory Boy factories for generating test data.

Usage:
    from tests.factories.task_factories import TaskFactory, RecurringTaskFactory
    
    # Create single instance
    task = TaskFactory()
    
    # Create with specific attributes
    task = TaskFactory(title="Custom Title", priority="high")
    
    # Create batch
    tasks = TaskFactory.create_batch(10)
"""
import factory
from factory import Faker, LazyAttribute, Sequence, SubFactory
from datetime import datetime, timedelta
import random
import uuid


# =============================================================================
# Base Factories
# =============================================================================

class BaseFactory(factory.Factory):
    """Base factory with common attributes."""
    
    class Meta:
        abstract = True
    
    id = Sequence(lambda n: n + 1)
    created_at = LazyAttribute(lambda _: datetime.utcnow())
    updated_at = LazyAttribute(lambda o: o.created_at)


# =============================================================================
# User Factory
# =============================================================================

class UserFactory(BaseFactory):
    """Factory for User model."""
    
    class Meta:
        model = dict  # Using dict for simplicity
    
    id = Sequence(lambda n: f"user-{n}")
    email = Faker('email')
    username = Faker('user_name')
    full_name = Faker('name')
    is_active = True
    
    @factory.lazy_attribute
    def notification_preferences(self):
        return {
            "email_enabled": True,
            "push_enabled": random.choice([True, False]),
            "websocket_enabled": True,
        }


# =============================================================================
# Task Factory
# =============================================================================

class TaskFactory(BaseFactory):
    """Factory for Task model."""
    
    class Meta:
        model = dict
    
    id = LazyAttribute(lambda _: str(uuid.uuid4()))
    user_id = Sequence(lambda n: f"user-{n}")
    title = Faker('sentence', nb_words=4)
    description = Faker('paragraph')
    priority = factory.LazyFunction(lambda: random.choice(['low', 'medium', 'high']))
    status = 'pending'
    
    @factory.lazy_attribute
    def due_date(self):
        days_ahead = random.randint(1, 30)
        return (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
    
    @factory.lazy_attribute
    def tags(self):
        tag_options = ['work', 'personal', 'urgent', 'review', 'bug', 'feature']
        return random.sample(tag_options, k=random.randint(0, 3))


class CompletedTaskFactory(TaskFactory):
    """Factory for completed tasks."""
    
    status = 'completed'
    
    @factory.lazy_attribute
    def completed_at(self):
        return datetime.utcnow().isoformat()


class OverdueTaskFactory(TaskFactory):
    """Factory for overdue tasks."""
    
    @factory.lazy_attribute
    def due_date(self):
        days_ago = random.randint(1, 7)
        return (datetime.utcnow() - timedelta(days=days_ago)).isoformat()


# =============================================================================
# Recurring Task Factory
# =============================================================================

class RecurringTaskFactory(BaseFactory):
    """Factory for RecurringTask model."""
    
    class Meta:
        model = dict
    
    id = Sequence(lambda n: n + 1)
    user_id = Sequence(lambda n: f"user-{n}")
    title = Faker('sentence', nb_words=4)
    description = Faker('paragraph')
    is_active = True
    
    @factory.lazy_attribute
    def rrule(self):
        patterns = [
            "FREQ=DAILY;INTERVAL=1",
            "FREQ=DAILY;INTERVAL=2",
            "FREQ=WEEKLY;INTERVAL=1",
            "FREQ=WEEKLY;BYDAY=MO,WE,FR",
            "FREQ=MONTHLY;BYMONTHDAY=1",
            "FREQ=MONTHLY;BYMONTHDAY=15",
        ]
        return random.choice(patterns)
    
    @factory.lazy_attribute
    def start_date(self):
        return datetime.utcnow().isoformat()
    
    @factory.lazy_attribute
    def end_date(self):
        if random.choice([True, False]):
            days_ahead = random.randint(30, 365)
            return (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
        return None
    
    @factory.lazy_attribute
    def next_occurrence(self):
        days_ahead = random.randint(1, 7)
        return (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()


class DailyRecurringTaskFactory(RecurringTaskFactory):
    """Factory for daily recurring tasks."""
    rrule = "FREQ=DAILY;INTERVAL=1"


class WeeklyRecurringTaskFactory(RecurringTaskFactory):
    """Factory for weekly recurring tasks."""
    rrule = "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO"


class MonthlyRecurringTaskFactory(RecurringTaskFactory):
    """Factory for monthly recurring tasks."""
    rrule = "FREQ=MONTHLY;BYMONTHDAY=1"


# =============================================================================
# Task Instance Factory
# =============================================================================

class TaskInstanceFactory(BaseFactory):
    """Factory for TaskInstance model."""
    
    class Meta:
        model = dict
    
    id = Sequence(lambda n: n + 1)
    recurring_task_id = Sequence(lambda n: n + 1)
    task_id = LazyAttribute(lambda _: str(uuid.uuid4()))
    is_generated = False
    generated_at = None
    
    @factory.lazy_attribute
    def due_date(self):
        days_ahead = random.randint(1, 30)
        return (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()


# =============================================================================
# Notification Factory
# =============================================================================

class NotificationFactory(BaseFactory):
    """Factory for Notification model."""
    
    class Meta:
        model = dict
    
    id = LazyAttribute(lambda _: str(uuid.uuid4()))
    user_id = Sequence(lambda n: f"user-{n}")
    title = Faker('sentence', nb_words=5)
    body = Faker('paragraph')
    notification_type = factory.LazyFunction(
        lambda: random.choice(['reminder', 'task_update', 'system'])
    )
    channel = factory.LazyFunction(
        lambda: random.choice(['email', 'push', 'websocket'])
    )
    status = 'pending'
    
    @factory.lazy_attribute
    def scheduled_for(self):
        if random.choice([True, False]):
            minutes_ahead = random.randint(5, 60)
            return (datetime.utcnow() + timedelta(minutes=minutes_ahead)).isoformat()
        return None


class DeliveredNotificationFactory(NotificationFactory):
    """Factory for delivered notifications."""
    
    status = 'delivered'
    
    @factory.lazy_attribute
    def delivered_at(self):
        return datetime.utcnow().isoformat()


# =============================================================================
# Notification Preference Factory
# =============================================================================

class NotificationPreferenceFactory(BaseFactory):
    """Factory for NotificationPreference model."""
    
    class Meta:
        model = dict
    
    user_id = Sequence(lambda n: f"user-{n}")
    email_enabled = True
    push_enabled = factory.LazyFunction(lambda: random.choice([True, False]))
    websocket_enabled = True
    sms_enabled = False
    quiet_hours_start = "22:00"
    quiet_hours_end = "08:00"
    rate_limit_per_minute = 10
    
    @factory.lazy_attribute
    def preferred_channels(self):
        return random.sample(['email', 'push', 'websocket'], k=2)


# =============================================================================
# Audit Event Factory
# =============================================================================

class AuditEventFactory(BaseFactory):
    """Factory for AuditEvent model."""
    
    class Meta:
        model = dict
    
    id = LazyAttribute(lambda _: str(uuid.uuid4()))
    entity_type = factory.LazyFunction(
        lambda: random.choice(['task', 'user', 'recurring_task', 'notification'])
    )
    entity_id = LazyAttribute(lambda _: str(uuid.uuid4()))
    action = factory.LazyFunction(
        lambda: random.choice(['created', 'updated', 'deleted', 'completed'])
    )
    user_id = Sequence(lambda n: f"user-{n}")
    timestamp = LazyAttribute(lambda _: datetime.utcnow().isoformat())
    
    @factory.lazy_attribute
    def before_state(self):
        if self.action in ['updated', 'deleted']:
            return {"title": "Old Title", "status": "pending"}
        return None
    
    @factory.lazy_attribute
    def after_state(self):
        if self.action in ['created', 'updated']:
            return {"title": "New Title", "status": "pending"}
        return None
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "ip_address": Faker('ipv4').generate(),
            "user_agent": "TestClient/1.0",
        }


# =============================================================================
# Kafka Event Factories
# =============================================================================

class KafkaEventFactory(factory.Factory):
    """Base factory for Kafka events."""
    
    class Meta:
        model = dict
    
    event_id = LazyAttribute(lambda _: str(uuid.uuid4()))
    timestamp = LazyAttribute(lambda _: datetime.utcnow().isoformat())
    
    @classmethod
    def as_json(cls, **kwargs):
        """Generate event and return as JSON string."""
        import json
        return json.dumps(cls.create(**kwargs))


class TaskCreatedEventFactory(KafkaEventFactory):
    """Factory for task created Kafka events."""
    
    event_type = "task_created"
    
    @factory.lazy_attribute
    def payload(self):
        return TaskFactory()


class RecurringTaskCreatedEventFactory(KafkaEventFactory):
    """Factory for recurring task created events."""
    
    event_type = "recurring_task_created"
    
    @factory.lazy_attribute
    def payload(self):
        return RecurringTaskFactory()


class NotificationTriggeredEventFactory(KafkaEventFactory):
    """Factory for notification triggered events."""
    
    event_type = "notification_triggered"
    
    @factory.lazy_attribute
    def payload(self):
        return NotificationFactory()

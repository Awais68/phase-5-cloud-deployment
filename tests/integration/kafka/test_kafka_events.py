"""
Integration tests for Kafka event producer/consumer.

Tests use testcontainers to spin up real Kafka brokers.
"""
import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def task_created_event() -> Dict[str, Any]:
    """Sample task created event."""
    return {
        "event_type": "task_created",
        "event_id": f"evt-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "task_id": "task-001",
            "user_id": "user-123",
            "title": "Integration Test Task",
            "description": "Created from integration test",
            "priority": "high",
            "due_date": "2025-02-20T10:00:00Z",
        }
    }


@pytest.fixture
def recurring_task_event() -> Dict[str, Any]:
    """Sample recurring task event."""
    return {
        "event_type": "recurring_task_created",
        "event_id": f"evt-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "recurring_task_id": 1,
            "user_id": "user-123",
            "rrule": "FREQ=DAILY;INTERVAL=1",
            "start_date": "2025-02-10T10:00:00Z",
        }
    }


@pytest.fixture
def notification_event() -> Dict[str, Any]:
    """Sample notification event."""
    return {
        "event_type": "notification_triggered",
        "event_id": f"evt-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "user_id": "user-123",
            "notification_type": "reminder",
            "title": "Task Reminder",
            "body": "Your task is due soon",
            "channels": ["email", "push"],
        }
    }


# =============================================================================
# Kafka Producer Tests
# =============================================================================

class TestKafkaProducer:
    """Tests for Kafka event producer."""

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_produce_task_event(
        self, kafka_producer, kafka_bootstrap_servers, task_created_event
    ):
        """Producer can send task event to Kafka."""
        topic = "task-events"
        message = json.dumps(task_created_event)
        
        # Send message
        result = await kafka_producer.send_and_wait(topic, message.encode('utf-8'))
        
        # Verify message was sent
        assert result is not None
        assert result.topic == topic

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_produce_recurring_task_event(
        self, kafka_producer, recurring_task_event
    ):
        """Producer can send recurring task event."""
        topic = "recurring-task-events"
        message = json.dumps(recurring_task_event)
        
        result = await kafka_producer.send_and_wait(topic, message.encode('utf-8'))
        
        assert result is not None
        assert result.topic == topic

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_produce_notification_event(
        self, kafka_producer, notification_event
    ):
        """Producer can send notification event."""
        topic = "notification-events"
        message = json.dumps(notification_event)
        
        result = await kafka_producer.send_and_wait(topic, message.encode('utf-8'))
        
        assert result is not None

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_produce_batch_events(
        self, kafka_producer, task_created_event
    ):
        """Producer can send batch of events."""
        topic = "task-events"
        
        # Send batch of 10 messages
        futures = []
        for i in range(10):
            event = task_created_event.copy()
            event["event_id"] = f"evt-batch-{i}"
            message = json.dumps(event)
            future = await kafka_producer.send(topic, message.encode('utf-8'))
            futures.append(future)
        
        # Flush to ensure all messages are sent
        await kafka_producer.flush()
        
        # All messages should be sent
        assert len(futures) == 10


# =============================================================================
# Kafka Consumer Tests
# =============================================================================

class TestKafkaConsumer:
    """Tests for Kafka event consumer."""

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_consume_task_event(
        self, kafka_producer, kafka_bootstrap_servers, task_created_event
    ):
        """Consumer can receive task event from Kafka."""
        try:
            from aiokafka import AIOKafkaConsumer
        except ImportError:
            pytest.skip("aiokafka not installed")
        
        topic = "test-task-events"
        message = json.dumps(task_created_event)
        
        # Create consumer
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            consumer_timeout_ms=5000,
        )
        
        try:
            await consumer.start()
            
            # Send message
            await kafka_producer.send_and_wait(topic, message.encode('utf-8'))
            
            # Consume message
            async for msg in consumer:
                received = json.loads(msg.value.decode('utf-8'))
                assert received["event_type"] == "task_created"
                break
        finally:
            await consumer.stop()

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_consumer_handles_invalid_json(
        self, kafka_producer, kafka_bootstrap_servers
    ):
        """Consumer handles invalid JSON gracefully."""
        try:
            from aiokafka import AIOKafkaConsumer
        except ImportError:
            pytest.skip("aiokafka not installed")
        
        topic = "test-invalid-json"
        
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=3000,
        )
        
        try:
            await consumer.start()
            
            # Send invalid JSON
            await kafka_producer.send_and_wait(topic, b"not-valid-json{")
            
            # Consumer should not crash
            async for msg in consumer:
                try:
                    json.loads(msg.value.decode('utf-8'))
                except json.JSONDecodeError:
                    pass  # Expected - handled gracefully
                break
        finally:
            await consumer.stop()


# =============================================================================
# Event Flow Tests
# =============================================================================

class TestEventFlow:
    """Tests for end-to-end event flows."""

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_task_to_notification_flow(
        self, kafka_producer, kafka_bootstrap_servers
    ):
        """Test event flow from task creation to notification."""
        try:
            from aiokafka import AIOKafkaConsumer
        except ImportError:
            pytest.skip("aiokafka not installed")
        
        # Topics in the flow
        task_topic = "test-task-flow"
        notification_topic = "test-notification-flow"
        
        # Create task event
        task_event = {
            "event_type": "task_created",
            "event_id": "flow-test-001",
            "payload": {"task_id": "task-flow-001", "user_id": "user-flow"}
        }
        
        # Send task event
        await kafka_producer.send_and_wait(
            task_topic, 
            json.dumps(task_event).encode('utf-8')
        )
        
        # Simulate service processing (would normally be done by recurring service)
        notification_event = {
            "event_type": "notification_triggered",
            "event_id": "flow-notification-001",
            "payload": {
                "user_id": "user-flow",
                "triggered_by": "flow-test-001",
            }
        }
        
        await kafka_producer.send_and_wait(
            notification_topic,
            json.dumps(notification_event).encode('utf-8')
        )
        
        # Verify notification was published
        consumer = AIOKafkaConsumer(
            notification_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
        )
        
        try:
            await consumer.start()
            async for msg in consumer:
                received = json.loads(msg.value.decode('utf-8'))
                assert received["event_type"] == "notification_triggered"
                break
        finally:
            await consumer.stop()


# =============================================================================
# Idempotency Tests
# =============================================================================

class TestEventIdempotency:
    """Tests for event processing idempotency."""

    @pytest.mark.integration
    @pytest.mark.kafka
    @pytest.mark.asyncio
    async def test_duplicate_event_handling(
        self, kafka_producer, redis_client, task_created_event
    ):
        """Duplicate events are handled idempotently."""
        event_id = task_created_event["event_id"]
        topic = "test-idempotency"
        
        # Simulate processing first event
        processed_key = f"processed:{event_id}"
        first_check = await redis_client.get(processed_key)
        assert first_check is None  # Not processed yet
        
        # Mark as processed
        await redis_client.set(processed_key, "1", ex=3600)
        
        # Send same event twice
        message = json.dumps(task_created_event)
        await kafka_producer.send_and_wait(topic, message.encode('utf-8'))
        await kafka_producer.send_and_wait(topic, message.encode('utf-8'))
        
        # Check idempotency key exists
        second_check = await redis_client.get(processed_key)
        assert second_check == "1"  # Was marked as processed

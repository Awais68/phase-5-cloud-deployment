"""
Pytest fixtures and configuration for Todo App Microservices.

This module provides:
- Testcontainers setup for PostgreSQL, Kafka, Redis
- FastAPI TestClient fixtures
- Mock Dapr client
- Database session fixtures
- Kafka producer/consumer fixtures
- Factory Boy integration for test data generation
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# Testcontainers imports
try:
    from testcontainers.postgres import PostgresContainer
    from testcontainers.kafka import KafkaContainer
    from testcontainers.redis import RedisContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False

# FastAPI imports
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Kafka imports
try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False


# ============================================================
# Event Loop Configuration
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
# PostgreSQL Testcontainer Fixtures
# ============================================================

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for integration tests."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not installed")
    
    container = PostgresContainer(
        image="postgres:15-alpine",
        user="test",
        password="test",
        dbname="test_db"
    )
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Get PostgreSQL connection URL."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def async_postgres_url(postgres_container):
    """Get async PostgreSQL connection URL."""
    sync_url = postgres_container.get_connection_url()
    return sync_url.replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="function")
def db_engine(postgres_url):
    """Create sync database engine for tests."""
    engine = create_engine(postgres_url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
async def async_db_engine(async_postgres_url):
    """Create async database engine for tests."""
    engine = create_async_engine(async_postgres_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session = sessionmaker(
        async_db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================
# Kafka Testcontainer Fixtures
# ============================================================

@pytest.fixture(scope="session")
def kafka_container():
    """Start Kafka container for integration tests."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not installed")
    
    container = KafkaContainer(image="confluentinc/cp-kafka:7.5.0")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def kafka_bootstrap_servers(kafka_container) -> str:
    """Get Kafka bootstrap servers."""
    return kafka_container.get_bootstrap_server()


@pytest.fixture
async def kafka_producer(kafka_bootstrap_servers) -> AsyncGenerator[AIOKafkaProducer, None]:
    """Create Kafka producer for tests."""
    if not AIOKAFKA_AVAILABLE:
        pytest.skip("aiokafka not installed")
    
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest.fixture
async def kafka_consumer(kafka_bootstrap_servers) -> AsyncGenerator[AIOKafkaConsumer, None]:
    """Create Kafka consumer for tests."""
    if not AIOKAFKA_AVAILABLE:
        pytest.skip("aiokafka not installed")
    
    consumer = AIOKafkaConsumer(
        "test-topic",
        bootstrap_servers=kafka_bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        value_deserializer=lambda v: v.decode('utf-8')
    )
    await consumer.start()
    yield consumer
    await consumer.stop()


# ============================================================
# Redis Testcontainer Fixtures
# ============================================================

@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container for integration tests."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not installed")
    
    container = RedisContainer(image="redis:7-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def redis_url(redis_container) -> str:
    """Get Redis connection URL."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"


@pytest.fixture
async def redis_client(redis_url):
    """Create Redis client for tests."""
    try:
        import redis.asyncio as aioredis
        client = await aioredis.from_url(redis_url, decode_responses=True)
        yield client
        await client.close()
    except ImportError:
        pytest.skip("redis not installed")


# ============================================================
# FastAPI TestClient Fixtures
# ============================================================

@pytest.fixture
def mock_settings():
    """Mock settings for unit tests."""
    return MagicMock(
        database_url="postgresql://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
        kafka_bootstrap_servers="localhost:9092",
        dapr_pubsub_name="kafka-pubsub",
        jwt_secret="test-secret-key-for-testing",
        jwt_algorithm="HS256",
        debug=True
    )


@pytest.fixture
def test_client_recurring_service(mock_settings):
    """Test client for Recurring Task Service."""
    # Import here to avoid circular imports during test collection
    import sys
    sys.path.insert(0, "backend/services/recurring-task-service")
    
    try:
        from app.main import app
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("recurring-task-service not available")


@pytest.fixture
def test_client_notification_service(mock_settings):
    """Test client for Notification Service."""
    import sys
    sys.path.insert(0, "backend/services/notification-service")
    
    try:
        from app.main import app
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("notification-service not available")


@pytest.fixture
def test_client_audit_service(mock_settings):
    """Test client for Audit Log Service."""
    import sys
    sys.path.insert(0, "backend/services/audit-log-service")
    
    try:
        from app.main import app
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("audit-log-service not available")


@pytest.fixture
def test_client_main_api(mock_settings):
    """Test client for main Todo API."""
    import sys
    sys.path.insert(0, "backend/hf_deployment/todo_chatbot")
    
    try:
        from server import app
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("todo_chatbot API not available")


# ============================================================
# Async HTTP Client Fixtures
# ============================================================

@pytest.fixture
async def async_client_recurring_service():
    """Async HTTP client for Recurring Task Service."""
    import sys
    sys.path.insert(0, "backend/services/recurring-task-service")
    
    try:
        from app.main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client
    except ImportError:
        pytest.skip("recurring-task-service not available")


# ============================================================
# Mock Dapr Client Fixtures
# ============================================================

@pytest.fixture
def mock_dapr_client():
    """Mock Dapr client for unit tests."""
    mock = AsyncMock()
    mock.publish_event = AsyncMock(return_value=None)
    mock.invoke_method = AsyncMock(return_value={"status": "ok"})
    mock.get_state = AsyncMock(return_value=None)
    mock.save_state = AsyncMock(return_value=None)
    return mock


# ============================================================
# Test Data Fixtures
# ============================================================

@pytest.fixture
def sample_task():
    """Sample task data for tests."""
    return {
        "id": "task-123",
        "title": "Test Task",
        "description": "This is a test task",
        "user_id": "user-456",
        "priority": "medium",
        "status": "pending",
        "due_date": "2025-02-15T10:00:00Z"
    }


@pytest.fixture
def sample_recurring_task():
    """Sample recurring task data for tests."""
    return {
        "id": "recurring-123",
        "task_id": "task-123",
        "user_id": "user-456",
        "rrule": "FREQ=DAILY;INTERVAL=1;COUNT=10",
        "start_date": "2025-02-10",
        "end_date": "2025-02-20",
        "next_occurrence": "2025-02-11T10:00:00Z"
    }


@pytest.fixture
def sample_notification_preference():
    """Sample notification preference data for tests."""
    return {
        "user_id": "user-456",
        "email_enabled": True,
        "push_enabled": True,
        "websocket_enabled": True,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "preferred_channels": ["email", "push"]
    }


@pytest.fixture
def sample_audit_event():
    """Sample audit event data for tests."""
    return {
        "event_id": "event-789",
        "entity_type": "task",
        "entity_id": "task-123",
        "action": "created",
        "user_id": "user-456",
        "timestamp": "2025-02-10T10:00:00Z",
        "before_state": None,
        "after_state": {"title": "New Task", "status": "pending"},
        "metadata": {"ip_address": "192.168.1.1", "user_agent": "TestClient/1.0"}
    }


@pytest.fixture
def sample_kafka_task_event():
    """Sample Kafka task event message."""
    import json
    return json.dumps({
        "event_type": "task_created",
        "event_id": "evt-001",
        "timestamp": "2025-02-10T10:00:00Z",
        "payload": {
            "task_id": "task-123",
            "user_id": "user-456",
            "title": "Test Task"
        }
    })


# ============================================================
# Environment Configuration
# ============================================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    os.environ.update({
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "JWT_SECRET": "test-secret-key",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================
# Helper Functions
# ============================================================

def assert_valid_json_response(response, status_code=200):
    """Assert that a response is valid JSON with expected status code."""
    assert response.status_code == status_code
    assert response.headers.get("content-type", "").startswith("application/json")
    return response.json()


def assert_health_check_ok(response):
    """Assert that a health check response is healthy."""
    data = assert_valid_json_response(response)
    assert data.get("status") in ["healthy", "ok", "up"]
    return data

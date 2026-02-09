"""Configuration settings for Audit Log Service."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Service
    service_name: str = "audit-log-service"
    service_port: int = 8004
    log_level: str = "INFO"

    # Database (TimescaleDB)
    database_url: str = "postgresql://user:password@timescaledb:5432/todo_audit"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Dapr
    dapr_http_port: int = 3500
    dapr_grpc_port: int = 50001
    dapr_pubsub_name: str = "kafka-pubsub"

    # Kafka Topics (subscribe to all domain events)
    task_events_topic: str = "task-events"
    user_events_topic: str = "user-events"
    notification_events_topic: str = "notification-events"
    recurring_task_events_topic: str = "recurring-task-events"

    # Audit Settings
    retention_days: int = 2555  # ~7 years for compliance
    compression_days: int = 30  # Compress data older than 30 days

    # Redis (for idempotency)
    redis_url: str = "redis://redis:6379/0"
    idempotency_ttl_seconds: int = 86400  # 24 hours

    # Query Settings
    max_query_results: int = 1000
    default_query_limit: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""Configuration settings for Recurring Task Service."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Service
    service_name: str = "recurring-task-service"
    service_port: int = 8002
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://user:password@postgres:5432/todo_app"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Dapr
    dapr_http_port: int = 3500
    dapr_grpc_port: int = 50001
    dapr_pubsub_name: str = "kafka-pubsub"

    # Kafka Topics
    task_events_topic: str = "task-events"
    recurring_task_events_topic: str = "recurring-task-events"

    # Recurrence Settings
    future_instances_horizon_days: int = 90
    max_instances_per_generation: int = 12
    check_interval_seconds: int = 3600  # 1 hour

    # Redis (for idempotency)
    redis_url: str = "redis://redis:6379/0"
    idempotency_ttl_seconds: int = 86400  # 24 hours

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""Configuration settings for Notification Service."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Service
    service_name: str = "notification-service"
    service_port: int = 8003
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
    reminder_events_topic: str = "reminder-events"
    task_events_topic: str = "task-events"
    notification_events_topic: str = "notification-events"

    # Email Settings (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@todoapp.com"
    smtp_from_name: str = "Todo App"

    # Rate Limiting
    rate_limit_per_user_per_minute: int = 10
    rate_limit_per_channel_per_minute: int = 50

    # Redis (for rate limiting & WebSocket pub/sub)
    redis_url: str = "redis://redis:6379/0"
    idempotency_ttl_seconds: int = 86400  # 24 hours

    # WebSocket
    websocket_connection_timeout: int = 300  # 5 minutes

    # Templates
    email_template_dir: str = "app/templates/email"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

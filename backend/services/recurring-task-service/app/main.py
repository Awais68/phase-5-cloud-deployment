"""
Recurring Task Service - Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dapr.ext.fastapi import DaprApp
import structlog
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings
from app.api import health, recurring_events
from app.models.recurring_task import RecurringTask, TaskInstance

settings = get_settings()
logger = structlog.get_logger()

# Database engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=False,
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Redis client
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global redis_client

    # Startup
    logger.info("starting_recurring_task_service")

    # Initialize Redis
    redis_client = await aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )

    # Create tables
    async with engine.begin() as conn:
        from sqlmodel import SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)

    logger.info("recurring_task_service_started")

    yield

    # Shutdown
    logger.info("shutting_down_recurring_task_service")
    if redis_client:
        await redis_client.close()
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Recurring Task Service",
    description="Microservice for managing recurring task generation",
    version="1.0.0",
    lifespan=lifespan,
)

# Create Dapr app
dapr_app = DaprApp(app)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(recurring_events.router, tags=["Events"])


# Dependency to get DB session
async def get_db_session() -> AsyncSession:
    """Get database session."""
    async with async_session_factory() as session:
        yield session


# Dependency to get Redis client
async def get_redis() -> aioredis.Redis:
    """Get Redis client."""
    return redis_client


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "status": "running",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        log_level=settings.log_level.lower(),
    )

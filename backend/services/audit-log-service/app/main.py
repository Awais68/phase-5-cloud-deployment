"""
Audit Log Service - Main Application
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
from app.api import health, audit_events, audit_query
from app.models.audit_event import AuditEvent
from app.services.timescale_setup import setup_timescaledb

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
    logger.info("starting_audit_log_service")

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

    # Setup TimescaleDB
    await setup_timescaledb(engine)

    logger.info("audit_log_service_started")

    yield

    # Shutdown
    logger.info("shutting_down_audit_log_service")
    if redis_client:
        await redis_client.close()
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Audit Log Service",
    description="Immutable audit trail service with TimescaleDB",
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
app.include_router(audit_events.router, tags=["Events"])
app.include_router(audit_query.router, prefix="/audit", tags=["Query"])


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

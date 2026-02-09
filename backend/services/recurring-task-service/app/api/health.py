"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(lambda: None),  # Injected at runtime
    redis: aioredis.Redis = Depends(lambda: None),  # Injected at runtime
):
    """
    Readiness check with dependencies.

    Checks database and Redis connectivity.
    """
    checks = {"database": False, "redis": False}

    # Check database
    try:
        if db:
            result = await db.execute(text("SELECT 1"))
            checks["database"] = result.scalar() == 1
    except Exception:
        pass

    # Check Redis
    try:
        if redis:
            await redis.ping()
            checks["redis"] = True
    except Exception:
        pass

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

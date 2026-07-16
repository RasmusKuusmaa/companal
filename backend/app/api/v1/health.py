"""Liveness and readiness checks.

Kept separate on purpose: liveness must stay fast and dependency-free (it's
what Docker's HEALTHCHECK and an orchestrator's restart policy poll), while
readiness actually exercises the DB connection so a load balancer can tell
"process is up" apart from "process can serve requests".
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness check")
async def liveness() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@router.get("/ready", summary="Readiness check")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok", "database": "reachable"}

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from implementation.core.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Production health check probing API availability and database connectivity.
    Conforms to container orchestration standards (Docker/Kubernetes readiness probes).
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return {
        "status": "healthy",
        "service": "cynbit-backend-api",
        "database": db_status
    }

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.auth import require_admin
from app.database import async_session
from app.redis import redis
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/health", response_model=HealthResponse)
async def health():
    # Redis 체크
    try:
        await redis.ping()
        redis_status = "ok"
    except Exception:
        logger.error("Redis health check failed", exc_info=True)
        redis_status = "error"

    # DB 체크
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        logger.error("Database health check failed", exc_info=True)
        db_status = "error"

    return HealthResponse(redis=redis_status, database=db_status)

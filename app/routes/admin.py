import logging
import math

from fastapi import APIRouter, Depends, Query

from app import config
from app.auth import require_admin
from app.database import async_session
from app.redis import redis
from app.schemas import AdminHistoryResponse, HealthResponse, Pagination
from app.services.history import get_history_admin
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        await redis.ping()
        redis_status = "ok"
    except Exception:
        logger.error("Redis health check failed", exc_info=True)
        redis_status = "error"

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        logger.error("Database health check failed", exc_info=True)
        db_status = "error"

    return HealthResponse(redis=redis_status, database=db_status)


@router.get("/history", response_model=AdminHistoryResponse)
async def admin_history(
    target: str | None = Query(default=None, description="Filter by target"),
    status: str | None = Query(default=None, description="Filter by status: ok, timeout, connection_error"),
    hours: int | None = Query(default=None, ge=1, description="Filter records within last N hours"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=config.HISTORY_PAGE_SIZE, ge=1, le=100),
):
    records, total = await get_history_admin(
        target=target,
        status=status,
        hours=hours,
        page=page,
        page_size=page_size,
    )
    return AdminHistoryResponse(
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        ),
        records=records,
    )

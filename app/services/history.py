import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app import config
from app.database import async_session
from app.models import History
from app.redis import redis

logger = logging.getLogger(__name__)


def _to_dict(r: History) -> dict:
    return {
        "id": r.id,
        "target": r.target,
        "status": r.status,
        "latency_ms": r.latency_ms,
        "timestamp": r.timestamp.isoformat(),
        "data": r.data,
    }


def _cache_key(target: str, hours: int) -> str:
    return f"history:{target}:{hours}h"


async def get_history_cached(target: str, hours: int) -> list[dict]:
    """Get history for public users. Cached with Redis."""
    cache_key = _cache_key(target, hours)

    cached = await redis.get(cache_key)
    if cached:
        logger.debug("History cache hit target=%s hours=%d", target, hours)
        return json.loads(cached)

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with async_session() as session:
        stmt = (
            select(History)
            .where(History.target == target, History.timestamp >= since)
            .order_by(History.timestamp.desc())
        )
        rows = (await session.execute(stmt)).scalars().all()

    records = [_to_dict(r) for r in rows]

    await redis.set(cache_key, json.dumps(records), ex=config.CACHE_TTL)
    logger.info("History query target=%s hours=%d records=%d", target, hours, len(records))
    return records


async def get_history_admin(
    target: str | None = None,
    status: str | None = None,
    hours: int | None = None,
    page: int = 1,
    page_size: int | None = None,
) -> tuple[list[dict], int]:
    """Admin history query. Direct DB access with filters and pagination."""
    if page_size is None:
        page_size = config.HISTORY_PAGE_SIZE
    offset = (page - 1) * page_size

    filters = []
    if target:
        filters.append(History.target == target)
    if status:
        filters.append(History.status == status)
    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        filters.append(History.timestamp >= since)

    async with async_session() as session:
        count_stmt = select(func.count()).select_from(History).where(*filters)
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            select(History)
            .where(*filters)
            .order_by(History.timestamp.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await session.execute(stmt)).scalars().all()

    records = [_to_dict(r) for r in rows]
    logger.info(
        "Admin history query target=%s status=%s hours=%s page=%d total=%d",
        target, status, hours, page, total,
    )
    return records, total

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app import config
from app.database import async_session
from app.models import History
from app.redis import redis

logger = logging.getLogger(__name__)


def _cache_key(target: str, hours: int) -> str:
    return f"history:{target}:{hours}h"


async def get_history(target: str, hours: int) -> list[dict]:
    cache_key = _cache_key(target, hours)

    # 1. Redis 캐시 확인
    cached = await redis.get(cache_key)
    if cached:
        logger.debug("History cache hit target=%s hours=%d", target, hours)
        return json.loads(cached)

    # 2. RDB 조회
    logger.debug("History cache miss target=%s hours=%d", target, hours)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with async_session() as session:
        stmt = (
            select(History)
            .where(History.target == target, History.timestamp >= since)
            .order_by(History.timestamp.desc())
        )
        rows = (await session.execute(stmt)).scalars().all()

    records = [
        {
            "id": r.id,
            "target": r.target,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "timestamp": r.timestamp.isoformat(),
            "data": r.data,
        }
        for r in rows
    ]

    # 3. Redis 캐싱
    await redis.set(cache_key, json.dumps(records), ex=config.CACHE_TTL)

    logger.info("History query target=%s hours=%d records=%d", target, hours, len(records))
    return records

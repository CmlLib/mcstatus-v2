import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app import config
from app.database import async_session
from app.models import History

logger = logging.getLogger(__name__)


async def get_history(
    target: str,
    hours: int = 24,
    status: str | None = None,
    page: int = 1,
    page_size: int | None = None,
) -> tuple[list[dict], int]:
    """이력 조회. (records, total) 튜플 반환."""
    if page_size is None:
        page_size = config.HISTORY_PAGE_SIZE

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    offset = (page - 1) * page_size

    # 공통 필터
    filters = [History.target == target, History.timestamp >= since]
    if status:
        filters.append(History.status == status)

    async with async_session() as session:
        # total count
        count_stmt = select(func.count()).select_from(History).where(*filters)
        total = (await session.execute(count_stmt)).scalar_one()

        # paginated rows
        stmt = (
            select(History)
            .where(*filters)
            .order_by(History.timestamp.desc())
            .offset(offset)
            .limit(page_size)
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

    logger.info(
        "History query target=%s hours=%d status=%s page=%d total=%d",
        target, hours, status, page, total,
    )
    return records, total

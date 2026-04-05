import math

from fastapi import APIRouter, Query

from app import config
from app.errors import InvalidParameter
from app.schemas import HistoryResponse, Pagination, ServerStatus
from app.services.history import get_history
from app.services.status import get_status, get_status_batch

router = APIRouter(prefix="/api/v1/servers", tags=["servers"])


@router.get("/batch", response_model=list[ServerStatus])
async def server_status_batch(
    targets: str = Query(..., description="쉼표로 구분된 target 목록 (예: ip1:port1,ip2:port2)"),
):
    target_list = [t.strip() for t in targets.split(",") if t.strip()]

    if len(target_list) == 0:
        raise InvalidParameter("targets must not be empty")
    if len(target_list) > config.BATCH_MAX:
        raise InvalidParameter(f"Maximum {config.BATCH_MAX} targets allowed")

    return await get_status_batch(target_list)


@router.get("/{target}", response_model=ServerStatus)
async def server_status(target: str):
    return await get_status(target)


@router.get("/{target}/history", response_model=HistoryResponse)
async def server_history(
    target: str,
    hours: int = Query(default=24, ge=1, le=config.HISTORY_MAX_HOURS),
    status: str | None = Query(default=None, description="필터: ok, timeout, connection_error"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=config.HISTORY_PAGE_SIZE, ge=1, le=100),
):
    records, total = await get_history(
        target=target,
        hours=hours,
        status=status,
        page=page,
        page_size=page_size,
    )
    return HistoryResponse(
        target=target,
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        ),
        records=records,
    )

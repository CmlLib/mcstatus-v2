from fastapi import APIRouter, Query

from app import config
from app.errors import InvalidParameter
from app.schemas import HistoryRecord, ServerStatus
from app.services.history import get_history_cached
from app.services.status import get_status, get_status_batch

router = APIRouter(prefix="/api/v1/servers", tags=["servers"])


@router.get("/batch", response_model=list[ServerStatus])
async def server_status_batch(
    targets: str = Query(..., description="Comma-separated target list (e.g. ip1:port1,ip2:port2)"),
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


@router.get("/{target}/history", response_model=list[HistoryRecord])
async def server_history(
    target: str,
    hours: int = Query(default=24, ge=1, le=config.HISTORY_MAX_HOURS),
):
    return await get_history_cached(target, hours)

from fastapi import APIRouter, HTTPException, Query

from app import config
from app.schemas import ErrorResponse, HistoryResponse, ServerStatus
from app.services.history import get_history
from app.services.status import get_status, get_status_batch

router = APIRouter(prefix="/api/v1/servers", tags=["servers"])


@router.get("/batch", response_model=list[ServerStatus])
async def server_status_batch(
    targets: str = Query(..., description="쉼표로 구분된 target 목록 (예: ip1:port1,ip2:port2)"),
):
    target_list = [t.strip() for t in targets.split(",") if t.strip()]

    if len(target_list) == 0:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_PARAMETER", "message": "targets must not be empty"}},
        )
    if len(target_list) > config.BATCH_MAX:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_PARAMETER", "message": f"Maximum {config.BATCH_MAX} targets allowed"}},
        )

    return await get_status_batch(target_list)


@router.get("/{target}", response_model=ServerStatus)
async def server_status(target: str):
    return await get_status(target)


@router.get("/{target}/history", response_model=HistoryResponse)
async def server_history(
    target: str,
    hours: int = Query(default=24, ge=1, le=config.HISTORY_MAX_HOURS),
):
    records = await get_history(target, hours)
    return HistoryResponse(target=target, hours=hours, records=records)

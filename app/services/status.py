import asyncio
import json
import logging
from datetime import datetime, timezone

from mcstatus import JavaServer

from app import config
from app.database import async_session
from app.models import History
from app.redis import redis
from app.services.single_flight import SingleFlight

logger = logging.getLogger(__name__)
flight = SingleFlight()


def _parse_target(target: str) -> tuple[str, int]:
    if ":" in target:
        host, port_str = target.rsplit(":", 1)
        return host, int(port_str)
    return target, config.DEFAULT_MC_PORT


def _normalize_target(target: str) -> str:
    host, port = _parse_target(target)
    return f"{host}:{port}"


def _cache_key(target: str) -> str:
    return f"status:{target}"


async def _probe(target: str) -> dict:
    """Probe target server via TCP and return result dict."""
    host, port = _parse_target(target)
    now = datetime.now(timezone.utc)

    try:
        server = await JavaServer.async_lookup(f"{host}:{port}")
        status = await asyncio.wait_for(
            server.async_status(),
            timeout=config.TCP_TIMEOUT,
        )
        result = {
            "target": target,
            "status": "ok",
            "latency_ms": round(status.latency),
            "timestamp": now.isoformat(),
            "data": status.raw,
        }
        logger.info("Probe OK target=%s latency=%dms", target, result["latency_ms"])
    except (asyncio.TimeoutError, OSError, Exception) as exc:
        status_str = "timeout" if isinstance(exc, asyncio.TimeoutError) else "connection_error"
        logger.warning("Probe failed target=%s status=%s error=%s", target, status_str, exc)
        result = {
            "target": target,
            "status": status_str,
            "latency_ms": None,
            "timestamp": now.isoformat(),
            "data": None,
        }

    # Save to DB
    async with async_session() as session:
        session.add(History(
            target=target,
            timestamp=now,
            status=result["status"],
            latency_ms=result["latency_ms"],
            data=result["data"],
        ))
        await session.commit()

    # Cache in Redis
    await redis.set(
        _cache_key(target),
        json.dumps(result),
        ex=config.CACHE_TTL,
    )

    return result


async def get_status(target: str) -> dict:
    target = _normalize_target(target)

    # 1. Check Redis cache
    cached = await redis.get(_cache_key(target))
    if cached:
        logger.debug("Cache hit target=%s", target)
        return json.loads(cached)

    # 2. Probe with Single Flight
    logger.debug("Cache miss target=%s", target)
    return await flight.do(target, lambda: _probe(target))


async def get_status_batch(targets: list[str]) -> list[dict]:
    targets = [_normalize_target(t) for t in targets]
    keys = [_cache_key(t) for t in targets]

    # 1. Redis MGET
    cached_values = await redis.mget(keys)

    results: dict[str, dict] = {}
    missing: list[str] = []

    for target, cached in zip(targets, cached_values):
        if cached:
            results[target] = json.loads(cached)
        else:
            missing.append(target)

    logger.info("Batch request total=%d cached=%d miss=%d", len(targets), len(targets) - len(missing), len(missing))

    # 2. Probe cache-missed targets concurrently
    if missing:
        probed = await asyncio.gather(
            *(flight.do(t, lambda t=t: _probe(t)) for t in missing)
        )
        for target, result in zip(missing, probed):
            results[target] = result

    return [results[t] for t in targets]

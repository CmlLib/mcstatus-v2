import asyncio
from typing import Any, Callable, Coroutine


class SingleFlight:
    """Deduplicates concurrent calls for the same key. Only one coroutine runs; others share the result."""

    def __init__(self) -> None:
        self._futures: dict[str, asyncio.Future[Any]] = {}

    async def do(self, key: str, fn: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
        if key in self._futures:
            return await self._futures[key]

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self._futures[key] = fut

        try:
            result = await fn()
            fut.set_result(result)
            return result
        except Exception as exc:
            fut.set_exception(exc)
            raise
        finally:
            self._futures.pop(key, None)

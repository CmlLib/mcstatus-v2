import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.errors import register_error_handlers
from app.logging import setup_logging
from app.models import Base
from app.redis import redis
from app.routes.admin import router as admin_router
from app.routes.servers import router as servers_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MCStatus API")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")
    yield
    logger.info("Shutting down")
    await redis.aclose()
    await engine.dispose()


app = FastAPI(title="MCStatus API", version="0.1.0", lifespan=lifespan)
register_error_handlers(app)
app.include_router(servers_router)
app.include_router(admin_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

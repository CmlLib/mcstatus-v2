import os


ENV = os.getenv("ENV", "development")  # "development" | "production"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/mcstatus")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CACHE_TTL = 300  # 5분
TCP_TIMEOUT = 3  # 3초
DEFAULT_MC_PORT = 25565
BATCH_MAX = 20
HISTORY_MAX_HOURS = 24

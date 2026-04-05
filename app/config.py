import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/mcstatus")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
TCP_TIMEOUT = int(os.getenv("TCP_TIMEOUT", "3"))
DEFAULT_MC_PORT = int(os.getenv("DEFAULT_MC_PORT", "25565"))
BATCH_MAX = int(os.getenv("BATCH_MAX", "20"))
HISTORY_MAX_HOURS = int(os.getenv("HISTORY_MAX_HOURS", "24"))
HISTORY_PAGE_SIZE = int(os.getenv("HISTORY_PAGE_SIZE", "50"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

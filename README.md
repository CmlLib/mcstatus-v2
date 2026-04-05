# MCStatus API v2

Minecraft Java Edition 서버 상태 조회 API

## Docker로 실행

```bash
docker compose up --build
```

PostgreSQL, Redis, API 서버가 모두 함께 실행됩니다. DB와 테이블은 자동 생성됩니다.

`http://localhost:8000`에서 접속할 수 있습니다.

## Docker Hub에 배포

```bash
# 빌드
docker build -t <dockerhub-username>/mcstatus-v2:<tag> .

# 로그인 (최초 1회)
docker login

# 푸시
docker push <dockerhub-username>/mcstatus-v2:<tag>
```

## 로컬 실행

### 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis

### 설치 및 실행

```bash
uv sync
cp .env.example .env  # 필요시 수정
createdb mcstatus      # DB 생성 (테이블은 서버 시작 시 자동 생성)
uv run python main.py
```

`http://localhost:8000`에서 시작됩니다. API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 환경변수

`.env` 파일 또는 시스템 환경변수로 설정합니다. Docker 사용 시 `compose.yml`에서 설정합니다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/mcstatus` | PostgreSQL 연결 문자열 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 연결 문자열 |
| `ENV` | `development` | `development`: 읽기 쉬운 로그, `production`: JSON 로그 |
| `CACHE_TTL` | `300` | Redis 캐시 TTL (초) |
| `TCP_TIMEOUT` | `3` | MC 서버 연결 타임아웃 (초) |
| `BATCH_MAX` | `20` | 일괄 조회 최대 서버 수 |
| `HISTORY_MAX_HOURS` | `24` | 일반 사용자 이력 조회 최대 시간 |
| `HISTORY_PAGE_SIZE` | `50` | 관리자 이력 조회 기본 페이지 크기 |
| `ADMIN_USERNAME` | `admin` | 관리자 API Basic Auth 사용자명 |
| `ADMIN_PASSWORD` | `admin` | 관리자 API Basic Auth 비밀번호 |
| `CORS_ORIGINS` | `*` | 허용할 CORS origin (쉼표 구분) |

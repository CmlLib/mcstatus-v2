# MCStatus API v2

Minecraft Java Edition 서버 상태 조회 API

## 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis

## 설치

```bash
uv sync
```

## 실행

```bash
uv run python main.py
```

`http://localhost:8000`에서 시작됩니다. API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/mcstatus` | PostgreSQL 연결 문자열 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 연결 문자열 |
| `ENV` | `development` | `development`: 사람이 읽기 쉬운 로그, `production`: JSON 로그 |

## 데이터베이스 준비

테이블은 서버 시작 시 자동 생성됩니다. DB만 미리 만들어두면 됩니다.

```bash
createdb mcstatus
```

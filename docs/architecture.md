## 기술 스택 (Tech Stack)

| 영역 | 기술 |
|------|------|
| 패키지 매니저 | uv |
| 웹 프레임워크 | FastAPI (asyncio) |
| ORM | SQLAlchemy |
| RDB | PostgreSQL |
| 캐시 | Redis |

> 서버 상태를 가져오는 예제는 `docs/example.py` 참고

---

## 🏗️ 1. 시스템 아키텍처 (System Architecture)

워커(Worker) 프로세스와 상태 관리용 마스터 테이블을 모두 제거하고, API 서버 1개가 모든 로직을 처리하는 단일 프로세스 구조입니다.

 * API Server (FastAPI):

   * 모든 비즈니스 로직, 캐싱, 외부 TCP 통신을 전담합니다.

   * 비동기(asyncio) 기반으로 동작하여 수많은 동시 접속에도 스레드 고갈 없이 가볍게 동작합니다.

 * Data Flow (Cache-Aside & Lazy Loading):

   * 사용자가 특정 IP:Port의 상태를 API로 요청합니다.

   * API 서버가 Redis 캐시(TTL 5분)를 확인합니다.

   * Cache Hit: Redis에서 즉시 꺼내서 반환합니다 (DB 부하 0, 외부 통신 0).

   * Cache Miss: API 서버가 Single Flight 패턴을 통해 방어막을 친 뒤, 직접 외부 서버와 TCP 통신을 시도합니다. 성공/실패 여부를 RDB에 Insert하고, 결과를 Redis에 5분 TTL로 저장한 후 반환합니다.

---

## 🗄️ 2. 데이터베이스 스키마 (DB Schema)

마스터 테이블(managed_servers)과 로그 테이블(jobs)이 사라지고, 오직 과거 기록을 남기는 단 1개의 RDB 테이블만 존재합니다.

### RDB (PostgreSQL)

 * Table: history (수집 결과 누적 기록용)

   * id (BIGINT, Primary Key, Auto Increment)

   * target (VARCHAR(100), Index) - 예: '192.168.0.10:8080' (ID 자체가 곧 타겟 정보)

   * timestamp (DATETIME, Index) - 시간 기반 조회를 위한 필수 인덱스

   * status (VARCHAR(20)) - 예: 'ok', 'timeout', 'connection_error'

   * latency_ms (INT, Nullable) - 실패 시 NULL 기록

   * data (JSONB, Nullable) - `JavaStatusResponse.raw` (서버 원본 응답 dict)를 그대로 저장. 실패 시 NULL

### Redis (고속 서빙 및 RDB 방패용)

 * 최신 상태 캐시 (String 구조)

   * Key: status:{target} (예: status:192.168.0.10:8080)

   * Value: {"status": "ok", "latency_ms": 15, "timestamp": "...", "data": { ... }}

   * TTL: 300초 (5분). 만료되면 다음 요청 시 API 서버가 새로 통신합니다.

 * 히스토리 쿼리 캐시 (String 구조)

   * Key: history:{target}:{hours}h (예: history:192.168.0.10:8080:24h)

   * Value: 지난 24시간의 이력 데이터 배열 (JSON)

   * TTL: 300초 (5분). 동일한 히스토리 반복 조회 시 RDB를 보호합니다.

---

## 🌐 3. API 엔드포인트 설계 (API Endpoints)

관리해야 할 대상 목록이 없으므로, ID 파라미터 위치에 외부 서버의 IP:Port 정보를 직접 넘깁니다. 포트 생략 시 Minecraft Java 기본 포트(25565)를 사용합니다. (단, URL에 : 기호가 들어가므로 클라이언트에서 파라미터를 보낼 때 URL 인코딩(%3A)을 하거나, Base64로 감싸서 보내는 것을 권장합니다.)

### 👤 데이터 조회 API

**GET /api/v1/servers/{target}**

 * 역할: 특정 서버(IP:Port)의 현재 상태 조회.

 * 동작: Redis 캐시 확인 → 없으면 Single Flight 적용하여 TCP 직접 통신 → 결과 RDB 저장 & Redis 5분 캐싱 → 응답.

**GET /api/v1/servers/batch?targets=ip1:port1,ip2:port2**

 * 역할: 여러 서버의 상태를 한 번에 조회. **최대 20개**까지 허용.

 * 동작: Redis에서 MGET으로 한 번에 조회. 만약 이 중 캐시가 없는 타겟이 섞여 있다면, 그 타겟들만 묶어서 비동기(asyncio.gather)로 동시에 TCP 통신을 시도한 뒤 결과를 합쳐서 응답.

**GET /api/v1/servers/{target}/history?hours=24**

 * 역할: 특정 서버의 통신 이력 조회. **hours는 최대 24**까지 허용.

 * 동작: Redis 캐시(history:...) 확인 → 없으면 RDB history 테이블 조회 → Redis에 5분 TTL로 캐싱 → 응답.

### 🛡️ 관리자 API (Basic Auth)

백그라운드 워커가 사라졌기 때문에 관리자 API도 모니터링 목적의 최소한만 남습니다.

**GET /api/v1/admin/health**

 * 역할: API 서버, Redis, RDB 연결 상태 점검.

### 📋 에러 응답 스펙 (Error Response)

모든 에러 응답은 아래의 통일된 JSON 포맷을 따릅니다.

```json
{
  "error": {
    "code": "INVALID_TARGET",
    "message": "Target must be in host:port format"
  }
}
```

| HTTP Status | code | 상황 |
|-------------|------|------|
| 400 | `INVALID_TARGET` | target 파라미터 형식이 올바르지 않음 (host:port 아닌 경우) |
| 400 | `INVALID_PARAMETER` | hours 등 쿼리 파라미터 값이 유효하지 않음 (hours > 24, batch > 20 등) |
| 404 | `NO_HISTORY` | 해당 target의 히스토리 데이터가 없음 |
| 500 | `INTERNAL_ERROR` | 서버 내부 에러 (Redis/RDB 장애 등) |
| 503 | `UPSTREAM_TIMEOUT` | 대상 서버에 TCP 연결 시도했으나 타임아웃 (결과는 캐싱됨) |

> 정상 응답은 HTTP 200으로 반환하되, 대상 서버가 응답하지 않는 경우 `status: "timeout"` 데이터를 정상 응답(200)으로 돌려줍니다. 503은 우리 서버 자체가 외부 통신을 수행할 수 없는 극단적 상황에서만 사용합니다.

---

## ⚠️ 4. 구현 시 절대 타협 불가능한 2가지 규칙 (Strict Guardrails)

이 심플한 아키텍처가 실전 트래픽에서 무너지지 않으려면 다음 두 가지를 코드 레벨에서 반드시 강제해야 합니다.

 * Single Flight 도입 의무화:

   * 5분 TTL이 끝난 직후 1,000명의 유저가 A서버를 동시에 조회할 때, API 서버가 A서버로 1,000개의 TCP 커넥션을 날리지 않도록 합니다. 1개의 스레드만 통신 및 RDB 저장을 수행하고 999개는 대기 후 결과를 공유받는 코드를 반드시 작성해야 합니다.

 * 짧은 비동기 TCP 타임아웃 (asyncio + 3초 이내 제한):

   * 요청받은 타겟 서버가 죽어 응답이 없을 때, API 서버가 하염없이 기다리면 전체 API 서비스가 멈춥니다(Thread/Connection Pool 고갈). asyncio.wait_for 등을 사용해 최대 2~3초 안에 응답이 오지 않으면 즉시 예외 처리하고 status='timeout'으로 캐싱해버려야 우리 서버가 안전합니다.

---

## 📌 5. 추후 고려 사항 (Future Considerations)

현재는 단일 인스턴스를 가정한 최소 구조이며, 아래 항목은 필요 시 단계적으로 도입합니다.

 * **SSRF 방어**: 임의 IP:Port를 타겟으로 받으므로, 내부망 대역(10.x, 172.16.x, 192.168.x, 127.0.0.1 등) 차단 및 허용 목록(allowlist) 도입
 * **Rate Limiting**: 일반 API에 대한 요청 속도 제한 (IP별 또는 API 키 기반)
 * **수평 확장**: 다중 인스턴스 배포 시 Single Flight 범위를 Redis 분산 락으로 확장
 * **데이터 보관 정책**: history 테이블의 파티셔닝 또는 일정 기간 이후 데이터 아카이빙/삭제
 * **인증/인가**: 일반 API에 대한 API 키 또는 토큰 기반 인증 도입

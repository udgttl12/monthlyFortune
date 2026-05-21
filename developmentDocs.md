# 개발 문서

## 0. 목표 확정 (30분)

**산출물**: 년/월/일/시주 한자(간지)만 JSON/간단 웹페이지로 출력

**입력**: 생년-월-일 [시:분], 성별(옵션), 출생지(옵션)

**기준**: Asia/Seoul, 입춘 기준 연주 전환(옵션화 가능)

**범위**: 1900–2100년

## 1. 리포지토리/러닝 환경 (0.5일)

- **툴체인**: Python 3.11+, poetry 또는 uv, ruff(lint), pytest, pre-commit
- **프레임워크**: FastAPI(+ Uvicorn) — 모놀리스로 API+간단 HTML 둘 다
- **구조**
  ```
  codex-fortune/
    app/
      main.py               # FastAPI 엔트리포인트
      api/                  # 라우트 (REST)
      views/                # Jinja2 템플릿(선택)
      services/             # 계산 서비스
      core/                 # 순수 계산 로직(테스트 핵심)
      data/                 # 절기/음력 시드, 로더
      models/               # pydantic 스키마
      infra/                # Mongo/Redis/설정/로그
    tests/
    pyproject.toml
    README.md
  ```

## 2. 캘린더/데이터 계층 준비 (1–2일)

풀이 불필요하므로 여기만 정확하면 끝난다.

- **옵션 A (가장 간단)**: 오픈소스 라이브러리 사용
  - sxtwl(중국력 기반) 또는 solarlunar(Node) 참고 → 파이썬은 sxtwl 추천
- **옵션 B (자체 시드)**: 1900–2100년 24절기 테이블 + 양↔음력 맵 CSV 생성 후 로드
  - `app/data/`에 `jieqi.csv`, `lunar_map.csv` 두고 로더 작성

검증 케이스: 입춘/경계일 30~50개 수집 (연도별 다른 시각 확인)

## 3. 사주 계산 코어 (2–3일)

- **모듈**: `app/core/pillars.py`
- **기능**:
  - 기준일(예: 1984-02-02 甲子)로부터 일주 인덱스 계산
  - 연주: 입춘 기준(기본) / 음력설 기준(옵션) 전환
  - 월주: 절기 기반(중기 기준) 산출
  - 시주: 일간 + 시간표 매핑(지지 12시×2시간 블록)

**출력 예**:
```json
{ "year": "甲子", "month": "乙丑", "day": "丙寅", "time": "丁卯" }
```

전부 순수 함수로 작성 + pytest 단위테스트(경계일 중점)

## 4. API & 간단 웹 (0.5–1일)

- **REST**:
  - `GET /api/health`
  - `GET /api/calc?date=YYYY-MM-DD&time=HH:mm&tz=Asia/Seoul` → 간지 JSON
- **웹뷰(선택)**: Jinja2로 한 페이지 폼 + 결과 렌더링
- **스키마**: pydantic v2 (`models/request.py`, `models/response.py`)
- **에러 처리**: 잘못된 날짜/시간, 범위 밖 요청, 타임존 미지정 대비

## 5. 저장/캐시 (선택, 0.5–1일)

프로토타입은 무저장으로 시작 가능. 반복 요청이 많다면 추가.

- **MongoDB (선호)**
  - `calc_snapshot` 컬렉션: `hash(date,time,place)` 유니크 + TTL(예: 30일)
- **Redis 캐시**
  - 키: `fortune:v1:{hash}` → JSON 24시간
- 둘 다 옵셔널; 성능 필요 시 붙이기

## 6. 설정/로깅/테스트 자동화 (0.5일)

- **설정**: pydantic-settings로 `.env` 관리 (`TZ`, `MONGO_URL`, `REDIS_URL` 등)
- **로깅**: structlog 또는 기본 logging(JSON 포맷)
- **테스트**: `pytest -q`; 경계일 스위트는 `tests/edge_cases/`
- **CI**: GitHub Actions (lint+test)

## 7. 패키징 & 실행 (0.5일)

- **Dockerfile** (slim 이미지를 기반)
- `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- 단일 인스턴스로 시작, 필요 시 `gunicorn -k uvicorn.workers.UvicornWorker -w 2`

## 8. 배포 (개발/스테이징) (0.5–1일)

- 한 대 서버: Nginx(리버스 프록시) + Uvicorn
- 또는 Cloud Run / Fly.io 같은 간편 PaaS
- **HTTPS**: certbot 또는 PaaS 기본 인증서

## 9. 품질 체크리스트 (DoD)

- 1900–2100년 입력 시 네 축(년·월·일·시) 간지 정확
- 입춘 경계일 테스트 통과 (±1일, 시간 경계)
- `GET /api/calc` 200ms 이내(캐시 없이)
- 에러 응답 스키마 일관성
- 단일 바이너리(도커)로 기동 가능

## 10. 백로그 (다음 단계)

- (옵션) 연/월/일/시주 표기 로마자/한글 동시 제공
- (옵션) 다국어(i18n) 준비
- (옵션) 절기/윤달 옵션 토글(입춘 vs 설 기준)
- (옵션) 간단 OG 이미지 생성(공유 카드)

## 간단 설치 명령(메모)

```bash
# 새 프로젝트
uv venv && uv pip install fastapi "uvicorn[standard]" pydantic pydantic-settings jinja2
uv pip install pytest ruff
# (옵션) sxtwl / pymongo / redis, structlog 등 필요 시 추가
```


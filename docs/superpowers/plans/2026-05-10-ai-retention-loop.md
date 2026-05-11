# AI 재방문 루프 구현 계획

> **작업자 안내:** 이 문서는 사용자가 직접 읽고 수정할 수 있는 한국어 구현 계획서입니다. 실제 구현을 시작할 때는 `superpowers:subagent-driven-development` 또는 `superpowers:executing-plans`로 Task 순서대로 진행합니다.

**목표:** `monthlyFortune`을 단순 월운 조회 사이트에서 매일 다시 방문할 이유가 있는 AI 타이밍 도구로 확장합니다.

**핵심 기능:** 30일 액션 캘린더, AI 오늘 브리핑, AI 결정 타이밍 코치.

**아키텍처:** 기존 출생 차트와 월간 트랜짓 계산을 사실의 기준으로 둡니다. LLM은 점성술 계산을 새로 만들지 않고, 이미 계산된 일별 점수와 근거를 사용자가 이해하기 쉬운 한국어 행동 조언으로 바꾸는 역할만 합니다.

**기술 스택:** Next.js 14, React 18, TypeScript, FastAPI, Pydantic, Python `unittest`, 기존 `TTLCache`, provider 교체 가능한 LLM 클라이언트, 선택적 MariaDB.

---

## 1. 제품 방향

이번 기능의 목적은 콘텐츠를 더 길게 쓰는 것이 아니라, 사용자가 다시 들어올 이유를 만드는 것입니다.

사용자 루프:

1. 월초 또는 중요한 일이 생겼을 때 `30일 액션 캘린더`를 봅니다.
2. 매일 아침 `AI 오늘 브리핑`으로 오늘 할 일과 피할 일을 확인합니다.
3. 면접, 고백, 계약, 이직, 지출, 연락 같은 고민이 생기면 `AI 결정 타이밍 코치`에게 질문합니다.
4. 좋은 답변과 회고는 브라우저에 저장해 다시 확인합니다.

제품 포지션:

- "운세를 읽는 사이트"가 아니라 "개인 타이밍 의사결정 도구"입니다.
- 재미 요소는 유지하되, 결과는 현실적인 행동 조언으로 보여줍니다.
- 중요한 결정에 대해서는 운세가 확정 답변이 아니라 참고 자료라는 안내를 항상 포함합니다.

---

## 2. 구현 범위

### 이번 1차 구현에 포함

- `/calendar` 월간 액션 캘린더 페이지
- `/today` 오늘 브리핑 페이지
- `/coach` AI 결정 타이밍 코치 페이지
- `/api/ai-retention/action-calendar`
- `/api/ai-retention/daily-brief`
- `/api/ai-retention/coach`
- LLM provider 추상화
- xAI provider 지원
- DeepSeek provider 지원 가능 구조
- LLM 실패 시 deterministic fallback
- 브라우저 `localStorage` 기반 간단 저장

### 이번 1차 구현에서 제외

- 로그인
- 결제
- 푸시 알림
- 관리자 페이지
- 서버 DB 저장
- MariaDB 실제 연결
- 사용자별 장기 히스토리

### 나중에 필요하면 추가

- MariaDB 저장
- 계정 기반 프로필 관리
- 여러 사람 프로필 전환
- 캘린더 내보내기
- 주간 리마인드
- 유료 질문 제한

---

## 3. 중요한 결정

### 3.1 DB 결정

1차 구현은 DB 없이 갑니다.

- 서버 쪽은 기존 `TTLCache` 사용
- 브라우저 쪽은 `localStorage` 사용
- 서버 재시작 시 캐시는 사라져도 괜찮은 구조

DB가 필요해지면 MariaDB만 사용합니다.

- SQLite 사용하지 않음
- Postgres 사용하지 않음
- Supabase 사용하지 않음
- MongoDB 같은 문서형 DB 사용하지 않음

MariaDB를 쓰는 경우의 저장 대상:

- 저장한 코치 질문과 답변
- 오늘 브리핑 회고
- 서버 측 LLM 생성 결과 캐시
- 사용자 프로필이 생길 경우 프로필별 저장 데이터

출생 정보는 민감 정보입니다. DB에 저장할 경우 원문 birth detail을 그대로 많이 쌓지 말고, 캐시 조회용으로 `birth_signature_hash`를 사용합니다.

### 3.2 LLM provider 결정

제품 코드는 xAI나 DeepSeek를 직접 호출하지 않습니다.

제품 코드는 `LLMRetentionClient`만 호출합니다.

환경 변수:

```env
LLM_RETENTION_PROVIDER=xai
LLM_RETENTION_API_KEY=
LLM_RETENTION_MODEL=grok-4.20-reasoning
LLM_RETENTION_TIMEOUT_SECONDS=45
```

DeepSeek로 바꿀 경우:

```env
LLM_RETENTION_PROVIDER=deepseek
LLM_RETENTION_API_KEY=
LLM_RETENTION_MODEL=deepseek-v4-pro
LLM_RETENTION_TIMEOUT_SECONDS=45
```

provider별 방식:

- xAI: `https://api.x.ai/v1/responses`
- DeepSeek: `https://api.deepseek.com/chat/completions`
- xAI는 JSON Schema structured output 사용
- DeepSeek는 OpenAI 호환 Chat Completions와 JSON Output 사용
- 모든 LLM 결과는 Pydantic으로 다시 검증
- 실패, timeout, 빈 응답, schema 오류는 fallback으로 처리

기존 `XAI_API_KEY`는 월간 운세 확장용으로 남겨둘 수 있습니다. 새 AI 재방문 기능은 `LLM_RETENTION_*` 설정을 우선 사용합니다.

---

## 4. 사용자 화면 설계

### 4.1 `/calendar` 30일 액션 캘린더

목적:

- 사용자가 한 달 흐름을 빠르게 보고 중요한 날짜를 고르게 합니다.

화면 구성:

- 월 제목
- 프로필 요약
- 1일 단위 카드 그리드
- 각 날짜 카드에는 점수, 분위기, 추천 행동, 피할 행동, 근거 표시
- 각 날짜에서 오늘 브리핑으로 이동
- AI 코치 질문 버튼

예시 카드:

```text
5/10
점수 8/10
연락이 풀리는 날
추천: 오전에 중요한 연락을 보낸다.
주의: 일정을 과하게 늘리지 않는다.
근거: 관계와 커리어 신호가 함께 좋다.
```

### 4.2 `/today` AI 오늘 브리핑

목적:

- 매일 아침 다시 열 이유를 만듭니다.

화면 구성:

- 오늘 날짜
- 오늘 점수
- 오늘의 핵심 문장
- 오늘 할 일
- 오늘 피할 일
- 좋은 시간대 힌트
- 주의 시간대 힌트
- 저녁 회고 질문
- 월간 캘린더와 AI 코치 이동 버튼

예시:

```text
오늘은 차분히 시작하면 좋은 날입니다.
할 일: 가장 중요한 연락을 오전에 먼저 보냅니다.
피할 일: 감정이 올라온 상태에서 긴 답장을 보내지 않습니다.
회고: 오늘 가장 잘 조절한 선택은 무엇이었나요?
```

### 4.3 `/coach` AI 결정 타이밍 코치

목적:

- 사용자가 실제 고민을 입력하게 만들어 고관여 방문을 만듭니다.

사용 예시:

```text
다음 주 면접 준비는 언제 집중하는 게 좋을까?
고백은 이번 달 언제 하는 게 좋을까?
계약 답장을 오늘 보내도 될까?
이직 제안을 받아도 될지 고민이야.
이번 주 큰 지출을 해도 될까?
```

결과 구성:

- 질문 요약
- 답변
- 추천 날짜
- 주의 날짜
- 지금 할 첫 행동
- 보낼 메시지 초안
- 판단 근거 요약
- 면책 문구

---

## 5. 백엔드 API 설계

### 5.1 월간 액션 캘린더

Endpoint:

```text
GET /api/ai-retention/action-calendar
```

Query:

```text
birthDate=1990-01-01
birthTime=0900
city=Seoul
countryCode=KR
year=2026
month=5
timezone=Asia/Seoul
```

Response:

```json
{
  "year": 2026,
  "month": 5,
  "profileSummary": "개인 차트 요약",
  "llmEnhanced": true,
  "days": [
    {
      "date": "2026-05-10",
      "score": 8,
      "tone": "supportive",
      "title": "연락이 풀리는 날",
      "action": "오전에 중요한 연락을 보낸다.",
      "avoid": "일정을 과하게 늘리지 않는다.",
      "reason": "관계와 커리어 신호가 함께 좋다.",
      "categories": ["career", "love"]
    }
  ]
}
```

### 5.2 오늘 브리핑

Endpoint:

```text
GET /api/ai-retention/daily-brief
```

Query:

```text
birthDate=1990-01-01
birthTime=0900
city=Seoul
countryCode=KR
year=2026
month=5
targetDate=2026-05-10
timezone=Asia/Seoul
```

Response:

```json
{
  "date": "2026-05-10",
  "score": 8,
  "tone": "supportive",
  "headline": "차분히 시작하면 좋은 날",
  "summary": "오전에는 정리, 오후에는 연락이 좋습니다.",
  "bestTimeHint": "오전 9시-11시",
  "avoidTimeHint": "늦은 밤 즉흥 답장",
  "action": "가장 중요한 연락을 먼저 보냅니다.",
  "avoid": "감정적인 결정을 미룹니다.",
  "reflectionPrompt": "오늘 가장 잘 조절한 선택은 무엇인가요?",
  "llmEnhanced": true
}
```

### 5.3 AI 코치

Endpoint:

```text
POST /api/ai-retention/coach
```

Body:

```json
{
  "birthDate": "1990-01-01",
  "birthTime": "0900",
  "city": "Seoul",
  "countryCode": "KR",
  "year": 2026,
  "month": 5,
  "question": "다음 주 면접 준비는 언제 하는 게 좋을까?"
}
```

Response:

```json
{
  "question": "다음 주 면접 준비는 언제 하는 게 좋을까?",
  "answer": "준비는 초반에 몰아서 하고, 전날에는 점검만 하는 흐름이 좋습니다.",
  "recommendedDates": [
    {
      "date": "2026-05-10",
      "label": "준비 집중",
      "reason": "커리어 점수가 높습니다."
    }
  ],
  "cautionDates": [
    {
      "date": "2026-05-12",
      "label": "무리 금지",
      "reason": "리스크 신호가 있습니다."
    }
  ],
  "firstAction": "오늘 예상 질문 리스트를 정리합니다.",
  "messageDraft": "면접 일정 확인 감사합니다. 준비해서 뵙겠습니다.",
  "reasoningSummary": "커리어 신호와 리스크 신호를 함께 보았습니다.",
  "disclaimer": "중요한 결정은 현실 정보와 함께 판단하세요.",
  "llmEnhanced": true
}
```

---

## 6. 새로 만들 파일

### 백엔드

- `app/schemas/ai_retention.py`
  - API request/response 모델
  - LLM structured output 모델

- `app/services/timing_signal_service.py`
  - `MonthlyTransitAnalysis.daily_scores`를 API와 LLM에 넣을 수 있는 형태로 변환
  - LLM이 꺼져 있을 때 사용할 fallback 문장 생성

- `app/services/llm_retention_client.py`
  - xAI와 DeepSeek를 교체 가능하게 호출
  - provider별 응답 파싱
  - Pydantic 검증

- `app/services/ai_retention_service.py`
  - 출생 정보로 natal profile 생성
  - 월간 트랜짓 분석 생성
  - timing signal 생성
  - LLM 호출
  - fallback 처리
  - 캐시 key 생성

- `app/routers/ai_retention.py`
  - `/api/ai-retention/*` route 제공

### 프론트엔드

- `app/lib/aiRetention.ts`
  - 타입 정의
  - API query builder
  - route builder
  - 날짜 helper

- `app/lib/aiRetentionStorage.ts`
  - 브라우저 localStorage 저장
  - 코치 답변과 오늘 브리핑 archive

- `components/ActionCalendarSections.tsx`
  - 월간 액션 캘린더 UI

- `components/DailyBriefSections.tsx`
  - 오늘 브리핑 UI

- `components/CoachPanel.tsx`
  - 질문 입력과 결과 표시 client component

- `app/calendar/page.tsx`
- `app/today/page.tsx`
- `app/coach/page.tsx`

### 테스트

- `tests/test_ai_retention_service.py`
- `tests/test_ai_retention_api.py`
- `tests/test_llm_retention_client.py`
- `app/lib/aiRetention.test.ts`
- `app/lib/aiRetentionStorage.test.ts`

---

## 7. 수정할 파일

- `app/main.py`
  - 새 router include

- `app/routers/__init__.py`
  - 필요하면 새 router export

- `app/lib/floatingMenu.ts`
  - 오늘 브리핑, 액션 캘린더, AI 코치 링크 추가

- `app/lib/floatingMenu.test.ts`
  - 새 링크 테스트 추가

- `app/globals.css`
  - 캘린더 카드, 브리핑 카드, 코치 폼 스타일 추가

- `README.md`
  - 새 기능, 새 API, 새 환경 변수, 실행 방법 추가

- `requirements.txt`
  - MariaDB persistence를 실제로 추가할 때만 `pymysql` 추가

---

## 8. 작업 순서

### Task 1. 백엔드 스키마 추가

파일:

- `app/schemas/ai_retention.py`
- `tests/test_ai_retention_service.py`

할 일:

- `ActionCalendarRequest`
- `DailyBriefRequest`
- `CoachRequest`
- `ActionCalendarResponse`
- `DailyBriefResponse`
- `CoachResponse`
- LLM output 모델 추가

검증:

```bash
python -m unittest tests.test_ai_retention_service -v
```

완료 기준:

- camelCase alias가 API 응답에 맞게 동작
- 기존 birth request 형식과 호환

### Task 2. deterministic timing signal 생성

파일:

- `app/services/timing_signal_service.py`
- `tests/test_ai_retention_service.py`

할 일:

- `DailyTransitScore`를 `TimingSignal`로 변환
- 일별 score를 1-10 점수로 변환
- `supportive`, `neutral`, `challenging` tone 계산
- fallback action, avoid, reason 생성

검증:

```bash
python -m unittest tests.test_ai_retention_service -v
```

완료 기준:

- LLM이 없어도 월간 캘린더와 오늘 브리핑 생성 가능

### Task 3. LLM provider 공통 클라이언트 추가

파일:

- `app/services/llm_retention_client.py`
- `tests/test_llm_retention_client.py`

할 일:

- `LLMRetentionClient.from_env()` 구현
- `LLM_RETENTION_PROVIDER=xai` 지원
- `LLM_RETENTION_PROVIDER=deepseek` 지원
- xAI Responses API 응답 파싱
- DeepSeek Chat Completions 응답 파싱
- Pydantic validation 실패 시 `None` 반환

검증:

```bash
python -m unittest tests.test_llm_retention_client -v
```

완료 기준:

- provider를 바꿔도 product service 코드는 변하지 않음

### Task 4. AI retention service 추가

파일:

- `app/services/ai_retention_service.py`
- `tests/test_ai_retention_service.py`

할 일:

- action calendar 생성
- daily brief 생성
- timing coach 답변 생성
- 캐시 key 생성
- LLM 실패 시 fallback 적용

캐시 정책:

- calendar: 7일
- daily brief: 24시간
- coach answer: 24시간

검증:

```bash
python -m unittest tests.test_ai_retention_service -v
```

완료 기준:

- `LLM_RETENTION_API_KEY`가 없어도 API 응답 생성
- LLM 성공 시 `llmEnhanced=true`
- LLM 실패 시 `llmEnhanced=false`

### Task 5. FastAPI route 추가

파일:

- `app/routers/ai_retention.py`
- `app/main.py`
- `tests/test_ai_retention_api.py`

할 일:

- `/api/ai-retention/action-calendar`
- `/api/ai-retention/daily-brief`
- `/api/ai-retention/coach`
- FastAPI app에 router include

검증:

```bash
python -m unittest tests.test_ai_retention_api -v
```

완료 기준:

- FastAPI docs에서 새 API 확인 가능
- 필수 parameter 누락 시 422 반환
- 정상 요청은 200 반환

### Task 6. 프론트엔드 helper와 localStorage 추가

파일:

- `app/lib/aiRetention.ts`
- `app/lib/aiRetention.test.ts`
- `app/lib/aiRetentionStorage.ts`
- `app/lib/aiRetentionStorage.test.ts`

할 일:

- API query parameter builder
- `/calendar`, `/today`, `/coach` route builder
- 한국 날짜 helper
- localStorage archive read/write
- 깨진 JSON 처리

검증:

```bash
node --import tsx --test app/lib/aiRetention.test.ts app/lib/aiRetentionStorage.test.ts
```

완료 기준:

- `country` page param이 API에서는 `countryCode`로 변환
- archive 저장 실패가 화면 기능을 막지 않음

### Task 7. 월간 액션 캘린더 UI

파일:

- `components/ActionCalendarSections.tsx`
- `app/calendar/page.tsx`
- `app/globals.css`

할 일:

- 출생 정보 입력
- 월간 액션 카드 grid
- 오늘 브리핑 이동 링크
- AI 코치 이동 링크
- LLM 여부 표시

검증:

```bash
npm run build
```

완료 기준:

- typed routes 오류 없음
- birth detail 입력 후 calendar 표시

### Task 8. 오늘 브리핑 UI

파일:

- `components/DailyBriefSections.tsx`
- `app/today/page.tsx`
- `app/globals.css`

할 일:

- 오늘 날짜 기준 브리핑 표시
- targetDate query 지원
- 오늘 할 일, 피할 일, 시간대 힌트, 회고 질문 표시
- calendar와 coach 이동

검증:

```bash
npm run build
```

완료 기준:

- `/today`가 직접 접근 가능
- `/calendar`의 특정 날짜에서 `/today?targetDate=...`로 이동 가능

### Task 9. AI 결정 타이밍 코치 UI

파일:

- `components/CoachPanel.tsx`
- `app/coach/page.tsx`
- `app/globals.css`

할 일:

- 질문 textarea
- submit loading 상태
- 에러 상태
- 추천 날짜 표시
- 주의 날짜 표시
- 첫 행동 표시
- 메시지 초안 표시
- 결과 localStorage 저장

검증:

```bash
npm run build
```

완료 기준:

- 사용자가 질문을 입력하고 답변을 볼 수 있음
- LLM이 꺼져도 fallback 답변 표시

### Task 10. 네비게이션과 README 정리

파일:

- `app/lib/floatingMenu.ts`
- `app/lib/floatingMenu.test.ts`
- `README.md`

할 일:

- 기존 horoscope 결과에서 `/today`, `/calendar`, `/coach`로 이동 가능하게 추가
- README에 route, API, env, 검증 명령 추가

검증:

```bash
node --import tsx --test app/lib/floatingMenu.test.ts
```

완료 기준:

- 사용자가 기존 월운 화면에서 새 재방문 기능으로 자연스럽게 이동 가능

### Task 11. 전체 검증

백엔드:

```bash
python -m unittest discover -s tests -v
```

프론트엔드:

```bash
npm run test:frontend
node --import tsx --test app/lib/aiRetention.test.ts app/lib/aiRetentionStorage.test.ts
```

빌드:

```bash
npm run build
```

로컬 실행:

```bash
npm run dev:backend
npm run dev
```

수동 확인 URL:

```text
http://127.0.0.1:3000/calendar
http://127.0.0.1:3000/today
http://127.0.0.1:3000/coach
http://127.0.0.1:8000/docs
```

완료 기준:

- 세 페이지가 모두 열린다.
- 백엔드가 꺼져 있을 때는 안내 카드가 보인다.
- 백엔드가 켜져 있을 때는 실제 결과가 보인다.
- `LLM_RETENTION_API_KEY`가 없어도 fallback 결과가 나온다.
- provider를 DeepSeek로 바꿔도 product service 코드는 바뀌지 않는다.

---

## 9. 선택 사항: MariaDB 저장 구현

이 단계는 1차 구현 후 필요할 때만 진행합니다.

필요해지는 경우:

- 사용자가 여러 기기에서 저장 기록을 보고 싶을 때
- 로그인 기능을 붙일 때
- 코치 질문 히스토리를 서버에 남기고 싶을 때
- LLM 생성 결과를 서버 재시작 후에도 유지하고 싶을 때

### MariaDB migration 파일

파일:

- `deploy/mariadb/001_ai_retention.sql`

테이블:

```sql
CREATE TABLE IF NOT EXISTS ai_retention_calendar_cache (
  cache_key VARCHAR(255) NOT NULL PRIMARY KEY,
  birth_signature_hash CHAR(64) NOT NULL,
  provider VARCHAR(32) NOT NULL,
  model VARCHAR(128) NOT NULL,
  year SMALLINT NOT NULL,
  month TINYINT NOT NULL,
  payload_json JSON NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_calendar_birth_month (birth_signature_hash, year, month),
  INDEX idx_calendar_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_retention_daily_brief_cache (
  cache_key VARCHAR(255) NOT NULL PRIMARY KEY,
  birth_signature_hash CHAR(64) NOT NULL,
  provider VARCHAR(32) NOT NULL,
  model VARCHAR(128) NOT NULL,
  target_date DATE NOT NULL,
  payload_json JSON NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_daily_birth_date (birth_signature_hash, target_date),
  INDEX idx_daily_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_retention_coach_archive (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_profile_id BIGINT UNSIGNED NULL,
  birth_signature_hash CHAR(64) NOT NULL,
  provider VARCHAR(32) NOT NULL,
  model VARCHAR(128) NOT NULL,
  question_hash CHAR(64) NOT NULL,
  question_text TEXT NOT NULL,
  payload_json JSON NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_coach_birth_created (birth_signature_hash, created_at),
  INDEX idx_coach_question_hash (question_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### MariaDB 환경 변수

```env
AI_RETENTION_DB_URL=mysql+pymysql://user:password@127.0.0.1:3306/monthly_fortune
```

### MariaDB 적용 명령

```bash
mysql -u user -p monthly_fortune < deploy/mariadb/001_ai_retention.sql
```

### Python dependency

`requirements.txt`에 필요할 때만 추가:

```text
pymysql==1.1.1
```

---

## 10. LLM prompt 원칙

LLM system prompt는 다음 원칙을 지켜야 합니다.

- 한국어로 답변
- 과장된 예언 금지
- deterministic signal에 없는 날짜 발명 금지
- 의료, 법률, 투자 확정 조언 금지
- 사용자가 실제로 할 수 있는 행동 중심
- 답변은 반드시 JSON
- 결과는 Pydantic schema로 검증

코치 답변에는 항상 아래 성격의 문구가 포함되어야 합니다.

```text
운세는 의사결정 보조 자료입니다. 중요한 결정은 현실 정보와 함께 판단하세요.
```

---

## 11. 실패 처리 정책

아래 상황에서는 LLM 결과를 버리고 fallback을 사용합니다.

- API key 없음
- timeout
- HTTP error
- 빈 응답
- JSON parse 실패
- Pydantic validation 실패
- 응답 날짜가 요청 월 범위를 벗어남
- 필수 필드 누락

fallback은 부끄러운 임시 기능이 아니라 제품의 안정 장치입니다.

화면에는 아래처럼 표시합니다.

```text
기본 리딩
```

LLM 성공 시:

```text
AI 확장 리딩
```

---

## 12. 비용 관리

LLM 호출을 최소화합니다.

권장 캐시:

- 월간 액션 캘린더: 7일
- 오늘 브리핑: 24시간
- 코치 답변: 24시간

코치 cache key:

```text
birth_signature + year + month + normalized_question_hash + provider + model + prompt_version
```

provider나 model이 바뀌면 cache key도 바뀌어야 합니다.

---

## 13. 사용자가 수정하기 좋은 지점

제품 이름 후보:

- 오늘의 타이밍
- AI 타이밍 코치
- 월간 액션 캘린더
- 결정 타이밍 리딩

수정하기 좋은 부분:

- `/today` 문구 톤
- `/coach` 질문 예시
- `calendar` 카드에 표시할 category 이름
- LLM provider 기본값
- 캐시 TTL
- MariaDB 저장 시점
- 유료화 범위

---

## 14. 최종 완료 기준

개발 완료라고 말하려면 아래가 모두 되어야 합니다.

- `/calendar` 페이지 동작
- `/today` 페이지 동작
- `/coach` 페이지 동작
- FastAPI docs에 새 API 3개 표시
- `LLM_RETENTION_API_KEY` 없이 fallback 동작
- xAI provider mock 테스트 통과
- DeepSeek provider mock 테스트 통과
- 프론트엔드 helper 테스트 통과
- backend unittest 통과
- `npm run build` 통과
- README 업데이트

---

## 15. 다음 실행 방법

바로 구현한다면 순서는 이렇습니다.

1. Task 1부터 Task 5까지 백엔드 먼저 구현
2. Task 6으로 프론트 helper 구현
3. Task 7-9로 화면 구현
4. Task 10으로 네비게이션과 README 정리
5. Task 11로 전체 검증
6. MariaDB는 실제 저장 요구가 생긴 뒤 별도 작업


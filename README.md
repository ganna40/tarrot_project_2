# Tarot Engine Lab

구조화된 타로 지식과 명시적 관계 규칙으로 **판정과 카드 흐름을 먼저 계산**하고, OpenAI는 그 결과를 자연스러운 한국어로 표현하는 Tarot Engine v1입니다. 같은 저장소의 `docs/`에는 GitHub Pages에서 실행되는 대화형 API 검증 화면이 들어 있습니다.

## 구조

```text
GitHub Pages 정적 검증 화면
        │ POST /api/v1/readings
        │ 또는 /api/consultation
        ▼
FastAPI
  ├─ 질문 문맥 분류
  ├─ PostgreSQL 지식 조회
  ├─ 태그 관계 Rule Engine
  ├─ 점수·판정·전체 흐름 확정
  └─ OpenAI 문장화(선택)
        │
        ▼
PostgreSQL
```

브라우저에는 OpenAI API 키를 넣지 않습니다. `OPENAI_API_KEY`는 백엔드 환경 변수에만 저장합니다.

## 현재 구현

- RWS 78장 고정 식별자
- 3카드 `시작 → 전개 → 결과`
- 정방향·역방향
- `GENERAL`, `LOVE`, `CAREER`, `BUSINESS`, `MONEY`, `TIMING` 문맥
- JSON/JSONB를 사용하지 않는 핵심 지식 정규 테이블 8개
- 인접 카드 태그 관계 규칙과 Golden Dawn 원소 보정
- OpenAI 호출 전에 `score`, `verdict`, `flow_summary` 확정
- OpenAI 장애 시 규칙 기반 fallback
- 출처·태그·적용 규칙 trace
- 선택적 Bearer 또는 `X-API-Key` 접근 보호
- GitHub Pages용 Mock/Live 대화형 검증 화면

> 현재 운영 지식은 **엔진 검증용 `INTERNAL_DEMO` 데이터**입니다. 78장의 식별자는 모두 들어 있지만, 승인된 정·역방향 의미는 우선 10장에만 들어 있습니다. 지원되지 않은 카드를 Live API로 선택하면 `KNOWLEDGE_NOT_READY`가 반환됩니다. Public Domain 원전 추출·검수·적재는 다음 데이터 단계입니다.

## 로컬 백엔드 실행

```bash
cp .env.example .env
docker compose up --build
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

실행 후:

```text
API: http://localhost:8000
Docs: http://localhost:8000/docs
Health: http://localhost:8000/health
```

OpenAI 문장화를 사용하려면 `.env`에 서버측 값만 넣습니다.

```dotenv
OPENAI_API_KEY=...
OPENAI_MODEL=사용할_모델_ID
```

공개된 백엔드를 보호하려면 다음 값도 설정합니다.

```dotenv
API_ACCESS_KEY=충분히_긴_임의의_문자열
```

정적 화면의 `API 설정`에서 같은 값을 Bearer Token 또는 `X-API-Key`로 전달할 수 있습니다.

## 정적 검증 화면

로컬 실행:

```bash
python3 -m http.server 8080 --directory docs
```

Windows:

```powershell
py -m http.server 8080 --directory docs
```

브라우저에서 `http://localhost:8080`을 열고 `API 설정`에서 다음을 입력합니다.

```text
실행 모드: 원격 API
API 기본 URL: http://localhost:8000
상담 엔드포인트: /api/v1/readings
Health 경로: /health
```

GitHub Pages에서 HTTPS 백엔드를 호출해야 합니다. HTTPS 페이지에서 로컬 HTTP API를 직접 호출하면 브라우저의 Mixed Content 정책으로 차단될 수 있으므로, 로컬 API 검증 때는 정적 화면도 로컬에서 여는 방식이 가장 간단합니다.

## GitHub Pages 활성화

저장소에서 한 번만 설정합니다.

```text
Settings
→ Pages
→ Build and deployment
→ Source: Deploy from a branch
→ Branch: new
→ Folder: /docs
→ Save
```

예상 주소:

```text
https://ganna40.github.io/tarrot_project_2/
```

실제 저장소 이름은 `tarrot_project_2`로 `r`이 두 개입니다.

## API 예시

```bash
curl -X POST http://localhost:8000/api/v1/readings \
  -H "Content-Type: application/json" \
  -d '{
    "question": "게임을 만들면 투자를 받을 수 있을까?",
    "reading_context": "BUSINESS",
    "spread_type": "three_card",
    "cards": [
      {"code": "TEN_OF_SWORDS", "orientation": "UPRIGHT"},
      {"code": "EIGHT_OF_WANDS", "orientation": "UPRIGHT"},
      {"code": "HIEROPHANT", "orientation": "UPRIGHT"}
    ],
    "response_length": "SHORT",
    "include_trace": true,
    "use_llm": false
  }'
```

정적 검증 UI의 기존 기본값과 호환되도록 `POST /api/consultation`도 같은 요청을 받습니다.

## 테스트

```bash
python -m pip install -r backend/requirements.txt
python -m pytest -q
npm test
npm run check:static
```

GitHub Actions도 Python 백엔드 테스트와 정적 UI 테스트를 함께 실행합니다.

## 핵심 파일

```text
backend/app/models.py          정규 DB 모델
backend/app/repository.py      승인 지식 조회
backend/app/engine.py          결정적 판정·흐름 계산
backend/app/openai_service.py  OpenAI 문장화
backend/app/main.py            FastAPI
backend/app/seed.py            78장 식별자 + INTERNAL_DEMO

docs/                          GitHub Pages 검증 화면
```

## 다음 데이터 단계

```text
Public Domain 원전
→ 페이지 단위 추출
→ 후보 CSV
→ 자동 검증
→ 사람 검수
→ APPROVED 데이터만 PostgreSQL 적재
```

해석 품질의 핵심 자산은 프롬프트가 아니라 `card_meanings`, `card_meaning_tags`, `card_correspondences`, `relation_rules`입니다.

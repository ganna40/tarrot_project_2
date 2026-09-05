# Tarot Engine Lab

타로 규칙 엔진을 개발하면서 요청 JSON, 응답, 판정, 흐름, trace를 대화형 화면에서 검증하기 위한 정적 웹 페이지입니다.

현재 저장소는 **정적 검증 UI**까지 구현되어 있습니다. 실제 PostgreSQL 규칙 엔진과 OpenAI 호출은 별도 백엔드 API에 두고, 이 페이지가 그 API를 호출합니다.

## 구조

```text
GitHub Pages 정적 UI
        │
        │ POST /api/consultation
        ▼
FastAPI 백엔드
        ├─ PostgreSQL 규칙·원전 데이터
        └─ OpenAI API 문장화
```

정적 페이지에 OpenAI API 키를 넣지 않습니다. API 키는 백엔드 환경 변수로만 보관합니다.

## 현재 기능

- RWS 78장 선택
- 정방향·역방향
- 3카드 `시작 → 전개 → 결과`
- 질문 분야와 답변 길이 설정
- 로컬 데모 / 원격 API 전환
- Bearer 또는 `X-API-Key` 방식의 백엔드 접근 토큰
- 요청 JSON, 원본 응답 JSON, trace 확인 및 복사
- API health check
- 입력·HTTP·CORS·타임아웃 오류 표시
- 모바일 대응

## 로컬 실행

저장소 루트에서 실행합니다.

```bash
python3 -m http.server 8080 --directory docs
```

Windows PowerShell에서는 다음 명령을 사용할 수 있습니다.

```powershell
py -m http.server 8080 --directory docs
```

브라우저에서 `http://localhost:8080`을 엽니다.

## 테스트

Node.js 22 이상이 필요합니다. 외부 npm 패키지는 사용하지 않습니다.

```bash
npm test
npm run check:static
npm run check
```

## GitHub Pages 활성화

이 저장소의 GitHub 화면에서 아래와 같이 한 번만 설정합니다.

```text
Settings
→ Pages
→ Build and deployment
→ Source: Deploy from a branch
→ Branch: new
→ Folder: /docs
→ Save
```

배포가 완료되면 일반적인 프로젝트 페이지 주소는 다음 형식입니다.

```text
https://ganna40.github.io/tarrot_project_2/
```

> 실제 저장소 이름은 `tarrot_project_2`입니다. 사용자가 처음 전달한 `tarot_project_2`와 철자가 다릅니다.

## API 연결 방법

페이지 우측 상단의 `API 설정`에서 다음을 지정합니다.

```text
실행 모드: 원격 API
API 기본 URL: https://your-api.example.com
상담 엔드포인트: /api/consultation
Health 경로: /health
인증 방식: 없음 / Bearer / X-API-Key
```

백엔드 접근 토큰은 현재 브라우저 탭의 메모리에만 유지하며 `localStorage`에 저장하지 않습니다. **OpenAI API 키를 이 입력란에 넣지 마세요.**

GitHub Pages에서 호출할 백엔드는 HTTPS를 권장합니다. 로컬 HTTP 백엔드를 테스트할 때 브라우저가 혼합 콘텐츠를 차단하면 이 정적 페이지도 로컬에서 실행하십시오.

## 요청 계약

```json
{
  "question": "게임을 만들면 투자를 받을 수 있을까?",
  "spread_type": "three_card",
  "context": "투자자가 데모를 먼저 보겠다고 했다.",
  "reading_context": "BUSINESS",
  "cards": [
    { "code": "TEN_OF_SWORDS", "orientation": "UPRIGHT" },
    { "code": "EIGHT_OF_WANDS", "orientation": "UPRIGHT" },
    { "code": "HIEROPHANT", "orientation": "UPRIGHT" }
  ],
  "response_length": "SHORT",
  "include_trace": true,
  "use_llm": true
}
```

`reading_context`를 자동 분류하려면 UI에서 `자동 분류`를 선택합니다. 이 경우 해당 필드를 요청에서 생략합니다.

## 권장 응답 계약

```json
{
  "spread_name": "3카드 흐름",
  "spread_type": "three_card",
  "reading_context": "BUSINESS",
  "verdict": "CAUTIOUS",
  "score": 0.82,
  "flow_summary": "기존 단계가 끝난 뒤 빠르게 전개되어 공식적 구조로 이어지는 흐름",
  "cards": [],
  "overall_interpretation": "플레이 가능한 결과물을 먼저 보여주는 것이 중요합니다.",
  "advice": "투자 조건과 역할을 문서로 확인하세요.",
  "llm_used": true,
  "trace": {
    "tags": ["ENDING", "MOVEMENT", "FORMALIZATION"],
    "rules": ["ACCELERATE", "FORMALIZE"]
  },
  "disclaimer": "타로 해석은 참고용입니다."
}
```

기존 API가 `overall_interpretation`과 `advice`만 반환해도 화면에 표시됩니다.

## FastAPI CORS 예시

GitHub Pages와 로컬 검증 페이지의 Origin을 허용해야 합니다.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ganna40.github.io",
        "http://localhost:8080",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)
```

## 문서

- 설계 명세: `docs/superpowers/specs/2026-09-05-tarot-engine-v1-design.md`
- 정적 검증 UI 구현 계획: `docs/superpowers/plans/2026-09-05-static-tarot-validator-implementation-plan.md`

## 다음 구현 단계

1. PostgreSQL 정규 스키마와 migration
2. RWS 78장 seed
3. 원전 후보 CSV 검수·적재 파이프라인
4. 태그 관계 Rule Engine
5. `InterpretationPlan` 생성
6. OpenAI 문장화 서비스
7. 이 정적 페이지를 이용한 100개 질문 검증

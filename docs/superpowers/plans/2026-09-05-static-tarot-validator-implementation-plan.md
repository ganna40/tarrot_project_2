# Static Tarot Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task.

**Goal:** GitHub Pages에서 Tarot Engine v1 API 요청·응답을 대화형으로 검증하는 무빌드 정적 페이지를 만든다.

**Architecture:** `docs/`의 HTML/CSS/ES Modules가 브라우저에서 실행된다. 로컬 데모는 외부 호출 없이 UI를 검증하고, 원격 모드는 사용자가 지정한 FastAPI를 호출한다.

**Tech Stack:** HTML, CSS, browser ES modules, Node.js built-in test runner, GitHub Pages

**Spec:** `docs/superpowers/specs/2026-09-05-tarot-engine-v1-design.md`

## Global Constraints

- 외부 프론트엔드 라이브러리와 CDN을 사용하지 않는다.
- OpenAI API 키를 브라우저에서 받거나 저장하지 않는다.
- 백엔드 접근 토큰은 localStorage에 저장하지 않는다.
- API 계약은 `POST /api/consultation`을 기본값으로 한다.
- 3카드 요청만 생성한다.

---

### Task 1: 카드 목록과 요청 생성

**Files:**
- Create: `docs/assets/cards.js`
- Create: `docs/assets/payload.js`
- Test: `tests/cards.test.mjs`
- Test: `tests/payload.test.mjs`

- [x] 실패 테스트에서 78장, 고정 코드, 요청 validation을 정의한다.
- [x] 실패를 확인한다.
- [x] 카드 목록과 payload builder를 구현한다.
- [x] 카드 중복·빈 질문·방향 오류 테스트를 통과시킨다.

### Task 2: API 및 응답 어댑터

**Files:**
- Create: `docs/assets/api-client.js`
- Create: `docs/assets/response.js`
- Test: `tests/api-client.test.mjs`
- Test: `tests/response.test.mjs`

- [x] URL, 인증 헤더, HTTP 오류, health check 실패 테스트를 작성한다.
- [x] fetch 기반 API client를 구현한다.
- [x] v1과 legacy 응답을 공통 형식으로 정규화한다.
- [x] 관련 테스트를 통과시킨다.

### Task 3: 로컬 골든 데모

**Files:**
- Create: `docs/assets/demo.js`
- Test: `tests/demo.test.mjs`

- [x] `10S → 8W → Hierophant` 기대 흐름을 테스트로 정의한다.
- [x] UI 검증 전용 응답을 구현한다.
- [x] 데모가 실제 API 호출이 아님을 명시한다.

### Task 4: 정적 대화 UI

**Files:**
- Create: `docs/index.html`
- Create: `docs/styles.css`
- Create: `docs/assets/app.js`
- Create: `docs/.nojekyll`
- Create: `scripts/check-static.mjs`
- Test: `tests/static.test.mjs`

- [x] 필요한 DOM과 보안 조건을 실패 테스트로 정의한다.
- [x] 3열형 대화·카드·검사기 UI를 구현한다.
- [x] 요청, 응답, trace, 복사, 오류 상태를 연결한다.
- [x] API 토큰 비저장 검증을 통과시킨다.

### Task 5: 저장소 실행·배포 문서와 CI

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `.github/workflows/ci.yml`
- Create: `package.json`

- [x] 로컬 실행과 API 계약을 문서화한다.
- [x] GitHub Pages `new / docs` 활성화 절차를 적는다.
- [x] CORS 예시와 보안 주의사항을 적는다.
- [x] push 및 PR에서 자동 테스트하는 CI를 추가한다.

## Verification

```bash
npm test
npm run check:static
python3 -m http.server 8080 --directory docs
```

브라우저 검증 항목:

- 기본 골든 케이스 응답 표시
- 78장 선택과 무작위 카드
- 요청·응답·trace 표시
- 원격 API health check
- API 실패 메시지
- 모바일 레이아웃

# Tarot Engine v1 설계 명세

## 목표

원전에서 검수한 구조화 지식과 명시적 규칙을 먼저 적용하고, OpenAI는 이미 확정된 판정과 흐름을 자연스러운 한국어로 표현한다.

```text
질문 + 카드 3장
→ 문맥 분류
→ PostgreSQL 지식 조회
→ 카드 의미·태그·Golden Dawn 대응 조회
→ 인접 카드 관계 규칙 적용
→ 점수·판정·전체 흐름 확정
→ OpenAI 문장화
```

## 단순 아키텍처

```text
정적 검증 UI (GitHub Pages)
          │ HTTPS/JSON
          ▼
FastAPI 단일 백엔드
    ├─ PostgreSQL
    └─ OpenAI API
```

v1에서 Redis, Neo4j, 별도 Vector DB, LangChain, 마이크로서비스, 자율 에이전트는 사용하지 않는다.

## 역할 분리

- PostgreSQL: 원전, 카드 의미, 대응 관계, 태그, 규칙, 검수 상태 저장
- Rule Engine: 문맥, 전환, 점수, verdict, flow 확정
- OpenAI: 확정된 `InterpretationPlan`을 문장으로 표현
- 정적 UI: 요청·응답·trace 검증

## 핵심 지식 테이블

핵심 지식에는 JSON/JSONB 컬럼을 사용하지 않는다.

1. `sources`
2. `tarot_cards`
3. `card_meanings`
4. `interpretation_tags`
5. `card_meaning_tags`
6. `card_correspondences`
7. `relation_rules`
8. `spread_positions`

### sources

`code`, `title`, `author`, `publication_year`, `license_status`, `checksum`, `priority`, `is_active`를 가진다.

### tarot_cards

RWS 78장의 고정 코드, 한·영 이름, 아르카나, 슈트, 랭크, 번호, 정렬 순서를 가진다.

### card_meanings

카드·출처·방향·문맥별 의미와 `polarity`, `action_level`, `speed_level`, `stability_level`, `ending_level`, 출처 페이지, 검수 상태를 가진다.

### card_correspondences

`ELEMENT`, `PLANET`, `ZODIAC`, `DECAN`, `GD_TITLE`, `HEBREW_LETTER`, `TREE_PATH`, `SEPHIRAH`를 출처별로 저장한다.

### relation_rules

카드 78×78 조합이 아니라 태그 전환만 저장한다.

```text
ENDING → MOVEMENT       = ACCELERATE
MOVEMENT → FORMALIZATION = FORMALIZE
CONFLICT → STABILITY     = RESOLVE
```

## v1 해석 범위

- RWS 78장
- 정방향·역방향
- 3카드 `START → DEVELOPMENT → OUTCOME`
- 문맥: `GENERAL`, `LOVE`, `CAREER`, `BUSINESS`, `MONEY`, `TIMING`
- 인접 카드 두 쌍만 계산
- Golden Dawn 대응 중 원소 관계만 제한적으로 점수 보정
- 출처·페이지·적용 규칙 trace
- OpenAI 실패 시 규칙 기반 fallback

## 판정 원칙

```text
base_score = Σ(card.polarity × position.weight) / Σ(position.weight)
final_score = base_score + relation_delta + elemental_modifier
```

- 시작 0.9, 전개 1.0, 결과 1.2
- 최종 점수는 -5~5
- `>= 1.25`: POSITIVE
- `<= -1.25`: NEGATIVE
- 나머지: CAUTIOUS

OpenAI 호출 전에 verdict와 flow를 확정한다. OpenAI는 이를 변경할 수 없다.

## 원전 적재 흐름

```text
원본 파일
→ 페이지 텍스트 추출
→ OpenAI 구조화 후보 생성
→ CSV
→ 자동 검증
→ 사람 승인
→ PostgreSQL 적재
```

후보 데이터가 자동으로 운영 DB에 들어가서는 안 된다. 모든 운영 행은 출처와 검수 상태를 가져야 한다.

## 정적 검증 UI

정적 페이지는 다음을 지원한다.

- 78장과 방향 선택
- 질문·상황·문맥·답변 길이 입력
- 로컬 데모와 원격 API 전환
- 요청 JSON, 원본 응답, trace 표시
- health check와 CORS/HTTP 오류 표시
- 백엔드 접근 토큰은 메모리에만 유지

정적 페이지는 OpenAI API를 직접 호출하지 않는다.

## API 핵심 계약

`POST /api/consultation`

입력은 질문, 추가 문맥, 3장, 방향, 문맥, trace·LLM 옵션이다. 출력은 `verdict`, `score`, `flow_summary`, `overall_interpretation`, `advice`, `trace`를 포함한다.

## 완료 기준

1. 78장과 정·역방향을 식별한다.
2. 승인된 의미와 규칙만 사용한다.
3. 카드 1→2, 카드 2→3 전환을 결정적으로 계산한다.
4. OpenAI 호출 전에 verdict와 flow를 확정한다.
5. OpenAI 장애 시에도 유효한 응답을 반환한다.
6. trace로 의미·출처·페이지·규칙을 확인할 수 있다.
7. 정적 페이지에서 로컬 데모와 원격 API를 모두 검증할 수 있다.

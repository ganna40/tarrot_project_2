import { getCard } from './cards.js';

const GOLDEN_CODES = ['TEN_OF_SWORDS', 'EIGHT_OF_WANDS', 'HIEROPHANT'];

function isGoldenCase(payload) {
  return payload.cards?.length === 3
    && payload.cards.every((card, index) => card.code === GOLDEN_CODES[index] && card.orientation === 'UPRIGHT');
}

export async function runDemoConsultation(payload) {
  await new Promise((resolve) => setTimeout(resolve, 280));

  if (isGoldenCase(payload)) {
    return {
      spread_name: '3카드 흐름',
      spread_type: 'three_card',
      reading_context: payload.reading_context ?? 'BUSINESS',
      verdict: 'POSITIVE',
      score: 2.36,
      flow_summary: '끝나던 국면 뒤로 상황이 빠르게 움직이고, 계약과 절차로 구체화되는 흐름',
      cards: payload.cards.map((card, index) => ({
        ...card,
        position: ['시작', '전개', '결과'][index],
        name_ko: getCard(card.code).nameKo,
        name_en: getCard(card.code).nameEn,
      })),
      overall_interpretation: '기존 고민 단계가 끝난 뒤 실제 결과물이 나오면 논의가 빠르게 움직이고 공식 조건을 정리할 가능성이 커지는 흐름입니다. 다만 긍정 판정은 투자 확정을 뜻하지 않으므로, 플레이 가능한 데모와 함께 금액·지분·역할을 문서로 확인해야 합니다.',
      advice: '작게라도 완성된 데모와 함께 투자 금액·지분·의사결정 권한을 문서로 확인하세요.',
      llm_used: false,
      trace: {
        mode: 'LOCAL_DEMO',
        tags: ['ENDING', 'MOVEMENT', 'FORMALIZATION'],
        transitions: ['ACCELERATE', 'FORMALIZE'],
        note: '현재 CURATED_TAROT_V1의 대표 입력과 맞춘 정적 검증용 응답이며 실제 DB나 OpenAI는 호출하지 않습니다.',
      },
      disclaimer: '이 결과는 UI 검증용 로컬 데모이며 실제 타로 엔진의 판정이 아닙니다.',
    };
  }

  const labels = payload.cards.map(({ code, orientation }) => {
    const card = getCard(code);
    return `${card.nameKo}(${orientation === 'REVERSED' ? '역방향' : '정방향'})`;
  });

  return {
    spread_name: '3카드 흐름',
    spread_type: 'three_card',
    reading_context: payload.reading_context ?? 'AUTO',
    verdict: 'DEMO',
    score: 0,
    flow_summary: `${labels.join(' → ')} 조합의 요청 형식을 확인했습니다.`,
    cards: payload.cards,
    overall_interpretation: '현재는 로컬 데모 모드입니다. 카드 선택, 요청 JSON, 대화 화면을 검증할 수 있지만 실제 해석은 생성하지 않습니다. API 설정에서 원격 API 모드로 전환하면 같은 요청을 백엔드에 보냅니다.',
    advice: 'API 기본 URL과 엔드포인트를 설정한 뒤 연결 테스트를 실행하세요.',
    llm_used: false,
    trace: payload.include_trace ? {
      mode: 'LOCAL_DEMO',
      note: 'Mock response; no external request was made.',
    } : null,
    disclaimer: '로컬 데모 응답입니다.',
  };
}

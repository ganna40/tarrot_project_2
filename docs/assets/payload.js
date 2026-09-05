import { CARD_BY_CODE } from './cards.js';

const ORIENTATIONS = new Set(['UPRIGHT', 'REVERSED']);
const READING_CONTEXTS = new Set(['AUTO', 'GENERAL', 'LOVE', 'CAREER', 'BUSINESS', 'MONEY', 'TIMING']);
const RESPONSE_LENGTHS = new Set(['SHORT', 'NORMAL', 'DETAILED']);

export class ReadingValidationError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'ReadingValidationError';
    this.code = code;
  }
}

export function validateReadingInput({
  question,
  cards,
  readingContext = 'AUTO',
  responseLength = 'NORMAL',
} = {}) {
  const normalizedQuestion = String(question ?? '').trim();
  if (!normalizedQuestion) {
    throw new ReadingValidationError('QUESTION_REQUIRED', '질문을 입력해 주세요.');
  }
  if (normalizedQuestion.length > 2000) {
    throw new ReadingValidationError('QUESTION_TOO_LONG', '질문은 2,000자 이하로 입력해 주세요.');
  }
  if (!Array.isArray(cards) || cards.length !== 3) {
    throw new ReadingValidationError('THREE_CARDS_REQUIRED', '카드를 정확히 3장 선택해 주세요.');
  }

  const codes = new Set();
  for (const [index, card] of cards.entries()) {
    if (!card || !CARD_BY_CODE.has(card.code)) {
      throw new ReadingValidationError('INVALID_CARD', `${index + 1}번째 카드 코드가 올바르지 않습니다.`);
    }
    if (!ORIENTATIONS.has(card.orientation)) {
      throw new ReadingValidationError('INVALID_ORIENTATION', `${index + 1}번째 카드 방향이 올바르지 않습니다.`);
    }
    if (codes.has(card.code)) {
      throw new ReadingValidationError('DUPLICATE_CARD', '같은 카드는 두 번 선택할 수 없습니다.');
    }
    codes.add(card.code);
  }

  if (!READING_CONTEXTS.has(readingContext)) {
    throw new ReadingValidationError('INVALID_CONTEXT', '질문 분야가 올바르지 않습니다.');
  }
  if (!RESPONSE_LENGTHS.has(responseLength)) {
    throw new ReadingValidationError('INVALID_RESPONSE_LENGTH', '답변 길이 값이 올바르지 않습니다.');
  }

  return {
    question: normalizedQuestion,
    cards: cards.map(({ code, orientation }) => ({ code, orientation })),
    readingContext,
    responseLength,
  };
}

export function buildConsultationPayload({
  question,
  context = '',
  readingContext = 'AUTO',
  cards,
  responseLength = 'NORMAL',
  includeTrace = false,
  useLlm = true,
} = {}) {
  const validated = validateReadingInput({ question, cards, readingContext, responseLength });
  const payload = {
    question: validated.question,
    spread_type: 'three_card',
    cards: validated.cards,
    response_length: validated.responseLength,
    include_trace: Boolean(includeTrace),
    use_llm: Boolean(useLlm),
  };

  const normalizedContext = String(context ?? '').trim();
  if (normalizedContext) payload.context = normalizedContext;
  if (validated.readingContext !== 'AUTO') payload.reading_context = validated.readingContext;

  return payload;
}

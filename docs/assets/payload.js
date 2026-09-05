import { CARD_BY_CODE } from './cards.js';

const ORIENTATIONS = new Set(['UPRIGHT', 'REVERSED']);
const READING_CONTEXTS = new Set(['AUTO', 'GENERAL', 'LOVE', 'CAREER', 'BUSINESS', 'MONEY', 'TIMING']);
const RESPONSE_LENGTHS = new Set(['SHORT', 'NORMAL', 'DETAILED']);
const LLM_REASONING_EFFORTS = new Set(['DEFAULT', 'LOW', 'MEDIUM', 'HIGH', 'XHIGH']);
const INTERPRETATION_STYLES = new Set(['PRECISE', 'BALANCED', 'RICH']);
const MODEL_ID_PATTERN = /^[A-Za-z0-9._:-]+$/;

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

function normalizeLlmOptions({ llmModel, llmReasoningEffort, interpretationStyle }) {
  const model = String(llmModel ?? '').trim();
  const reasoningEffort = String(llmReasoningEffort ?? 'DEFAULT').toUpperCase();
  const style = String(interpretationStyle ?? 'BALANCED').toUpperCase();

  if (model && (!MODEL_ID_PATTERN.test(model) || model.length > 128)) {
    throw new ReadingValidationError(
      'INVALID_LLM_MODEL',
      'AI 모델 ID에는 영문, 숫자, 점, 밑줄, 콜론, 하이픈만 사용할 수 있습니다.',
    );
  }
  if (!LLM_REASONING_EFFORTS.has(reasoningEffort)) {
    throw new ReadingValidationError('INVALID_LLM_REASONING_EFFORT', '추론 강도 값이 올바르지 않습니다.');
  }
  if (!INTERPRETATION_STYLES.has(style)) {
    throw new ReadingValidationError('INVALID_INTERPRETATION_STYLE', '해설 스타일 값이 올바르지 않습니다.');
  }
  return { model, reasoningEffort, style };
}

export function buildConsultationPayload({
  question,
  context = '',
  readingContext = 'AUTO',
  cards,
  responseLength = 'NORMAL',
  includeTrace = false,
  useLlm = true,
  llmModel = '',
  llmReasoningEffort = 'DEFAULT',
  interpretationStyle = 'BALANCED',
} = {}) {
  const validated = validateReadingInput({ question, cards, readingContext, responseLength });
  const shouldUseLlm = Boolean(useLlm);
  const payload = {
    question: validated.question,
    spread_type: 'three_card',
    cards: validated.cards,
    response_length: validated.responseLength,
    include_trace: Boolean(includeTrace),
    use_llm: shouldUseLlm,
  };

  const normalizedContext = String(context ?? '').trim();
  if (normalizedContext) payload.context = normalizedContext;
  if (validated.readingContext !== 'AUTO') payload.reading_context = validated.readingContext;

  if (shouldUseLlm) {
    const options = normalizeLlmOptions({ llmModel, llmReasoningEffort, interpretationStyle });
    if (options.model) payload.llm_model = options.model;
    if (options.reasoningEffort !== 'DEFAULT') payload.llm_reasoning_effort = options.reasoningEffort;
    payload.interpretation_style = options.style;
  }

  return payload;
}

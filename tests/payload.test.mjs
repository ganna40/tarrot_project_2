import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ReadingValidationError,
  buildConsultationPayload,
  validateReadingInput,
} from '../docs/assets/payload.js';

const cards = [
  { code: 'TEN_OF_SWORDS', orientation: 'UPRIGHT' },
  { code: 'EIGHT_OF_WANDS', orientation: 'UPRIGHT' },
  { code: 'HIEROPHANT', orientation: 'REVERSED' },
];

test('builds the v1 consultation API payload', () => {
  const payload = buildConsultationPayload({
    question: '게임을 만들면 투자를 받을 수 있을까?',
    context: '투자자가 데모를 먼저 보겠다고 했다.',
    readingContext: 'BUSINESS',
    cards,
    responseLength: 'SHORT',
    includeTrace: true,
    useLlm: true,
  });

  assert.deepEqual(payload, {
    question: '게임을 만들면 투자를 받을 수 있을까?',
    spread_type: 'three_card',
    context: '투자자가 데모를 먼저 보겠다고 했다.',
    reading_context: 'BUSINESS',
    cards,
    response_length: 'SHORT',
    include_trace: true,
    use_llm: true,
  });
});

test('AUTO context is omitted so the backend can classify it', () => {
  const payload = buildConsultationPayload({
    question: '이번 달 흐름은?',
    context: '',
    readingContext: 'AUTO',
    cards,
    responseLength: 'NORMAL',
    includeTrace: false,
    useLlm: false,
  });

  assert.equal('reading_context' in payload, false);
  assert.equal('context' in payload, false);
});

test('rejects duplicate cards before the API call', () => {
  assert.throws(
    () => validateReadingInput({ question: '질문', cards: [cards[0], cards[0], cards[2]] }),
    (error) => error instanceof ReadingValidationError && error.code === 'DUPLICATE_CARD',
  );
});

test('rejects an empty question', () => {
  assert.throws(
    () => validateReadingInput({ question: '   ', cards }),
    (error) => error instanceof ReadingValidationError && error.code === 'QUESTION_REQUIRED',
  );
});

test('rejects unsupported orientation', () => {
  const invalid = [...cards];
  invalid[1] = { ...invalid[1], orientation: 'SIDEWAYS' };
  assert.throws(
    () => validateReadingInput({ question: '질문', cards: invalid }),
    (error) => error instanceof ReadingValidationError && error.code === 'INVALID_ORIENTATION',
  );
});

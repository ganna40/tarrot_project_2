import test from 'node:test';
import assert from 'node:assert/strict';

import { normalizeTarotResponse, verdictLabel } from '../docs/assets/response.js';

test('normalizes the v1 rule-engine response', () => {
  const normalized = normalizeTarotResponse({
    verdict: 'CAUTIOUS',
    score: 0.82,
    flow_summary: '종료 후 빠르게 움직여 공식화되는 흐름',
    overall_interpretation: '결과물을 먼저 보여주는 것이 중요합니다.',
    advice: '계약 조건을 문서로 확인하세요.',
    trace: { rules: [1, 2] },
    llm_used: true,
  });
  assert.equal(normalized.verdict, 'CAUTIOUS');
  assert.equal(normalized.score, 0.82);
  assert.equal(normalized.message, '결과물을 먼저 보여주는 것이 중요합니다.');
  assert.deepEqual(normalized.trace, { rules: [1, 2] });
});

test('accepts a basic legacy response without crashing', () => {
  const normalized = normalizeTarotResponse({
    overall_interpretation: '기존 응답',
    advice: '기존 조언',
    cards: [],
  });
  assert.equal(normalized.verdict, 'UNKNOWN');
  assert.equal(normalized.message, '기존 응답');
});

test('provides Korean verdict labels', () => {
  assert.equal(verdictLabel('POSITIVE'), '긍정');
  assert.equal(verdictLabel('NEGATIVE'), '부정');
  assert.equal(verdictLabel('CAUTIOUS'), '신중');
});

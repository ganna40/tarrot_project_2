import test from 'node:test';
import assert from 'node:assert/strict';

import { runDemoConsultation } from '../docs/assets/demo.js';

const goldenPayload = {
  question: '게임을 만들면 투자를 받을 수 있을까?',
  spread_type: 'three_card',
  reading_context: 'BUSINESS',
  cards: [
    { code: 'TEN_OF_SWORDS', orientation: 'UPRIGHT' },
    { code: 'EIGHT_OF_WANDS', orientation: 'UPRIGHT' },
    { code: 'HIEROPHANT', orientation: 'UPRIGHT' },
  ],
  response_length: 'SHORT',
  include_trace: true,
  use_llm: true,
};

test('returns the approved golden flow in local demo mode', async () => {
  const response = await runDemoConsultation(goldenPayload);
  assert.equal(response.verdict, 'POSITIVE');
  assert.match(response.flow_summary, /국면.*빠르게.*계약/);
  assert.equal(response.llm_used, false);
  assert.equal(response.trace.mode, 'LOCAL_DEMO');
});

test('returns an explicit mock response for other valid cards', async () => {
  const payload = {
    ...goldenPayload,
    cards: [
      { code: 'FOOL', orientation: 'UPRIGHT' },
      { code: 'MAGICIAN', orientation: 'UPRIGHT' },
      { code: 'WORLD', orientation: 'UPRIGHT' },
    ],
  };
  const response = await runDemoConsultation(payload);
  assert.equal(response.verdict, 'DEMO');
  assert.match(response.overall_interpretation, /로컬 데모/);
});

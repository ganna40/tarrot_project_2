import test from 'node:test';
import assert from 'node:assert/strict';

import { CARD_BY_CODE, TAROT_CARDS, formatCardLabel, getCard } from '../docs/assets/cards.js';

test('RWS deck contains 78 unique cards', () => {
  assert.equal(TAROT_CARDS.length, 78);
  assert.equal(new Set(TAROT_CARDS.map((card) => card.code)).size, 78);
  assert.equal(CARD_BY_CODE.size, 78);
});

test('well-known cards use stable engine codes', () => {
  assert.equal(getCard('TEN_OF_SWORDS').nameEn, 'Ten of Swords');
  assert.equal(getCard('EIGHT_OF_WANDS').nameKo, '완드 8');
  assert.equal(getCard('HIEROPHANT').arcana, 'MAJOR');
});

test('card labels include Korean and English names', () => {
  assert.equal(formatCardLabel(getCard('HIEROPHANT')), '교황 · The Hierophant');
});

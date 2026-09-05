import test from 'node:test';
import assert from 'node:assert/strict';

import * as cardsModule from '../docs/assets/cards.js';

const { CARD_BY_CODE, TAROT_CARDS, formatCardLabel, getCard } = cardsModule;

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

test('visual draw returns unique cards with supported orientations', () => {
  assert.equal(typeof cardsModule.drawRandomCards, 'function');

  const sequence = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
  let cursor = 0;
  const result = cardsModule.drawRandomCards(3, (max) => sequence[cursor++ % sequence.length] % max);

  assert.equal(result.length, 3);
  assert.equal(new Set(result.map((item) => item.card.code)).size, 3);
  for (const item of result) {
    assert.ok(['UPRIGHT', 'REVERSED'].includes(item.orientation));
  }
});

import { drawRandomCards, groupLabel } from './cards.js';

const SLOT_LABELS = ['시작', '전개', '결과'];
const SUIT_GLYPHS = Object.freeze({
  WANDS: '✦',
  CUPS: '◯',
  SWORDS: '⚔',
  PENTACLES: '⬟',
});

const state = {
  deck: [],
  drawn: [],
  revealTimers: [],
};

const $ = (id) => document.getElementById(id);
const elements = {
  deck: $('tarot-deck'),
  deckStatus: $('deck-status'),
  drawOne: $('draw-one-card'),
  drawThree: $('draw-three-cards'),
  shuffle: $('shuffle-deck'),
  legacyRandomize: $('randomize-cards'),
  slots: [1, 2, 3].map((index) => $(`draw-slot-${index}`)),
};

function clearRevealTimers() {
  state.revealTimers.forEach((timer) => clearTimeout(timer));
  state.revealTimers = [];
}

function faceGlyph(card) {
  if (card.arcana === 'MAJOR') return String(card.number ?? '✧');
  return SUIT_GLYPHS[card.suit] ?? '✦';
}

function orientationLabel(orientation) {
  return orientation === 'REVERSED' ? '역방향' : '정방향';
}

function renderEmptySlot(slot, index) {
  slot.dataset.revealed = 'false';
  slot.dataset.orientation = 'UPRIGHT';
  slot.querySelector('[data-face-arcana]').textContent = 'READY';
  slot.querySelector('[data-face-glyph]').textContent = '✦';
  slot.querySelector('[data-face-name-ko]').textContent = `카드 ${index + 1}`;
  slot.querySelector('[data-face-name-en]').textContent = 'Draw a card';
  slot.querySelector('[data-face-orientation]').textContent = '정방향';
  slot.setAttribute('aria-label', `${SLOT_LABELS[index]} 카드가 아직 선택되지 않았습니다.`);
}

function renderDrawnSlot(slot, item, index, reveal = true) {
  slot.dataset.revealed = reveal ? 'true' : 'false';
  slot.dataset.orientation = item.orientation;
  slot.querySelector('[data-face-arcana]').textContent = groupLabel(item.card);
  slot.querySelector('[data-face-glyph]').textContent = faceGlyph(item.card);
  slot.querySelector('[data-face-name-ko]').textContent = item.card.nameKo;
  slot.querySelector('[data-face-name-en]').textContent = item.card.nameEn;
  slot.querySelector('[data-face-orientation]').textContent = orientationLabel(item.orientation);
  slot.setAttribute(
    'aria-label',
    `${SLOT_LABELS[index]}: ${item.card.nameKo} ${orientationLabel(item.orientation)}`,
  );
}

function updateDeckStatus() {
  const drawnCount = state.drawn.length;
  const remaining = state.deck.length;
  if (!drawnCount) {
    elements.deckStatus.textContent = `덱 ${remaining}장 · 아직 뽑지 않음`;
  } else if (drawnCount < 3) {
    elements.deckStatus.textContent = `덱 ${remaining}장 · ${drawnCount}/3장 선택`;
  } else {
    elements.deckStatus.textContent = `덱 ${remaining}장 · 3장 선택 완료`;
  }
  elements.drawOne.disabled = drawnCount >= 3;
  elements.deck.disabled = drawnCount >= 3;
}

function renderVisualDraw({ reveal = true } = {}) {
  elements.slots.forEach((slot, index) => {
    const item = state.drawn[index];
    if (item) renderDrawnSlot(slot, item, index, reveal);
    else renderEmptySlot(slot, index);
  });
  updateDeckStatus();
}

function revealSlot(index, delay = 0) {
  const slot = elements.slots[index];
  if (!slot || !state.drawn[index]) return;
  const timer = setTimeout(() => {
    slot.dataset.revealed = 'true';
  }, delay);
  state.revealTimers.push(timer);
}

export function syncVisualDrawToSelectors() {
  state.drawn.forEach((item, index) => {
    const cardSelect = $(`card-${index + 1}`);
    const orientationSelect = $(`orientation-${index + 1}`);
    if (!cardSelect || !orientationSelect) return;
    cardSelect.value = item.card.code;
    orientationSelect.value = item.orientation;
    cardSelect.dispatchEvent(new Event('change', { bubbles: true }));
    orientationSelect.dispatchEvent(new Event('change', { bubbles: true }));
  });
}

export function shuffleVisualDeck() {
  clearRevealTimers();
  state.deck = drawRandomCards(78);
  state.drawn = [];
  renderVisualDraw({ reveal: false });
  elements.deck.classList.remove('is-shuffling');
  void elements.deck.offsetWidth;
  elements.deck.classList.add('is-shuffling');
  setTimeout(() => elements.deck.classList.remove('is-shuffling'), 620);
}

export function drawOneVisualCard() {
  if (state.drawn.length >= 3) return;
  if (!state.deck.length) shuffleVisualDeck();

  clearRevealTimers();
  state.drawn.push(state.deck.shift());
  syncVisualDrawToSelectors();
  renderVisualDraw({ reveal: false });
  revealSlot(state.drawn.length - 1, 40);
}

export function drawThreeVisualCards() {
  clearRevealTimers();
  const freshDeck = drawRandomCards(78);
  state.drawn = freshDeck.slice(0, 3);
  state.deck = freshDeck.slice(3);
  syncVisualDrawToSelectors();
  renderVisualDraw({ reveal: false });
  state.drawn.forEach((_, index) => revealSlot(index, 90 + index * 170));
}

function toggleDrawnOrientation(index) {
  const item = state.drawn[index];
  if (!item) return;
  item.orientation = item.orientation === 'REVERSED' ? 'UPRIGHT' : 'REVERSED';
  syncVisualDrawToSelectors();
  renderDrawnSlot(elements.slots[index], item, index, true);
}

function initializeVisualDraw() {
  if (!elements.deck || elements.slots.some((slot) => !slot)) return;

  shuffleVisualDeck();
  elements.deck.addEventListener('click', drawOneVisualCard);
  elements.drawOne.addEventListener('click', drawOneVisualCard);
  elements.drawThree.addEventListener('click', drawThreeVisualCards);
  elements.shuffle.addEventListener('click', shuffleVisualDeck);

  // The existing ↻ button keeps its original exact-test behavior; this listener
  // runs after app.js and makes the final selector state match the visual draw.
  elements.legacyRandomize?.addEventListener('click', drawThreeVisualCards);

  elements.slots.forEach((slot, index) => {
    slot.addEventListener('click', () => toggleDrawnOrientation(index));
  });
}

initializeVisualDraw();

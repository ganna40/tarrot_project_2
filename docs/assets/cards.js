const MAJOR = [
  ['FOOL', '바보', 'The Fool', 0],
  ['MAGICIAN', '마법사', 'The Magician', 1],
  ['HIGH_PRIESTESS', '여사제', 'The High Priestess', 2],
  ['EMPRESS', '여제', 'The Empress', 3],
  ['EMPEROR', '황제', 'The Emperor', 4],
  ['HIEROPHANT', '교황', 'The Hierophant', 5],
  ['LOVERS', '연인', 'The Lovers', 6],
  ['CHARIOT', '전차', 'The Chariot', 7],
  ['STRENGTH', '힘', 'Strength', 8],
  ['HERMIT', '은둔자', 'The Hermit', 9],
  ['WHEEL_OF_FORTUNE', '운명의 수레바퀴', 'Wheel of Fortune', 10],
  ['JUSTICE', '정의', 'Justice', 11],
  ['HANGED_MAN', '매달린 사람', 'The Hanged Man', 12],
  ['DEATH', '죽음', 'Death', 13],
  ['TEMPERANCE', '절제', 'Temperance', 14],
  ['DEVIL', '악마', 'The Devil', 15],
  ['TOWER', '탑', 'The Tower', 16],
  ['STAR', '별', 'The Star', 17],
  ['MOON', '달', 'The Moon', 18],
  ['SUN', '태양', 'The Sun', 19],
  ['JUDGEMENT', '심판', 'Judgement', 20],
  ['WORLD', '세계', 'The World', 21],
];

const SUITS = [
  ['WANDS', '완드', 'Wands'],
  ['CUPS', '컵', 'Cups'],
  ['SWORDS', '소드', 'Swords'],
  ['PENTACLES', '펜타클', 'Pentacles'],
];

const RANKS = [
  ['ACE', '에이스', 'Ace', 1],
  ['TWO', '2', 'Two', 2],
  ['THREE', '3', 'Three', 3],
  ['FOUR', '4', 'Four', 4],
  ['FIVE', '5', 'Five', 5],
  ['SIX', '6', 'Six', 6],
  ['SEVEN', '7', 'Seven', 7],
  ['EIGHT', '8', 'Eight', 8],
  ['NINE', '9', 'Nine', 9],
  ['TEN', '10', 'Ten', 10],
  ['PAGE', '시종', 'Page', null],
  ['KNIGHT', '기사', 'Knight', null],
  ['QUEEN', '여왕', 'Queen', null],
  ['KING', '왕', 'King', null],
];

const majorCards = MAJOR.map(([code, nameKo, nameEn, number], index) => Object.freeze({
  code,
  nameKo,
  nameEn,
  arcana: 'MAJOR',
  suit: null,
  rank: null,
  number,
  sortOrder: index,
}));

const minorCards = SUITS.flatMap(([suit, suitKo, suitEn], suitIndex) =>
  RANKS.map(([rank, rankKo, rankEn, number], rankIndex) => Object.freeze({
    code: `${rank}_OF_${suit}`,
    nameKo: `${suitKo} ${rankKo}`,
    nameEn: `${rankEn} of ${suitEn}`,
    arcana: 'MINOR',
    suit,
    rank,
    number,
    sortOrder: 22 + suitIndex * RANKS.length + rankIndex,
  })),
);

export const TAROT_CARDS = Object.freeze([...majorCards, ...minorCards]);
export const CARD_BY_CODE = new Map(TAROT_CARDS.map((card) => [card.code, card]));

function defaultRandomIndex(max) {
  if (!Number.isInteger(max) || max <= 0) throw new RangeError('max must be a positive integer');
  if (globalThis.crypto?.getRandomValues) {
    const value = new Uint32Array(1);
    globalThis.crypto.getRandomValues(value);
    return value[0] % max;
  }
  return Math.floor(Math.random() * max);
}

export function getCard(code) {
  const card = CARD_BY_CODE.get(code);
  if (!card) {
    throw new Error(`Unknown tarot card code: ${code}`);
  }
  return card;
}

export function formatCardLabel(card) {
  return `${card.nameKo} · ${card.nameEn}`;
}

export function groupLabel(card) {
  if (card.arcana === 'MAJOR') return '메이저 아르카나';
  return {
    WANDS: '마이너 · 완드',
    CUPS: '마이너 · 컵',
    SWORDS: '마이너 · 소드',
    PENTACLES: '마이너 · 펜타클',
  }[card.suit];
}

export function drawRandomCards(count = 3, randomIndex = defaultRandomIndex) {
  if (!Number.isInteger(count) || count < 1 || count > TAROT_CARDS.length) {
    throw new RangeError(`count must be between 1 and ${TAROT_CARDS.length}`);
  }

  const pool = [...TAROT_CARDS];
  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = randomIndex(i + 1);
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }

  return pool.slice(0, count).map((card) => ({
    card,
    orientation: randomIndex(10) < 3 ? 'REVERSED' : 'UPRIGHT',
  }));
}

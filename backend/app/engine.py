from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from app.schemas import (
    CardInput,
    InterpretationPlan,
    ReadingContext,
    ResolvedCard,
    Transition,
    Verdict,
)


_CONTEXT_KEYWORDS: dict[ReadingContext, tuple[str, ...]] = {
    ReadingContext.BUSINESS: ("사업", "창업", "투자", "계약", "매출", "법인", "고객", "사업비"),
    ReadingContext.CAREER: ("취업", "이직", "승진", "직장", "회사", "면접", "퇴사", "커리어"),
    ReadingContext.LOVE: ("연애", "재회", "상대방", "결혼", "썸", "이별", "사랑"),
    ReadingContext.MONEY: ("돈", "대출", "지출", "수입", "재정", "금전", "빚", "저축"),
    ReadingContext.TIMING: ("언제", "시기", "이번 달", "이번주", "올해", "내년", "며칠"),
}


def classify_context(question: str, additional_context: str | None = None) -> ReadingContext:
    text = f"{question} {additional_context or ''}".lower()
    scores: Counter[ReadingContext] = Counter()
    for context, keywords in _CONTEXT_KEYWORDS.items():
        scores[context] = sum(text.count(keyword.lower()) for keyword in keywords)

    if not scores or max(scores.values(), default=0) == 0:
        return ReadingContext.GENERAL

    top_score = max(scores.values())
    winners = [context for context, score in scores.items() if score == top_score]
    return winners[0] if len(winners) == 1 else ReadingContext.GENERAL


def validate_card_inputs(cards: Sequence[CardInput]) -> None:
    if len(cards) != 3:
        raise ValueError("v1 해석에는 정확히 3장의 카드가 필요합니다")
    codes = [card.code for card in cards]
    if len(set(codes)) != len(codes):
        raise ValueError("중복 카드는 사용할 수 없습니다")


def _verdict_for_score(score: float) -> Verdict:
    if score >= 1.25:
        return Verdict.POSITIVE
    if score <= -1.25:
        return Verdict.NEGATIVE
    return Verdict.CAUTIOUS


def _flow_summary(cards: Sequence[ResolvedCard], transitions: Sequence[Transition]) -> str:
    if transitions:
        texts = [transition.transition_text.rstrip(".。 ") for transition in transitions]
        if len(texts) == 1:
            return f"{texts[0]}."
        return f"{texts[0]}. 이어서 {texts[1]}."

    tags = " → ".join(card.primary_tag for card in cards)
    return f"{tags} 순서로 국면이 전개되는 흐름"


def calculate_reading(
    question: str,
    reading_context: ReadingContext,
    cards: Sequence[ResolvedCard],
    transitions: Sequence[Transition],
    elemental_modifier: float,
) -> InterpretationPlan:
    if len(cards) != 3:
        raise ValueError("v1 해석에는 정확히 3장의 카드가 필요합니다")

    weighted_total = sum(card.polarity * card.position_weight for card in cards)
    total_weight = sum(card.position_weight for card in cards)
    if total_weight <= 0:
        raise ValueError("스프레드 위치 가중치 합계는 0보다 커야 합니다")
    base_score = weighted_total / total_weight
    relation_score = sum(transition.score_delta for transition in transitions)
    final_score = max(-5.0, min(5.0, base_score + relation_score + elemental_modifier))
    final_score = round(final_score, 2)

    flow_tags = [cards[0].primary_tag]
    flow_tags.extend(transition.to_tag for transition in transitions)
    if len(flow_tags) < 3:
        flow_tags = [card.primary_tag for card in cards]

    advice_constraints: list[str] = []
    for card in cards:
        if card.advice and card.advice not in advice_constraints:
            advice_constraints.append(card.advice)

    return InterpretationPlan(
        question=question,
        reading_context=reading_context,
        cards=list(cards),
        transitions=list(transitions),
        elemental_modifier=round(elemental_modifier, 2),
        score=final_score,
        verdict=_verdict_for_score(final_score),
        flow_tags=flow_tags,
        flow_summary=_flow_summary(cards, transitions),
        advice_constraints=advice_constraints,
    )

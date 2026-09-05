from __future__ import annotations

from app.schemas import InterpretationPlan, ResponseLength, Verdict


_VERDICT_OPENERS = {
    Verdict.POSITIVE: "전체적으로 긍정적인 가능성이 더 강합니다.",
    Verdict.CAUTIOUS: "가능성은 있지만 조건을 확인하며 신중하게 움직여야 합니다.",
    Verdict.NEGATIVE: "현재 흐름에서는 무리하게 밀어붙이기보다 위험을 줄이는 편이 좋습니다.",
}


def build_fallback_interpretation(
    plan: InterpretationPlan,
    response_length: ResponseLength,
) -> str:
    """Create a deterministic response when LLM use is disabled or unavailable."""
    opener = _VERDICT_OPENERS[plan.verdict]
    core = f"카드의 연결 흐름은 다음과 같습니다. {plan.flow_summary}"

    if response_length == ResponseLength.SHORT:
        return f"{opener} {core}"

    meanings = " ".join(card.meaning.rstrip(".。 ") + "." for card in plan.cards)
    if response_length == ResponseLength.NORMAL:
        return f"{opener} {core} {meanings}"

    transitions = " ".join(
        transition.transition_text.rstrip(".。 ") + "." for transition in plan.transitions
    )
    return f"{opener} {core} {meanings} {transitions}".strip()


def build_advice(plan: InterpretationPlan) -> str:
    if not plan.advice_constraints:
        return "결론을 확정하기 전에 실제 조건과 선택 가능한 행동을 확인하세요."
    return " ".join(plan.advice_constraints[:2])

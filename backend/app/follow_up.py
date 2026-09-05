from __future__ import annotations

from app.schemas import InterpretationPlan, ReadingContext, Verdict


def _subject(plan: InterpretationPlan) -> str:
    question = plan.question
    if plan.reading_context == ReadingContext.BUSINESS:
        if "투자" in question:
            return "투자"
        if "사업" in question:
            return "사업"
        return "사업 흐름"
    return {
        ReadingContext.GENERAL: "현재 흐름",
        ReadingContext.LOVE: "관계",
        ReadingContext.CAREER: "직장·커리어",
        ReadingContext.MONEY: "금전 흐름",
        ReadingContext.TIMING: "현재 상황",
    }[plan.reading_context]


def build_follow_up_questions(plan: InterpretationPlan) -> list[str]:
    """Build exactly three deterministic continuation questions.

    Follow-ups are derived only from the resolved reading context, verdict and
    flow tags. They never change the original verdict and do not use an LLM.
    """

    subject = _subject(plan)
    tags = set(plan.flow_tags)

    if plan.verdict == Verdict.POSITIVE:
        action = f"{subject} 흐름을 실제 기회로 연결하려면 지금 가장 먼저 무엇을 해야 할까?"
    elif plan.verdict == Verdict.NEGATIVE:
        action = f"{subject} 흐름을 바꾸기 위해 지금 가장 먼저 정리하거나 멈춰야 할 것은 무엇일까?"
    else:
        action = f"{subject}에서 성급하게 움직이지 않으면서 지금 가장 먼저 확인해야 할 것은 무엇일까?"

    if "ENDING" in tags:
        obstacle = "이 흐름에서 먼저 끝내거나 정리해야 할 가장 큰 변수는 무엇일까?"
    elif tags.intersection({"CONFLICT", "BLOCKAGE", "RESTRICTION", "LOSS", "FEAR"}):
        obstacle = f"{subject}을 막는 가장 큰 걸림돌이나 변수는 무엇일까?"
    else:
        obstacle = f"{subject}이 원하는 방향으로 가지 못하게 할 가장 큰 변수나 걸림돌은 무엇일까?"

    if "FORMALIZATION" in tags:
        next_step = f"{subject}이 실제 계약이나 공식적인 단계로 구체화되려면 무엇이 필요할까?"
    elif plan.reading_context == ReadingContext.TIMING or tags.intersection({"MOVEMENT", "SPEED", "DELAY", "WAITING"}):
        next_step = "이 흐름이 실제 변화로 드러나는 시기는 언제쯤일까?"
    else:
        next_step = f"{subject}이 다음 단계로 넘어갈 때 가장 먼저 나타날 신호는 무엇일까?"

    return [action, obstacle, next_step]

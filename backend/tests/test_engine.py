import pytest
from pydantic import ValidationError

from app.engine import calculate_reading, classify_context, validate_card_inputs
from app.schemas import (
    CardInput,
    Orientation,
    ReadingContext,
    ResolvedCard,
    Transition,
    Verdict,
)


def card(
    code: str,
    tag: str,
    polarity: float,
    *,
    action: float = 2,
    speed: float = 2,
    element: str | None = None,
    position_weight: float = 1.0,
) -> ResolvedCard:
    return ResolvedCard(
        code=code,
        name_ko=code,
        name_en=code,
        orientation=Orientation.UPRIGHT,
        position_order=1,
        position_label="",
        position_weight=position_weight,
        meaning="테스트 의미",
        advice="테스트 조언",
        warning=None,
        polarity=polarity,
        action_level=action,
        speed_level=speed,
        stability_level=2,
        ending_level=2,
        primary_tag=tag,
        tags=[tag],
        element=element,
        source_code="TEST",
        page_start=1,
        page_end=1,
    )


@pytest.mark.parametrize(
    ("question", "additional", "expected"),
    [
        ("게임을 만들면 투자를 받을까?", None, ReadingContext.BUSINESS),
        ("이번에 이직할 수 있을까?", None, ReadingContext.CAREER),
        ("그 사람과 재회할까?", None, ReadingContext.LOVE),
        ("대출을 먼저 갚는 게 좋을까?", None, ReadingContext.MONEY),
        ("언제 연락이 올까?", None, ReadingContext.TIMING),
        ("오늘의 흐름은?", None, ReadingContext.GENERAL),
        ("결과는 어떨까?", "창업과 계약 이야기", ReadingContext.BUSINESS),
    ],
)
def test_classify_context(question, additional, expected):
    assert classify_context(question, additional) == expected


def test_known_business_flow_is_calculated_before_language_generation():
    cards = [
        card("TEN_OF_SWORDS", "ENDING", -4, action=1, speed=1, element="AIR"),
        card("EIGHT_OF_WANDS", "MOVEMENT", 2, action=5, speed=5, element="FIRE"),
        card("HIEROPHANT", "FORMALIZATION", 1, action=2, speed=2, element="EARTH"),
    ]
    transitions = [
        Transition(
            from_card="TEN_OF_SWORDS",
            to_card="EIGHT_OF_WANDS",
            from_tag="ENDING",
            to_tag="MOVEMENT",
            relation_type="ACCELERATE",
            transition_text="기존 국면이 끝난 뒤 상황이 빠르게 움직이기 시작한다",
            score_delta=0.6,
            rule_id=1,
        ),
        Transition(
            from_card="EIGHT_OF_WANDS",
            to_card="HIEROPHANT",
            from_tag="MOVEMENT",
            to_tag="FORMALIZATION",
            relation_type="FORMALIZE",
            transition_text="빠른 움직임이 공식적인 구조로 이어진다",
            score_delta=0.4,
            rule_id=2,
        ),
    ]

    plan = calculate_reading(
        question="게임을 만들면 투자를 받을 수 있을까?",
        reading_context=ReadingContext.BUSINESS,
        cards=cards,
        transitions=transitions,
        elemental_modifier=0.0,
    )

    assert plan.verdict == Verdict.CAUTIOUS
    assert plan.flow_tags == ["ENDING", "MOVEMENT", "FORMALIZATION"]
    assert "빠르게" in plan.flow_summary
    assert "공식적인 구조" in plan.flow_summary
    assert "시작한다고" not in plan.flow_summary
    assert plan.flow_summary.endswith("이어진다.")
    assert -1.25 < plan.score < 1.25



def test_score_uses_position_weights_from_resolved_spread_data():
    cards = [
        card("A", "SUCCESS", 5, position_weight=10),
        card("B", "LOSS", -5, position_weight=1),
        card("C", "LOSS", -5, position_weight=1),
    ]

    plan = calculate_reading("질문", ReadingContext.GENERAL, cards, [], 0)

    assert plan.verdict == Verdict.POSITIVE
    assert plan.score == 3.33


def test_positive_and_negative_score_boundaries_are_deterministic():
    positive = [card("A", "SUCCESS", 2), card("B", "SUCCESS", 2), card("C", "SUCCESS", 2)]
    negative = [card("D", "LOSS", -2), card("E", "LOSS", -2), card("F", "LOSS", -2)]

    positive_plan = calculate_reading("질문", ReadingContext.GENERAL, positive, [], 0)
    negative_plan = calculate_reading("질문", ReadingContext.GENERAL, negative, [], 0)

    assert positive_plan.verdict == Verdict.POSITIVE
    assert negative_plan.verdict == Verdict.NEGATIVE


def test_validate_card_inputs_rejects_duplicate_cards():
    with pytest.raises(ValueError, match="중복"):
        validate_card_inputs(
            [
                CardInput(code="TEN_OF_SWORDS", orientation=Orientation.UPRIGHT),
                CardInput(code="TEN_OF_SWORDS", orientation=Orientation.REVERSED),
                CardInput(code="HIEROPHANT", orientation=Orientation.UPRIGHT),
            ]
        )


def test_validate_card_inputs_requires_exactly_three_cards():
    with pytest.raises(ValueError, match="정확히 3장"):
        validate_card_inputs([CardInput(code="HIEROPHANT", orientation=Orientation.UPRIGHT)])

@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("FIRE", "AIR", 0.25),
        ("FIRE", "EARTH", 0.25),
        ("AIR", "WATER", 0.25),
        ("FIRE", "WATER", -0.25),
        ("AIR", "EARTH", -0.25),
        ("WATER", "EARTH", 0.0),
        ("WATER", "WATER", 0.15),
    ],
)
def test_elemental_dignity_uses_book_t_friendly_hostile_and_neutral_pairs(left, right, expected):
    from app.repository import TarotRepository

    cards = [card("LEFT", "TEST", 0, element=left), card("RIGHT", "TEST", 0, element=right)]
    assert TarotRepository.elemental_modifier(cards) == expected

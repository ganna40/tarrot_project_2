from __future__ import annotations

import random

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import (
    CardCorrespondence,
    CardMeaning,
    CardMeaningTag,
    InterpretationTag,
    RelationRule,
    Source,
    SpreadPosition,
    TarotCard,
)
from app.schemas import CardInput, Orientation, ReadingContext, ResolvedCard, Transition


class KnowledgeNotReadyError(RuntimeError):
    pass


class TarotRepository:
    def __init__(self, session: Session):
        self.session = session

    def count_cards(self) -> int:
        return int(self.session.scalar(select(func.count(TarotCard.id))) or 0)

    def draw_supported_cards(self, count: int = 3) -> list[CardInput]:
        statement = (
            select(TarotCard.code)
            .join(CardMeaning, CardMeaning.card_id == TarotCard.id)
            .where(
                TarotCard.is_active.is_(True),
                CardMeaning.review_status == "APPROVED",
                CardMeaning.is_active.is_(True),
                CardMeaning.context == ReadingContext.GENERAL.value,
                CardMeaning.orientation == Orientation.UPRIGHT.value,
            )
            .distinct()
        )
        codes = list(self.session.scalars(statement).all())
        if len(codes) < count:
            raise KnowledgeNotReadyError("무작위 추첨에 필요한 승인 카드 의미가 부족합니다")
        return [CardInput(code=code, orientation=Orientation.UPRIGHT) for code in random.sample(codes, count)]

    def resolve_cards(
        self,
        card_inputs: list[CardInput],
        context: ReadingContext,
    ) -> list[ResolvedCard]:
        positions = list(
            self.session.scalars(
                select(SpreadPosition)
                .where(SpreadPosition.spread_code == "THREE_FLOW")
                .order_by(SpreadPosition.position_order)
            ).all()
        )
        if len(positions) != 3:
            raise KnowledgeNotReadyError("THREE_FLOW 스프레드 위치 데이터가 준비되지 않았습니다")

        resolved: list[ResolvedCard] = []
        for index, card_input in enumerate(card_inputs):
            card = self.session.scalar(
                select(TarotCard).where(TarotCard.code == card_input.code, TarotCard.is_active.is_(True))
            )
            if card is None:
                raise KnowledgeNotReadyError(f"카드 식별자를 찾을 수 없습니다: {card_input.code}")

            context_order = case((CardMeaning.context == context.value, 0), else_=1)
            meaning_statement = (
                select(CardMeaning, Source)
                .join(Source, Source.id == CardMeaning.source_id)
                .where(
                    CardMeaning.card_id == card.id,
                    CardMeaning.orientation == card_input.orientation.value,
                    CardMeaning.context.in_([context.value, ReadingContext.GENERAL.value]),
                    CardMeaning.review_status == "APPROVED",
                    CardMeaning.is_active.is_(True),
                    Source.is_active.is_(True),
                )
                .order_by(context_order, Source.priority, CardMeaning.priority, CardMeaning.id)
                .limit(1)
            )
            result = self.session.execute(meaning_statement).first()
            if result is None:
                raise KnowledgeNotReadyError(
                    f"승인된 카드 의미가 준비되지 않았습니다: {card.code}/{card_input.orientation.value}/{context.value}"
                )
            meaning, source = result

            tag_rows = self.session.execute(
                select(InterpretationTag, CardMeaningTag)
                .join(CardMeaningTag, CardMeaningTag.tag_id == InterpretationTag.id)
                .where(CardMeaningTag.card_meaning_id == meaning.id)
                .order_by(CardMeaningTag.is_primary.desc(), CardMeaningTag.weight.desc(), InterpretationTag.code)
            ).all()
            if not tag_rows:
                raise KnowledgeNotReadyError(f"승인된 해석 태그가 없습니다: {card.code}")
            tags = [tag.code for tag, _link in tag_rows]
            primary = next((tag.code for tag, link in tag_rows if link.is_primary), tags[0])

            element = self.session.scalar(
                select(CardCorrespondence.value)
                .where(
                    CardCorrespondence.card_id == card.id,
                    CardCorrespondence.correspondence_type == "ELEMENT",
                    CardCorrespondence.review_status == "APPROVED",
                    CardCorrespondence.is_active.is_(True),
                )
                .order_by(CardCorrespondence.priority, CardCorrespondence.id)
                .limit(1)
            )

            position = positions[index]
            resolved.append(
                ResolvedCard(
                    code=card.code,
                    name_ko=card.name_ko,
                    name_en=card.name_en,
                    orientation=card_input.orientation,
                    position_order=position.position_order,
                    position_label=position.label_ko,
                    meaning=meaning.meaning_text,
                    advice=meaning.advice_text,
                    warning=meaning.warning_text,
                    polarity=meaning.polarity,
                    action_level=meaning.action_level,
                    speed_level=meaning.speed_level,
                    stability_level=meaning.stability_level,
                    ending_level=meaning.ending_level,
                    primary_tag=primary,
                    tags=tags,
                    element=element,
                    source_code=source.code,
                    page_start=meaning.page_start,
                    page_end=meaning.page_end,
                )
            )
        return resolved

    def resolve_transitions(
        self,
        cards: list[ResolvedCard],
        context: ReadingContext,
    ) -> list[Transition]:
        from_tag = aliased(InterpretationTag)
        to_tag = aliased(InterpretationTag)
        transitions: list[Transition] = []

        for left, right in zip(cards, cards[1:]):
            context_order = case((RelationRule.context == context.value, 0), else_=1)
            statement = (
                select(RelationRule)
                .join(from_tag, from_tag.id == RelationRule.from_tag_id)
                .join(to_tag, to_tag.id == RelationRule.to_tag_id)
                .where(
                    from_tag.code == left.primary_tag,
                    to_tag.code == right.primary_tag,
                    or_(RelationRule.context == context.value, RelationRule.context.is_(None)),
                    RelationRule.review_status == "APPROVED",
                    RelationRule.is_active.is_(True),
                )
                .order_by(context_order, RelationRule.priority, RelationRule.id)
                .limit(1)
            )
            rule = self.session.scalar(statement)
            if rule is not None:
                transitions.append(
                    Transition(
                        from_card=left.code,
                        to_card=right.code,
                        from_tag=left.primary_tag,
                        to_tag=right.primary_tag,
                        relation_type=rule.relation_type,
                        transition_text=rule.transition_text,
                        score_delta=rule.score_delta,
                        rule_id=rule.id,
                    )
                )
            else:
                transitions.append(self._generic_transition(left, right))
        return transitions

    @staticmethod
    def _generic_transition(left: ResolvedCard, right: ResolvedCard) -> Transition:
        if left.primary_tag == right.primary_tag:
            relation_type = "CONTINUE"
            text = f"{left.primary_tag}의 흐름이 다음 단계에서도 이어진다"
        elif right.polarity - left.polarity >= 1.5:
            relation_type = "IMPROVE"
            text = "앞선 부담보다 다음 단계의 가능성이 커진다"
        elif left.polarity - right.polarity >= 1.5:
            relation_type = "DECLINE"
            text = "앞선 흐름보다 다음 단계의 부담이 커진다"
        elif right.speed_level + right.action_level > left.speed_level + left.action_level + 1:
            relation_type = "ACCELERATE"
            text = "정체된 흐름이 행동과 진행으로 바뀐다"
        elif left.speed_level + left.action_level > right.speed_level + right.action_level + 1:
            relation_type = "SLOW_DOWN"
            text = "빠르던 흐름이 점검과 조정 단계로 느려진다"
        else:
            relation_type = "TRANSITION"
            text = f"{left.primary_tag}에서 {right.primary_tag}로 국면이 전환된다"

        return Transition(
            from_card=left.code,
            to_card=right.code,
            from_tag=left.primary_tag,
            to_tag=right.primary_tag,
            relation_type=relation_type,
            transition_text=text,
            score_delta=0.0,
            rule_id=None,
        )

    @staticmethod
    def elemental_modifier(cards: list[ResolvedCard]) -> float:
        supportive = {frozenset(("FIRE", "AIR")), frozenset(("WATER", "EARTH"))}
        tense = {frozenset(("FIRE", "WATER")), frozenset(("AIR", "EARTH"))}
        modifier = 0.0
        for left, right in zip(cards, cards[1:]):
            if not left.element or not right.element:
                continue
            pair = frozenset((left.element, right.element))
            if left.element == right.element:
                modifier += 0.15
            elif pair in supportive:
                modifier += 0.25
            elif pair in tense:
                modifier -= 0.25
        return round(max(-0.5, min(0.5, modifier)), 2)

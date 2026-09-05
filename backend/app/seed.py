from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

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


MAJOR_CARDS = [
    ("FOOL", "바보", "The Fool"),
    ("MAGICIAN", "마법사", "The Magician"),
    ("HIGH_PRIESTESS", "여사제", "The High Priestess"),
    ("EMPRESS", "여황제", "The Empress"),
    ("EMPEROR", "황제", "The Emperor"),
    ("HIEROPHANT", "교황", "The Hierophant"),
    ("LOVERS", "연인", "The Lovers"),
    ("CHARIOT", "전차", "The Chariot"),
    ("STRENGTH", "힘", "Strength"),
    ("HERMIT", "은둔자", "The Hermit"),
    ("WHEEL_OF_FORTUNE", "운명의 수레바퀴", "Wheel of Fortune"),
    ("JUSTICE", "정의", "Justice"),
    ("HANGED_MAN", "매달린 사람", "The Hanged Man"),
    ("DEATH", "죽음", "Death"),
    ("TEMPERANCE", "절제", "Temperance"),
    ("DEVIL", "악마", "The Devil"),
    ("TOWER", "탑", "The Tower"),
    ("STAR", "별", "The Star"),
    ("MOON", "달", "The Moon"),
    ("SUN", "태양", "The Sun"),
    ("JUDGEMENT", "심판", "Judgement"),
    ("WORLD", "세계", "The World"),
]

SUITS = {
    "WANDS": "완드",
    "CUPS": "컵",
    "SWORDS": "소드",
    "PENTACLES": "펜타클",
}

RANKS = [
    ("ACE", "에이스", "Ace", 1),
    ("TWO", "2", "Two", 2),
    ("THREE", "3", "Three", 3),
    ("FOUR", "4", "Four", 4),
    ("FIVE", "5", "Five", 5),
    ("SIX", "6", "Six", 6),
    ("SEVEN", "7", "Seven", 7),
    ("EIGHT", "8", "Eight", 8),
    ("NINE", "9", "Nine", 9),
    ("TEN", "10", "Ten", 10),
    ("PAGE", "페이지", "Page", None),
    ("KNIGHT", "나이트", "Knight", None),
    ("QUEEN", "퀸", "Queen", None),
    ("KING", "킹", "King", None),
]

TAG_DEFINITIONS = {
    "ENDING": ("종료", "기존 국면이나 방식의 끝"),
    "LOSS": ("손실", "잃음 또는 소진"),
    "RECOVERY": ("회복", "손실 이후 회복"),
    "MOVEMENT": ("진행", "움직임과 전개"),
    "DELAY": ("지연", "진행 속도의 저하"),
    "FORMALIZATION": ("공식화", "계약·제도·절차로 구조화"),
    "NONCONFORMITY": ("비정형", "기존 규범에서 벗어남"),
    "SUCCESS": ("성공", "성과와 인정"),
    "SETBACK": ("후퇴", "성과의 지연이나 인정 부족"),
    "RESTRICTION": ("제약", "현실적 또는 심리적 제한"),
    "RELEASE": ("해방", "제약에서 벗어남"),
    "PAUSE": ("멈춤", "관점 전환을 위한 정지"),
    "STAGNATION": ("정체", "필요 이상으로 멈춤"),
    "CHANGE": ("변화", "근본적 전환"),
    "RESISTANCE": ("저항", "필요한 변화에 대한 거부"),
    "BEGINNING": ("시작", "새로운 동력과 출발"),
    "DISRUPTION": ("붕괴", "갑작스러운 구조 변화"),
    "AFTERSHOCK": ("여파", "충격 이후 남은 불안정"),
    "HOPE": ("희망", "회복 가능성과 방향"),
    "DISCOURAGEMENT": ("낙담", "희망과 자신감의 약화"),
}

# 이 값들은 구조 검증을 위한 INTERNAL_DEMO 편집 데이터다. 원전 추출 데이터가 아니다.
DEMO_MEANINGS = [
    ("TEN_OF_SWORDS", "UPRIGHT", "GENERAL", "기존 방식이 한계에 도달해 정리와 종료가 필요한 단계", "더 이어가기보다 끝낼 것과 남길 것을 구분하세요.", "손실을 만회하려고 같은 방식을 반복하지 마세요.", -4, 1, 1, 0, 5, [("ENDING", 1.0, True), ("LOSS", 0.8, False)]),
    ("TEN_OF_SWORDS", "REVERSED", "GENERAL", "최악의 국면을 지나 회복의 여지가 생기기 시작하는 단계", "작은 회복 신호를 확인하고 재발 원인을 정리하세요.", None, -1, 2, 2, 1, 3, [("RECOVERY", 1.0, True), ("ENDING", 0.5, False)]),
    ("EIGHT_OF_WANDS", "UPRIGHT", "GENERAL", "정체가 풀리며 소식과 행동이 빠르게 이어지는 단계", "결정이 필요한 항목을 미리 정리하세요.", "속도 때문에 조건 검토를 생략하지 마세요.", 3, 5, 5, 2, 0, [("MOVEMENT", 1.0, True)]),
    ("EIGHT_OF_WANDS", "UPRIGHT", "BUSINESS", "사업 관련 연락과 실행이 예상보다 빠르게 이어지는 단계", "제안 자료와 의사결정 조건을 바로 제시할 수 있게 준비하세요.", "구두 합의만 믿고 진행하지 마세요.", 2, 5, 5, 2, 0, [("MOVEMENT", 1.0, True)]),
    ("EIGHT_OF_WANDS", "REVERSED", "GENERAL", "연락과 진행이 엇갈리며 일정이 늦어지는 단계", "일정과 전달 경로를 다시 확인하세요.", None, -1, 2, 1, 1, 0, [("DELAY", 1.0, True)]),
    ("HIEROPHANT", "UPRIGHT", "GENERAL", "개인적 약속이 규칙·계약·공식 절차로 정리되는 단계", "역할과 조건을 문서로 명확히 하세요.", "권위자의 말만 따르지 말고 계약 내용을 확인하세요.", 1, 2, 2, 4, 0, [("FORMALIZATION", 1.0, True)]),
    ("HIEROPHANT", "REVERSED", "GENERAL", "기존 규칙이나 관행이 현재 상황과 맞지 않아 다른 방식이 필요한 단계", "필수 규칙과 바꿀 수 있는 관행을 구분하세요.", None, -1, 3, 2, 1, 0, [("NONCONFORMITY", 1.0, True)]),
    ("SIX_OF_WANDS", "UPRIGHT", "GENERAL", "성과가 드러나고 주변의 인정이나 지지를 얻는 단계", "성과를 구체적인 결과물로 보여주세요.", None, 4, 4, 3, 3, 0, [("SUCCESS", 1.0, True)]),
    ("SIX_OF_WANDS", "REVERSED", "GENERAL", "성과가 있어도 인정이나 확신이 부족해지는 단계", "평가 기준과 실제 성과를 분리해 확인하세요.", None, -1, 2, 2, 1, 0, [("SETBACK", 1.0, True)]),
    ("EIGHT_OF_SWORDS", "UPRIGHT", "GENERAL", "선택지가 없다고 느끼지만 일부 제약은 두려움과 고정관념에서 생긴 단계", "바꿀 수 있는 조건과 바꿀 수 없는 조건을 나누세요.", "불안을 현실의 절대적 한계로 단정하지 마세요.", -3, 1, 1, 1, 1, [("RESTRICTION", 1.0, True)]),
    ("EIGHT_OF_SWORDS", "REVERSED", "GENERAL", "제약의 실체를 파악하며 벗어날 선택지가 보이기 시작하는 단계", "작게라도 통제 가능한 행동부터 시작하세요.", None, 2, 3, 3, 2, 0, [("RELEASE", 1.0, True)]),
    ("HANGED_MAN", "UPRIGHT", "GENERAL", "즉시 결론을 내리기보다 관점을 바꾸고 멈춰 살피는 단계", "지금 보류해야 할 이유와 얻을 정보를 정하세요.", "무기한 미루는 상태가 되지 않게 기한을 두세요.", 0, 0, 0, 2, 1, [("PAUSE", 1.0, True)]),
    ("HANGED_MAN", "REVERSED", "GENERAL", "기다림이 통찰로 이어지지 않고 정체로 굳어지는 단계", "결정을 미루는 실제 이유를 적어보세요.", None, -2, 0, 0, 0, 1, [("STAGNATION", 1.0, True)]),
    ("DEATH", "UPRIGHT", "GENERAL", "기존 국면을 끝내고 근본적으로 다른 단계로 넘어가는 전환", "끝내야 새로 시작할 수 있는 부분을 정리하세요.", None, 0, 2, 2, 1, 5, [("CHANGE", 1.0, True), ("ENDING", 0.8, False)]),
    ("DEATH", "REVERSED", "GENERAL", "필요한 변화를 알면서도 익숙한 상태를 놓지 못하는 단계", "변화를 막고 있는 이해관계부터 확인하세요.", None, -2, 1, 0, 1, 3, [("RESISTANCE", 1.0, True)]),
    ("ACE_OF_WANDS", "UPRIGHT", "GENERAL", "새로운 시도에 필요한 의욕과 실행 동력이 생기는 단계", "작은 첫 결과물을 빠르게 만드세요.", None, 4, 5, 4, 2, 0, [("BEGINNING", 1.0, True)]),
    ("ACE_OF_WANDS", "REVERSED", "GENERAL", "시작할 의지는 있지만 방향과 실행력이 분산되는 단계", "범위를 줄이고 첫 행동을 하나만 정하세요.", None, -1, 1, 1, 1, 0, [("DELAY", 1.0, True)]),
    ("TOWER", "UPRIGHT", "GENERAL", "기존 구조의 약점이 드러나며 급격한 재정비가 필요한 단계", "무너진 가정과 실제로 남은 자원을 분리하세요.", "충격 속에서 성급한 추가 결정을 하지 마세요.", -4, 4, 5, 0, 4, [("DISRUPTION", 1.0, True)]),
    ("TOWER", "REVERSED", "GENERAL", "큰 충격을 피했어도 불안정한 여파가 남아 있는 단계", "근본 원인이 해결됐는지 다시 확인하세요.", None, -2, 2, 2, 1, 2, [("AFTERSHOCK", 1.0, True)]),
    ("STAR", "UPRIGHT", "GENERAL", "혼란 뒤에 회복 방향과 현실적인 희망이 다시 보이는 단계", "지속 가능한 회복 행동을 하나 정하세요.", None, 4, 3, 2, 4, 0, [("HOPE", 1.0, True), ("RECOVERY", 0.8, False)]),
    ("STAR", "REVERSED", "GENERAL", "가능성이 남아 있지만 자신감과 기대가 약해진 단계", "결과보다 회복 과정의 작은 증거를 확인하세요.", None, -2, 1, 1, 1, 0, [("DISCOURAGEMENT", 1.0, True)]),
]

ELEMENTS = {
    "TEN_OF_SWORDS": "AIR",
    "EIGHT_OF_WANDS": "FIRE",
    "HIEROPHANT": "EARTH",
    "SIX_OF_WANDS": "FIRE",
    "EIGHT_OF_SWORDS": "AIR",
    "HANGED_MAN": "WATER",
    "DEATH": "WATER",
    "ACE_OF_WANDS": "FIRE",
    "TOWER": "FIRE",
    "STAR": "AIR",
}

RULES = [
    ("ENDING", "MOVEMENT", "BUSINESS", "ACCELERATE", "기존 국면이 끝난 뒤 상황이 빠르게 움직이기 시작한다", 0.6),
    ("MOVEMENT", "FORMALIZATION", "BUSINESS", "FORMALIZE", "빠른 움직임이 공식적인 구조로 이어진다", 0.4),
    ("SUCCESS", "RESTRICTION", None, "BLOCK", "성과 가능성이 보이지만 현실적·심리적 제약이 진행을 막는다", -0.4),
    ("RESTRICTION", "PAUSE", None, "SLOW_DOWN", "제약을 바로 밀어붙이기보다 관점을 바꾸고 멈춰 살펴야 한다", -0.2),
    ("CHANGE", "BEGINNING", None, "REVERSE", "기존 국면을 끝낸 뒤 새로운 동력이 시작된다", 0.5),
    ("DISRUPTION", "HOPE", None, "RESOLVE", "큰 흔들림 이후 회복 방향과 희망이 나타난다", 0.6),
]


def all_card_rows() -> list[TarotCard]:
    cards: list[TarotCard] = []
    order = 0
    for number, (code, name_ko, name_en) in enumerate(MAJOR_CARDS):
        cards.append(
            TarotCard(
                code=code,
                name_ko=name_ko,
                name_en=name_en,
                arcana="MAJOR",
                suit=None,
                rank=None,
                number=number,
                sort_order=order,
            )
        )
        order += 1

    for suit, suit_ko in SUITS.items():
        for rank, rank_ko, rank_en, number in RANKS:
            cards.append(
                TarotCard(
                    code=f"{rank}_OF_{suit}",
                    name_ko=f"{suit_ko} {rank_ko}",
                    name_en=f"{rank_en} of {suit.title()}",
                    arcana="MINOR",
                    suit=suit,
                    rank=rank,
                    number=number,
                    sort_order=order,
                )
            )
            order += 1
    return cards


def seed_demo_knowledge(session: Session) -> None:
    if session.scalar(select(Source.id).where(Source.code == "INTERNAL_DEMO")) is not None:
        return

    source = Source(
        code="INTERNAL_DEMO",
        title="Tarot Engine v1 Internal Demo Knowledge",
        author="Project Editorial Seed",
        source_type="EDITORIAL",
        license_status="INTERNAL_DEMO",
        priority=999,
    )
    cards = all_card_rows()
    tags = [
        InterpretationTag(code=code, name_ko=name, description=description)
        for code, (name, description) in TAG_DEFINITIONS.items()
    ]
    session.add(source)
    session.add_all(cards)
    session.add_all(tags)
    session.add_all(
        [
            SpreadPosition(spread_code="THREE_FLOW", position_order=1, label_ko="시작", role="START", weight=0.9),
            SpreadPosition(spread_code="THREE_FLOW", position_order=2, label_ko="전개", role="DEVELOPMENT", weight=1.0),
            SpreadPosition(spread_code="THREE_FLOW", position_order=3, label_ko="결과", role="OUTCOME", weight=1.2),
        ]
    )
    session.flush()

    card_by_code = {card.code: card for card in cards}
    tag_by_code = {tag.code: tag for tag in tags}

    for row in DEMO_MEANINGS:
        (
            card_code,
            orientation,
            context,
            meaning,
            advice,
            warning,
            polarity,
            action,
            speed,
            stability,
            ending,
            meaning_tags,
        ) = row
        card_meaning = CardMeaning(
            card_id=card_by_code[card_code].id,
            source_id=source.id,
            orientation=orientation,
            context=context,
            meaning_text=meaning,
            advice_text=advice,
            warning_text=warning,
            polarity=polarity,
            action_level=action,
            speed_level=speed,
            stability_level=stability,
            ending_level=ending,
            origin="EDITORIAL",
            priority=100,
            review_status="APPROVED",
            is_active=True,
        )
        session.add(card_meaning)
        session.flush()
        for tag_code, weight, is_primary in meaning_tags:
            session.add(
                CardMeaningTag(
                    card_meaning_id=card_meaning.id,
                    tag_id=tag_by_code[tag_code].id,
                    weight=weight,
                    is_primary=is_primary,
                )
            )

    for card_code, element in ELEMENTS.items():
        session.add(
            CardCorrespondence(
                card_id=card_by_code[card_code].id,
                source_id=source.id,
                correspondence_type="ELEMENT",
                value=element,
                priority=100,
                review_status="APPROVED",
                is_active=True,
            )
        )

    for from_tag, to_tag, context, relation_type, text, delta in RULES:
        session.add(
            RelationRule(
                from_tag_id=tag_by_code[from_tag].id,
                to_tag_id=tag_by_code[to_tag].id,
                context=context,
                relation_type=relation_type,
                transition_text=text,
                score_delta=delta,
                priority=100,
                source_id=source.id,
                origin="DESIGNED",
                review_status="APPROVED",
                is_active=True,
            )
        )



def seed_public_domain_knowledge(session: Session) -> None:
    """Load the reviewed 78-card public-domain dataset into normalized tables.

    The CSV package is validated before any database mutation. The operation is
    idempotent and can safely upgrade a database that already contains the
    legacy INTERNAL_DEMO seed; public-domain rows have a higher source priority.
    """
    from app.curated_data import load_curated_dataset, validate_curated_dataset

    dataset = load_curated_dataset()
    report = validate_curated_dataset(dataset)
    report.raise_for_errors()

    legacy_source = session.scalar(select(Source).where(Source.code == "INTERNAL_DEMO"))
    if legacy_source is not None:
        legacy_meaning_ids = list(
            session.scalars(select(CardMeaning.id).where(CardMeaning.source_id == legacy_source.id)).all()
        )
        if legacy_meaning_ids:
            session.execute(delete(CardMeaningTag).where(CardMeaningTag.card_meaning_id.in_(legacy_meaning_ids)))
            session.execute(delete(CardMeaning).where(CardMeaning.id.in_(legacy_meaning_ids)))
        session.execute(delete(CardCorrespondence).where(CardCorrespondence.source_id == legacy_source.id))
        session.execute(delete(RelationRule).where(RelationRule.source_id == legacy_source.id))
        session.delete(legacy_source)
        session.flush()

    card_by_code: dict[str, TarotCard] = {}
    for template in all_card_rows():
        card = session.scalar(select(TarotCard).where(TarotCard.code == template.code))
        if card is None:
            card = template
            session.add(card)
        else:
            card.name_ko = template.name_ko
            card.name_en = template.name_en
            card.arcana = template.arcana
            card.suit = template.suit
            card.rank = template.rank
            card.number = template.number
            card.sort_order = template.sort_order
            card.is_active = True
        card_by_code[card.code] = card

    source_by_code: dict[str, Source] = {}
    for row in dataset.sources:
        source = session.scalar(select(Source).where(Source.code == row.code))
        if source is None:
            source = Source(code=row.code)
            session.add(source)
        source.title = row.title
        source.author = row.author or None
        source.publication_year = row.publication_year
        source.source_type = row.source_type
        source.license_status = row.license_status
        source.source_url = row.source_url
        source.rights_basis = row.rights_basis
        source.priority = row.priority
        source.is_active = row.is_active
        source_by_code[row.code] = source

    tag_by_code: dict[str, InterpretationTag] = {}
    for row in dataset.tags:
        tag = session.scalar(select(InterpretationTag).where(InterpretationTag.code == row.code))
        if tag is None:
            tag = InterpretationTag(code=row.code, name_ko=row.name_ko, description=row.description)
            session.add(tag)
        else:
            tag.name_ko = row.name_ko
            tag.description = row.description
        tag_by_code[row.code] = tag

    spread_defaults = (
        (1, "시작", "START", 0.9),
        (2, "전개", "DEVELOPMENT", 1.0),
        (3, "결과", "OUTCOME", 1.2),
    )
    for position_order, label_ko, role, weight in spread_defaults:
        position = session.scalar(
            select(SpreadPosition).where(
                SpreadPosition.spread_code == "THREE_FLOW",
                SpreadPosition.position_order == position_order,
            )
        )
        if position is None:
            position = SpreadPosition(
                spread_code="THREE_FLOW",
                position_order=position_order,
                label_ko=label_ko,
                role=role,
                weight=weight,
            )
            session.add(position)
        else:
            position.label_ko = label_ko
            position.role = role
            position.weight = weight

    session.flush()

    public_source_ids = [source_by_code[row.code].id for row in dataset.sources]
    previous_meaning_ids = list(
        session.scalars(select(CardMeaning.id).where(CardMeaning.source_id.in_(public_source_ids))).all()
    )
    if previous_meaning_ids:
        session.execute(delete(CardMeaningTag).where(CardMeaningTag.card_meaning_id.in_(previous_meaning_ids)))
        session.execute(delete(CardMeaning).where(CardMeaning.id.in_(previous_meaning_ids)))
    session.execute(delete(CardCorrespondence).where(CardCorrespondence.source_id.in_(public_source_ids)))
    session.flush()

    meaning_by_key: dict[tuple[str, str, str], CardMeaning] = {}
    for row in dataset.meanings:
        meaning = CardMeaning(
            card_id=card_by_code[row.card_code].id,
            source_id=source_by_code[row.source_code].id,
            orientation=row.orientation,
            context=row.context,
            meaning_text=row.meaning_text,
            advice_text=row.advice_text,
            warning_text=row.warning_text,
            polarity=row.polarity,
            action_level=row.action_level,
            speed_level=row.speed_level,
            stability_level=row.stability_level,
            ending_level=row.ending_level,
            origin=row.origin,
            source_locator=row.source_locator,
            page_start=row.page_start,
            page_end=row.page_end,
            priority=row.priority,
            review_status=row.review_status,
            review_method=row.review_method,
            review_notes=row.review_notes,
            is_active=row.is_active,
        )
        session.add(meaning)
        meaning_by_key[(row.card_code, row.orientation, row.context)] = meaning
    session.flush()

    for row in dataset.meaning_tags:
        meaning = meaning_by_key[(row.card_code, row.orientation, row.context)]
        session.add(
            CardMeaningTag(
                card_meaning_id=meaning.id,
                tag_id=tag_by_code[row.tag_code].id,
                weight=row.weight,
                is_primary=row.is_primary,
            )
        )

    for row in dataset.correspondences:
        session.add(
            CardCorrespondence(
                card_id=card_by_code[row.card_code].id,
                source_id=source_by_code[row.source_code].id,
                correspondence_type=row.correspondence_type,
                value=row.value,
                source_locator=row.source_locator,
                page_start=row.page_start,
                page_end=row.page_end,
                priority=row.priority,
                review_status=row.review_status,
                review_method=row.review_method,
                review_notes=row.review_notes,
                is_active=row.is_active,
            )
        )

    for row in dataset.relation_rules:
        context = row.context or None
        existing = session.scalar(
            select(RelationRule)
            .where(
                RelationRule.from_tag_id == tag_by_code[row.from_tag_code].id,
                RelationRule.to_tag_id == tag_by_code[row.to_tag_code].id,
                RelationRule.context.is_(None) if context is None else RelationRule.context == context,
                RelationRule.relation_type == row.relation_type,
            )
            .limit(1)
        )
        rule = existing or RelationRule(
            from_tag_id=tag_by_code[row.from_tag_code].id,
            to_tag_id=tag_by_code[row.to_tag_code].id,
            context=context,
            relation_type=row.relation_type,
        )
        if existing is None:
            session.add(rule)
        rule.transition_text = row.transition_text
        rule.score_delta = row.score_delta
        rule.priority = row.priority
        rule.source_id = source_by_code[row.source_code].id if row.source_code else None
        rule.source_locator = row.source_locator
        rule.page_start = None
        rule.page_end = None
        rule.origin = row.origin
        rule.review_status = row.review_status
        rule.review_method = row.review_method
        rule.review_notes = row.review_notes
        rule.is_active = row.is_active

    session.flush()

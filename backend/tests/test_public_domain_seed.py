from collections import Counter

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import CardCorrespondence, CardMeaning, RelationRule, Source, TarotCard, Base
from app.repository import TarotRepository
from app.schemas import CardInput, ReadingContext
from app.seed import seed_public_domain_knowledge


def make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def test_public_domain_seed_loads_complete_approved_dataset_idempotently():
    engine = make_engine()
    with Session(engine) as session:
        seed_public_domain_knowledge(session)
        seed_public_domain_knowledge(session)
        session.commit()

        assert session.scalar(select(func.count()).select_from(TarotCard)) == 78
        assert session.scalar(select(func.count()).select_from(CardMeaning)) == 156
        assert session.scalar(select(func.count()).select_from(CardCorrespondence)) >= 300
        assert session.scalar(select(func.count()).select_from(RelationRule)) >= 30
        assert set(session.scalars(select(Source.code))) >= {"WAITE_PKD_1910", "GOLDEN_DAWN_BOOK_T_1912"}

        meaning_counts = Counter(
            session.execute(select(CardMeaning.orientation, CardMeaning.context)).all()
        )
        assert meaning_counts[("UPRIGHT", "GENERAL")] == 78
        assert meaning_counts[("REVERSED", "GENERAL")] == 78

    engine.dispose()


def test_formerly_unsupported_cards_resolve_after_public_domain_seed():
    engine = make_engine()
    with Session(engine) as session:
        seed_public_domain_knowledge(session)
        session.commit()
        cards = TarotRepository(session).resolve_cards(
            [CardInput(code="FOOL"), CardInput(code="TWO_OF_CUPS"), CardInput(code="WORLD")],
            ReadingContext.GENERAL,
        )

        assert [card.source_code for card in cards] == ["WAITE_PKD_1910"] * 3
        assert all(card.meaning for card in cards)
        assert cards[1].primary_tag == "RELATIONSHIP"
        assert cards[0].source_locator == "Part III §3 — Zero. The Fool"

    engine.dispose()


def test_public_domain_seed_removes_legacy_demo_knowledge():
    from app.seed import seed_demo_knowledge

    engine = make_engine()
    with Session(engine) as session:
        seed_demo_knowledge(session)
        session.commit()
        seed_public_domain_knowledge(session)
        session.commit()

        assert session.scalar(select(Source.id).where(Source.code == "INTERNAL_DEMO")) is None
        cards = TarotRepository(session).resolve_cards(
            [CardInput(code="TEN_OF_SWORDS"), CardInput(code="EIGHT_OF_WANDS"), CardInput(code="HIEROPHANT")],
            ReadingContext.BUSINESS,
        )
        transitions = TarotRepository(session).resolve_transitions(cards, ReadingContext.BUSINESS)
        assert [item.score_delta for item in transitions] == [0.4, 0.3]

    engine.dispose()

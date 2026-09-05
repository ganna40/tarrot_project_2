import pytest
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.repository import TarotRepository
from app.schemas import CardInput, Orientation, ReadingContext
from app.seed import all_card_rows, seed_public_domain_knowledge


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        seed_public_domain_knowledge(session)
        session.commit()
    yield factory
    engine.dispose()


def test_seed_contains_all_78_card_identities(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        assert repository.count_cards() == 78


def test_core_knowledge_tables_do_not_use_json_columns():
    expected = {
        "sources",
        "tarot_cards",
        "card_meanings",
        "interpretation_tags",
        "card_meaning_tags",
        "card_correspondences",
        "relation_rules",
        "spread_positions",
    }
    assert expected.issubset(Base.metadata.tables)
    for table_name in expected:
        table = Base.metadata.tables[table_name]
        assert all(not isinstance(column.type, JSON) for column in table.columns)


def test_context_falls_back_to_general_public_domain_meaning(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        cards = repository.resolve_cards(
            [
                CardInput(code="TEN_OF_SWORDS", orientation=Orientation.UPRIGHT),
                CardInput(code="EIGHT_OF_WANDS", orientation=Orientation.UPRIGHT),
                CardInput(code="HIEROPHANT", orientation=Orientation.UPRIGHT),
            ],
            ReadingContext.BUSINESS,
        )

    assert [card.source_code for card in cards] == ["WAITE_PKD_1910"] * 3
    assert cards[1].primary_tag == "MOVEMENT"
    assert cards[0].position_label == "시작"
    assert cards[2].position_label == "결과"
    assert [card.position_weight for card in cards] == [0.9, 1.0, 1.2]
    assert cards[0].source_locator == "Part III §2 — Swords, Ten"
    assert cards[0].source_url and cards[0].source_url.startswith("https://")


def test_every_card_resolves_upright_and_reversed_general_meanings(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        for card in all_card_rows():
            for orientation in (Orientation.UPRIGHT, Orientation.REVERSED):
                resolved = repository.resolve_cards(
                    [
                        CardInput(code=card.code, orientation=orientation),
                        CardInput(code="MAGICIAN" if card.code != "MAGICIAN" else "HIGH_PRIESTESS"),
                        CardInput(code="WORLD" if card.code != "WORLD" else "SUN"),
                    ],
                    ReadingContext.GENERAL,
                )[0]
                assert resolved.code == card.code
                assert resolved.orientation == orientation
                assert resolved.meaning
                assert resolved.primary_tag


def test_repository_builds_known_pairwise_transitions(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        cards = repository.resolve_cards(
            [CardInput(code="TEN_OF_SWORDS"), CardInput(code="EIGHT_OF_WANDS"), CardInput(code="HIEROPHANT")],
            ReadingContext.BUSINESS,
        )
        transitions = repository.resolve_transitions(cards, ReadingContext.BUSINESS)

    assert [transition.relation_type for transition in transitions] == ["ACCELERATE", "FORMALIZE"]
    assert [transition.to_tag for transition in transitions] == ["MOVEMENT", "FORMALIZATION"]


def test_random_draw_can_use_the_complete_approved_deck(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        drawn = repository.draw_supported_cards(78)

    assert len(drawn) == 78
    assert len({card.code for card in drawn}) == 78

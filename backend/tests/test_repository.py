import pytest
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.repository import KnowledgeNotReadyError, TarotRepository
from app.schemas import CardInput, Orientation, ReadingContext
from app.seed import seed_demo_knowledge


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
        seed_demo_knowledge(session)
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


def test_exact_business_meaning_is_preferred(session_factory):
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

    assert cards[1].source_code == "INTERNAL_DEMO"
    assert "사업" in cards[1].meaning
    assert cards[0].position_label == "시작"
    assert cards[2].position_label == "결과"
    assert [card.position_weight for card in cards] == [0.9, 1.0, 1.2]


def test_general_meaning_is_used_when_context_specific_row_is_missing(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        cards = repository.resolve_cards(
            [
                CardInput(code="SIX_OF_WANDS"),
                CardInput(code="EIGHT_OF_SWORDS"),
                CardInput(code="HANGED_MAN"),
            ],
            ReadingContext.BUSINESS,
        )

    assert cards[2].primary_tag == "PAUSE"
    assert cards[2].meaning == "즉시 결론을 내리기보다 관점을 바꾸고 멈춰 살피는 단계"


def test_missing_approved_meaning_raises_clear_error(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        with pytest.raises(KnowledgeNotReadyError, match="FOOL"):
            repository.resolve_cards(
                [CardInput(code="FOOL"), CardInput(code="STAR"), CardInput(code="TOWER")],
                ReadingContext.GENERAL,
            )


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


def test_random_draw_uses_only_cards_with_approved_demo_meanings(session_factory):
    with session_factory() as session:
        repository = TarotRepository(session)
        drawn = repository.draw_supported_cards(3)

    assert len(drawn) == 3
    assert len({card.code for card in drawn}) == 3

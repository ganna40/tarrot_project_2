from sqlalchemy import create_engine, inspect, text

from app.database import apply_additive_migrations


def test_additive_migration_adds_public_domain_trace_columns_to_legacy_schema():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE sources (id INTEGER PRIMARY KEY, code VARCHAR(64))"))
        connection.execute(text("CREATE TABLE card_meanings (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE card_correspondences (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE relation_rules (id INTEGER PRIMARY KEY)"))

    apply_additive_migrations(engine)
    inspector = inspect(engine)

    assert {column["name"] for column in inspector.get_columns("sources")} >= {"source_url", "rights_basis"}
    for table in ("card_meanings", "card_correspondences", "relation_rules"):
        assert {column["name"] for column in inspector.get_columns(table)} >= {
            "source_locator",
            "review_method",
            "review_notes",
        }
    engine.dispose()

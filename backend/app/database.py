from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base


_ADDITIVE_COLUMNS: dict[str, dict[str, str]] = {
    "sources": {
        "source_url": "TEXT",
        "rights_basis": "TEXT",
    },
    "card_meanings": {
        "source_locator": "VARCHAR(255)",
        "review_method": "VARCHAR(64)",
        "review_notes": "TEXT",
    },
    "card_correspondences": {
        "source_locator": "VARCHAR(255)",
        "review_method": "VARCHAR(64)",
        "review_notes": "TEXT",
    },
    "relation_rules": {
        "source_locator": "VARCHAR(255)",
        "review_method": "VARCHAR(64)",
        "review_notes": "TEXT",
    },
}


def normalize_database_url(database_url: str) -> str:
    """Use SQLAlchemy's psycopg3 dialect for generic PostgreSQL URLs.

    Managed providers such as Render expose `postgresql://...` connection
    strings. This project installs psycopg3, so make the driver explicit while
    leaving already-qualified SQLAlchemy URLs unchanged.
    """
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://") :]
    return database_url


def apply_additive_migrations(engine: Engine) -> None:
    """Add traceability columns when upgrading a database from the demo schema."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name, columns in _ADDITIVE_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspect(connection).get_columns(table_name)}
            for column_name, sql_type in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(
                    text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {sql_type}')
                )
                existing_columns.add(column_name)


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def build_engine(database_url: str | None = None) -> Engine:
    raw_url = database_url or get_settings().database_url
    url = normalize_database_url(raw_url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def init_database() -> None:
    global _engine, _session_factory
    if _engine is None:
        _engine = build_engine()
        _session_factory = build_session_factory(_engine)
    Base.metadata.create_all(_engine)
    apply_additive_migrations(_engine)


def close_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_session() -> Generator[Session, None, None]:
    if _session_factory is None:
        init_database()
    assert _session_factory is not None
    with _session_factory() as session:
        yield session

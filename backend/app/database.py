from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def build_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
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

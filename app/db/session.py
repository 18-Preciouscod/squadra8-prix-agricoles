"""Moteur SQLAlchemy et fabrique de sessions."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_engine = None
_session_factory = None


def get_engine():
    """Crée le moteur à la demande (pratique pour tests et migrations)."""
    global _engine, _session_factory
    if _engine is None:
        url = get_settings().database_url
        options = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            options["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **options)
        _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def nouvelle_session() -> Session:
    """Construit une session indépendante."""
    get_engine()
    assert _session_factory is not None
    return _session_factory()


def get_session() -> Generator[Session, None, None]:
    """Dépendance FastAPI : ouvre puis ferme une session."""
    session = nouvelle_session()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Session contextuelle pour scripts et services synchrones."""
    session = nouvelle_session()
    try:
        yield session
    finally:
        session.close()


def reinitialiser_moteur_pour_tests() -> None:
    """Réinitialise le moteur après changement de DATABASE_URL en tests."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None

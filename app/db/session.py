"""Connexion et gestion des sessions SQLAlchemy."""

from __future__ import annotations

from functools import lru_cache
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Construit une seule fois le moteur à partir de DATABASE_URL."""
    url = get_settings().database_url
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Fabrique les sessions liées au moteur de l'application."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Dépendance FastAPI : ouvre une session et la ferme toujours."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()

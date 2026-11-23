"""Modèles SQLAlchemy des tables (produit, marché, prix, etc.).

Responsable : Precious.
"""

# TODO P1 : déclarer les tables de la partie 4 du plan (SQLAlchemy + migration Alembic).

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe de base de tous les modèles."""

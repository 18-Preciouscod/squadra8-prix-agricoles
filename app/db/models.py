"""Modèles SQLAlchemy de la base Squadra 8."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    CHAR,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Classe de base de tous les modèles."""


class Produit(Base):
    __tablename__ = "produit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    nom_fpma: Mapped[str | None] = mapped_column(String)
    touche: Mapped[int] = mapped_column(Integer, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("touche BETWEEN 1 AND 9", name="ck_produit_touche"),
        UniqueConstraint("touche", name="uq_produit_touche"),
    )


class Marche(Base):
    __tablename__ = "marche"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    commune: Mapped[str] = mapped_column(String, nullable=False)
    nom_fpma: Mapped[str | None] = mapped_column(String)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    licence: Mapped[str | None] = mapped_column(Text)


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    nom_affiche: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="validateur")
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'validateur', 'saisie')", name="ck_utilisateur_role"
        ),
    )


class Prix(Base):
    __tablename__ = "prix"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produit.id"), nullable=False)
    marche_id: Mapped[int] = mapped_column(ForeignKey("marche.id"), nullable=False)
    prix_fcfa: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unite: Mapped[str] = mapped_column(String, nullable=False, default="kg")
    type_prix: Mapped[str] = mapped_column(String, nullable=False, default="detail")
    date_releve: Mapped[date] = mapped_column(Date, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), nullable=False)
    statut: Mapped[str] = mapped_column(String, nullable=False, default="en_attente")
    score_anomalie: Mapped[float | None] = mapped_column(Float)
    motif_anomalie: Mapped[str | None] = mapped_column(Text)
    saisi_par: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id"))
    valide_par: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id"))
    date_validation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motif_rejet: Mapped[str | None] = mapped_column(Text)
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("prix_fcfa > 0", name="ck_prix_positif"),
        CheckConstraint("unite IN ('kg', 'sac_100kg')", name="ck_prix_unite"),
        CheckConstraint("type_prix IN ('detail', 'gros')", name="ck_prix_type"),
        CheckConstraint(
            "statut IN ('en_attente', 'valide', 'rejete')", name="ck_prix_statut"
        ),
        UniqueConstraint(
            "produit_id",
            "marche_id",
            "date_releve",
            "type_prix",
            "source_id",
            name="uq_prix_observation",
        ),
    )


class Appel(Base):
    __tablename__ = "appel"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    numero_hash: Mapped[str | None] = mapped_column(CHAR(64))
    canal: Mapped[str] = mapped_column(String, nullable=False, default="sim")
    debut: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    produit_id: Mapped[int | None] = mapped_column(ForeignKey("produit.id"))
    nb_actions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    demande_humain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    statut: Mapped[str] = mapped_column(String, nullable=False, default="en_cours")


class Interaction(Base):
    __tablename__ = "interaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appel.id"), nullable=False)
    etape: Mapped[str] = mapped_column(String, nullable=False)
    entree: Mapped[str] = mapped_column(String, nullable=False)
    texte_transcrit: Mapped[str | None] = mapped_column(Text)
    intention: Mapped[str | None] = mapped_column(String)
    methode: Mapped[str | None] = mapped_column(String)
    latence_ms: Mapped[int | None] = mapped_column(Integer)
    horodatage: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DemandeRappel(Base):
    __tablename__ = "demande_rappel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_chiffre: Mapped[str | None] = mapped_column(Text)
    numero_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False, index=True)
    motif: Mapped[str] = mapped_column(String, nullable=False, default="bip")
    cree_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    rappel_prevu_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    statut: Mapped[str] = mapped_column(String, nullable=False, default="en_attente")
    efface_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ListeNoire(Base):
    __tablename__ = "liste_noire"

    numero_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    raison: Mapped[str] = mapped_column(Text, nullable=False)
    jusqu_au: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Journal(Base):
    __tablename__ = "journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    utilisateur_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id"))
    action: Mapped[str] = mapped_column(String, nullable=False)
    cible: Mapped[str] = mapped_column(String, nullable=False)
    quand: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

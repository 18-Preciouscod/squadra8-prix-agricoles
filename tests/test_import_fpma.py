"""Tests de l'import FPMA vers la base, sans connexion réseau."""

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models import Base, Marche, Prix, Produit, Source
from data.scripts.import_fpma import importer_lignes


def _base():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _referentiels(session: Session) -> None:
    session.add_all(
        [
            Produit(code="mais", nom="Maïs", nom_fpma="Maïs Blanc", touche=1),
            Marche(
                code="bohicon",
                nom="Bohicon",
                commune="Bohicon",
                nom_fpma="Bohicon",
            ),
        ]
    )
    session.commit()


def _ligne(**overrides: str) -> dict[str, str]:
    ligne = {
        "produit": "Maïs Blanc",
        "marche": "Bohicon",
        "date": "2026-10-15",
        "prix": "250.50",
        "type": "Retail",
        "unite": "KG",
        "devise": "XOF",
    }
    ligne.update(overrides)
    return ligne


def test_import_cree_prix_en_attente_et_est_idempotent() -> None:
    engine = _base()
    with Session(engine) as session:
        _referentiels(session)
        premier = importer_lignes(session, [_ligne()])
        session.commit()
        second = importer_lignes(session, [_ligne()])
        session.commit()

        prix = session.scalars(select(Prix)).all()
        assert premier["importees"] == 1
        assert second["importees"] == 0
        assert second["doublons"] == 1
        assert len(prix) == 1
        assert prix[0].prix_fcfa == Decimal("250.50")
        assert prix[0].date_releve == date(2026, 10, 15)
        assert prix[0].statut == "en_attente"
    engine.dispose()


def test_import_ignore_produit_et_marche_non_reconnus() -> None:
    engine = _base()
    with Session(engine) as session:
        _referentiels(session)
        resume = importer_lignes(
            session,
            [
                _ligne(produit="Produit inconnu"),
                _ligne(marche="Marché inconnu"),
            ],
        )
        session.commit()

        assert resume["produit_inconnu"] == 1
        assert resume["marche_inconnu"] == 1
        assert resume["importees"] == 0
        assert session.scalar(select(Prix.id)) is None
    engine.dispose()


def test_import_rejette_devise_unite_type_et_prix_invalides() -> None:
    engine = _base()
    with Session(engine) as session:
        _referentiels(session)
        resume = importer_lignes(
            session,
            [
                _ligne(devise="USD"),
                _ligne(unite="litre"),
                _ligne(type="moyenne"),
                _ligne(prix="-12"),
                _ligne(date="date-invalide"),
            ],
        )
        session.commit()

        assert resume["donnee_invalide"] == 5
        assert resume["importees"] == 0
        assert session.scalar(select(Prix.id)) is None
    engine.dispose()


def test_dry_run_annule_toute_insertion() -> None:
    engine = _base()
    with Session(engine) as session:
        _referentiels(session)
        resume = importer_lignes(session, [_ligne()], dry_run=True)

        assert resume["importees"] == 1
        assert session.scalar(select(Prix.id)) is None
        assert session.scalar(select(Source.id).where(Source.code == "FAO_FPMA")) is None
    engine.dispose()

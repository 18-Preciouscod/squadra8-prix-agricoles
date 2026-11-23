"""Tests des modèles, de la session et du chargement des référentiels."""

from pathlib import Path

from sqlalchemy import Float, create_engine, select
from sqlalchemy.orm import Session

from app.db.models import Base, Marche, Prix, Produit
from app.db.seed import SEEDS_DIR, charger_donnees

SEEDS_REPO = Path(__file__).resolve().parents[1] / "data" / "seeds"


def test_metadata_declare_les_dix_tables() -> None:
    assert set(Base.metadata.tables) == {
        "produit", "marche", "source", "utilisateur", "prix",
        "appel", "interaction", "demande_rappel", "liste_noire", "journal",
    }


def test_produit_touche_unique_et_types_prix() -> None:
    noms = {c.name for c in Produit.__table__.constraints if getattr(c, "name", None)}
    assert "uq_produit_touche" in noms
    assert "ck_produit_touche" in noms
    assert isinstance(Prix.__table__.c.score_anomalie.type, Float)
    # Annotation Python = date (pas le type SQLAlchemy Date).
    assert "date" in str(Prix.__annotations__["date_releve"]).casefold()


def test_chargement_csv_est_rejouable_et_ne_cree_pas_de_doublons(tmp_path) -> None:
    (tmp_path / "produits.csv").write_text(
        "code,nom,nom_fpma,touche,actif\nmais,Maïs,,1,true\n",
        encoding="utf-8",
    )
    (tmp_path / "marches.csv").write_text(
        "code,nom,commune,nom_fpma,actif\nbohicon,Bohicon,Bohicon,,true\n",
        encoding="utf-8",
    )
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first = charger_donnees(session, tmp_path)
        session.commit()
        second = charger_donnees(session, tmp_path)
        session.commit()

        assert first == {"produits": 1, "marches": 1}
        assert second == {"produits": 0, "marches": 0}
        assert session.scalar(select(Produit).where(Produit.code == "mais")) is not None
        assert session.scalar(select(Marche).where(Marche.code == "bohicon")) is not None

    engine.dispose()


def test_seed_reel_mvp_six_produits_trois_marches() -> None:
    """Charge les vrais CSV du dépôt (data/seeds), pas un fichier temporaire."""
    assert SEEDS_DIR == SEEDS_REPO or SEEDS_DIR.resolve() == SEEDS_REPO.resolve()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        premier = charger_donnees(session, SEEDS_REPO)
        session.commit()
        second = charger_donnees(session, SEEDS_REPO)
        session.commit()

        produits = session.scalars(select(Produit).order_by(Produit.touche)).all()
        marches = session.scalars(select(Marche).order_by(Marche.code)).all()

        assert premier == {"produits": 6, "marches": 3}
        assert second == {"produits": 0, "marches": 0}
        assert len(produits) == 6
        assert len(marches) == 3

        attendus_produits = [
            ("mais_blanc", "Maïs Blanc", "Maïs Blanc", 1),
            ("mais_jaune", "Maïs Jaune", "Maïs Jaune", 2),
            ("soja", "Soja", "Soja", 3),
            ("haricot_blanc", "Haricot blanc", "Haricot blanc", 4),
            ("haricot_noir", "Haricot noir", "Haricot noir", 5),
            ("haricot_rouge", "Haricot rouge", "Haricot rouge", 6),
        ]
        assert [(p.code, p.nom, p.nom_fpma, p.touche) for p in produits] == attendus_produits
        assert len({p.touche for p in produits}) == 6

        attendus_marches = [
            ("azogotchebou", "Azogotchébou (Covè)", "Covè", "Azogotchébou (Covè)"),
            ("bohicon", "Bohicon", "Bohicon", "Bohicon"),
            ("houndjro", "Houndjro (Abomey)", "Abomey", "Houndjro (Abomey)"),
        ]
        assert [
            (m.code, m.nom, m.commune, m.nom_fpma) for m in marches
        ] == attendus_marches
        noms = {m.nom for m in marches}
        assert "Abomey" not in noms
        assert "Hlanxi (Zogbodomey)" not in noms
        assert "Covè" not in noms  # commune oui, marché non

    engine.dispose()

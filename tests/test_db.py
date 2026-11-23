"""Tests des modèles, de la session et du chargement des référentiels."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models import Base, Marche, Produit
from app.db.seed import charger_donnees


def test_metadata_declare_les_dix_tables() -> None:
    assert set(Base.metadata.tables) == {
        "produit", "marche", "source", "utilisateur", "prix",
        "appel", "interaction", "demande_rappel", "liste_noire", "journal",
    }


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

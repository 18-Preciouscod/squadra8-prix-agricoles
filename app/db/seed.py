"""Chargement idempotent des référentiels de départ."""
from __future__ import annotations

import csv
from pathlib import Path

import bcrypt
from sqlalchemy import select

from app.config import get_settings
from app.db.models import Marche, Produit, Source, Utilisateur
from app.db.session import nouvelle_session

ROOT = Path(__file__).resolve().parents[2]
SEEDS = ROOT / "data" / "seeds"


def _lire_csv(nom: str) -> list[dict[str, str]]:
    with (SEEDS / nom).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "oui", "yes"}


def run() -> None:
    """Insère les référentiels sans écraser les modifications existantes."""
    settings = get_settings()
    with nouvelle_session() as session:
        for row in _lire_csv("produits.csv"):
            if not session.scalar(select(Produit).where(Produit.code == row["code"])):
                session.add(Produit(code=row["code"], nom=row["nom"],
                    nom_fpma=row.get("nom_fpma") or None,
                    touche=int(row["touche"]) if row.get("touche") else None,
                    actif=_bool(row.get("actif", "true"))))
        for row in _lire_csv("marches.csv"):
            if not session.scalar(select(Marche).where(Marche.code == row["code"])):
                session.add(Marche(code=row["code"], nom=row["nom"], commune=row["commune"],
                    nom_fpma=row.get("nom_fpma") or None,
                    actif=_bool(row.get("actif", "true"))))
        sources = [
            {"code": "fpma", "nom": "FPMA – SIM-Bénin", "url": "https://fpma.review.fao.org/", "licence": "Source publique FPMA"},
            {"code": "saisie", "nom": "Saisie manuelle validée", "url": None, "licence": None},
        ]
        for row in sources:
            if not session.scalar(select(Source).where(Source.code == row["code"])):
                session.add(Source(**row))
        if settings.admin_email and settings.admin_password_initial:
            email = settings.admin_email.strip().lower()
            if not session.scalar(select(Utilisateur).where(Utilisateur.email == email)):
                hashed = bcrypt.hashpw(settings.admin_password_initial.encode(), bcrypt.gensalt()).decode()
                session.add(Utilisateur(email=email, nom_affiche="Administrateur",
                    role="admin", mot_de_passe_hash=hashed, actif=True))
        session.commit()


if __name__ == "__main__":
    run()

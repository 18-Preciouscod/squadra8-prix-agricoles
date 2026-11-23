"""Accès strict aux prix validés et encore frais."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.models import Marche, Prix, Produit, Source
from app.db.session import session_scope

FRAICHEUR_MAX_JOURS = 60


def prix_du_jour(produit: str, *, date_reference: date | None = None,
                 fraicheur_max_jours: int = FRAICHEUR_MAX_JOURS) -> list[dict]:
    """Retourne les observations validées, détaillées au kilo, âgées de 0 à 60 jours."""
    aujourd_hui = date_reference or date.today()
    seuil = aujourd_hui - timedelta(days=fraicheur_max_jours)
    with session_scope() as session:
        stmt = (
            select(Prix, Produit, Marche, Source)
            .join(Produit, Prix.produit_id == Produit.id)
            .join(Marche, Prix.marche_id == Marche.id)
            .join(Source, Prix.source_id == Source.id)
            .where(
                Produit.code == produit,
                Produit.actif.is_(True),
                Marche.actif.is_(True),
                Prix.statut == "valide",
                Prix.date_releve >= seuil,
                Prix.date_releve <= aujourd_hui,
                Prix.unite == "kg",
                Prix.type_prix == "detail",
            )
            .order_by(Prix.date_releve.desc(), Marche.nom.asc())
        )
        rows = session.execute(stmt).all()
        return [
            {
                "id": p.id, "produit": prod.nom, "marche": m.nom,
                "commune": m.commune, "prix_fcfa": Decimal(p.prix_fcfa),
                "unite": p.unite, "type_prix": p.type_prix,
                "date_releve": p.date_releve.isoformat(),
                "source": src.nom, "statut": p.statut,
            }
            for p, prod, m, src in rows
        ]

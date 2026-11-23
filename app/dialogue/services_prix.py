"""Adaptateur : Services du moteur ← get_source_prix() (plan B FAO)."""

from __future__ import annotations

from app.dialogue.moteur import Services
from app.services.calculs import juger_offre
from app.services.source_prix import get_source_prix


def services_reels() -> Services:
    """Construit l'objet Services branché sur la source de prix configurée."""

    def prix(produit: str) -> list[dict]:
        return get_source_prix().prix_du_jour(produit)

    def offre(produit: str, montant_sac: float) -> dict | None:
        liste = get_source_prix().prix_du_jour(produit)
        if not liste:
            return None
        # Même règle que POST /api/offre : premier marché disponible.
        ref = liste[0]
        offre_kg = float(montant_sac) / 100.0
        jugement = juger_offre(offre_kg, float(ref["prix_kg"]))
        return {
            "offre_kg": offre_kg,
            "reference_kg": float(ref["prix_kg"]),
            "marche": ref["marche"],
            "date_releve": ref["date_releve"],
            **jugement,
        }

    return Services(prix=prix, offre=offre)

"""Lit les prix VALIDÉS et applique les règles de date (fraîcheur).

Responsable : Precious.

Façade mince : délègue à get_source_prix() (CSV FAO plan B, puis base).
Aucun schéma SQL inventé ici.
"""

from __future__ import annotations

from app.services.source_prix import get_source_prix


def prix_du_jour(produit: str) -> list:
    """Retourne les prix disponibles d'un produit (un par marché MVP)."""
    return get_source_prix().prix_du_jour(produit)


def dernier_prix(produit: str, marche: str) -> dict | None:
    """Dernier prix « ok » pour un couple produit/marché, ou None."""
    return get_source_prix().dernier_prix(produit, marche)

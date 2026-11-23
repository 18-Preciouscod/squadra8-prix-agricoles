"""Limites de bips (rappels automatiques) et liste noire.

Responsable : 4e développeur.
"""

# TODO : au plus 3 bips par numéro et par heure, 10 par jour, 60 s entre deux,
#        liste noire, plafond global de 50 rappels par jour.


def bip_autorise(numero_hash: str) -> bool:
    """Indique si un nouveau bip est autorisé pour ce numéro. À implémenter."""
    raise NotImplementedError("TODO : règles anti-abus")

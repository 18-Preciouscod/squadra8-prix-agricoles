"""Chiffrement du numéro (Fernet) et hash pour les statistiques (HMAC-SHA256).

Responsable : 4e développeur.
"""

# TODO : chiffrer avec FERNET_KEY (puis effacer après le rappel) ;
#        hasher avec HASH_PEPPER (HMAC-SHA256) pour les stats et l'anti-abus.


def hasher_numero(numero: str) -> str:
    """Retourne le hash HMAC-SHA256 du numéro. À implémenter."""
    raise NotImplementedError("TODO : hash HMAC du numéro")


def chiffrer_numero(numero: str) -> str:
    """Chiffre le numéro avec Fernet. À implémenter."""
    raise NotImplementedError("TODO : chiffrement Fernet du numéro")

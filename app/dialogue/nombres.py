from num2words import num2words

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def arrondi(n):
    """Entier le plus proche (0,5 arrondi vers le haut)."""
    return int(n + 0.5)


def en_lettres(n):
    return num2words(arrondi(n), lang="fr")


def francs(n):
    return "franc" if arrondi(n) == 1 else "francs"


def date_en_lettres(iso):
    """'2026-10-25' -> 'vingt-cinq octobre'."""
    _, mois, jour = iso.split("-")
    j = int(jour)
    mot = "premier" if j == 1 else en_lettres(j)
    return f"{mot} {MOIS[int(mois) - 1]}"

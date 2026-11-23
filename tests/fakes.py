"""Fakes pour les tests unitaires du moteur uniquement."""

from __future__ import annotations

from app.dialogue.moteur import Services
from app.services.calculs import juger_offre, vers_100kg

SOURCE = "SIM-Bénin (FAO FPMA)"

# Ordre = ORDRE_MARCHES (Bohicon en premier). Noms FAO exacts. Pas de 4e marché.
PRIX = {
    "mais": [
        {
            "marche": "Bohicon",
            "prix_fcfa": 137.36,
            "prix_kg": 137.36,
            "prix_100kg": vers_100kg(137.36),
            "unite": "Kilogramme",
            "type_prix": "detail",
            "date_releve": "2026-10-25",
            "source": SOURCE,
        },
        {
            "marche": "Houndjro (Abomey)",
            "prix_fcfa": 128.57,
            "prix_kg": 128.57,
            "prix_100kg": vers_100kg(128.57),
            "unite": "Kilogramme",
            "type_prix": "detail",
            "date_releve": "2026-10-19",
            "source": SOURCE,
        },
        {
            "marche": "Azogotchébou (Covè)",
            "prix_fcfa": 140.0,
            "prix_kg": 140.0,
            "prix_100kg": vers_100kg(140.0),
            "unite": "Kilogramme",
            "type_prix": "detail",
            "date_releve": "2026-10-28",
            "source": SOURCE,
        },
    ],
    "soja": [
        {
            "marche": "Bohicon",
            "prix_fcfa": 407.0,
            "prix_kg": 407.0,
            "prix_100kg": vers_100kg(407.0),
            "unite": "Kilogramme",
            "type_prix": "detail",
            "date_releve": "2026-10-25",
            "source": SOURCE,
        },
    ],
    "haricot": [
        {
            "marche": "Bohicon",
            "prix_fcfa": 652.0,
            "prix_kg": 652.0,
            "prix_100kg": vers_100kg(652.0),
            "unite": "Kilogramme",
            "type_prix": "detail",
            "date_releve": "2026-10-25",
            "source": SOURCE,
        },
    ],
}


class FakeJournal:
    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []

    def __call__(self, appel_id: str, etape: str, entree: str) -> None:
        self.lignes.append((appel_id, etape, entree))


def services_fakes(*, sans_prix: bool = False, journal=None) -> Services:
    def prix(produit: str) -> list[dict]:
        return [] if sans_prix else list(PRIX.get(produit, []))

    def offre(produit: str, montant_sac: float) -> dict | None:
        liste = [] if sans_prix else PRIX.get(produit, [])
        if not liste:
            return None
        # Sans marché précisé : premier de la liste (Bohicon s'il est là).
        ref = liste[0]
        offre_kg = float(montant_sac) / 100.0
        jugement = juger_offre(offre_kg, float(ref["prix_fcfa"]))
        return {
            "offre_kg": offre_kg,
            "reference_kg": float(ref["prix_fcfa"]),
            "marche": ref["marche"],
            "date_releve": ref["date_releve"],
            **jugement,
        }

    if journal is None:
        return Services(prix=prix, offre=offre)
    return Services(prix=prix, offre=offre, journal=journal)

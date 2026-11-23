from app.dialogue.moteur import Services

SOURCE = "SIM-Bénin (FAO FPMA)"
PRIX = {
    "mais": [
        {"marche": "Abomey (Houndjro)", "prix_fcfa": 174, "unite": "kg", "type_prix": "detail",
         "date_releve": "2026-10-27", "source": SOURCE, "fraicheur": "fao_ok"},
        {"marche": "Bohicon", "prix_fcfa": 137.36, "unite": "kg", "type_prix": "detail",
         "date_releve": "2026-10-25", "source": SOURCE, "fraicheur": "fao_ok"},
        {"marche": "Covè (Azogotchébou)", "prix_fcfa": 137, "unite": "kg", "type_prix": "detail",
         "date_releve": "2026-10-28", "source": SOURCE, "fraicheur": "fao_ok"},
        {"marche": "Zogbodomey (Hlanxi)", "prix_fcfa": 137, "unite": "kg", "type_prix": "detail",
         "date_releve": "2026-10-29", "source": SOURCE, "fraicheur": "fao_ok"},
    ],
    "soja": [
        {"marche": "Bohicon", "prix_fcfa": 407, "unite": "kg", "type_prix": "detail",
         "date_releve": "2026-10-25", "source": SOURCE, "fraicheur": "fao_ok"},
    ],
    "haricot": [
        {"marche": "Bohicon", "prix_fcfa": 652, "unite": "kg", "type_prix": "detail",
         "date_releve": "2026-10-25", "source": SOURCE, "fraicheur": "fao_ok"},
    ],
}


class FakeJournal:
    def __init__(self):
        self.lignes = []

    def __call__(self, appel_id, etape, entree):
        self.lignes.append((appel_id, etape, entree))


def services_fakes(sans_prix=False, journal=None):
    def prix(produit):
        return [] if sans_prix else PRIX.get(produit, [])

    def offre(produit, montant_sac):
        liste = [] if sans_prix else PRIX.get(produit, [])
        ref = next((p for p in liste if p["marche"] == "Bohicon"), None)
        if ref is None:
            return None
        offre_kg = montant_sac / 100
        return {"offre_kg": offre_kg, "reference_kg": ref["prix_fcfa"],
                "ecart_kg": round(offre_kg - ref["prix_fcfa"], 2),
                "marche": "Bohicon", "date_releve": ref["date_releve"]}

    if journal is None:
        return Services(prix=prix, offre=offre)
    return Services(prix=prix, offre=offre, journal=journal)

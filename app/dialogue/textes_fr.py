"""Toutes les phrases du service. Rien n'est écrit en dur dans moteur.py."""
from app.dialogue.nombres import arrondi, date_en_lettres, en_lettres, francs

# Phrases fixes (mêmes identifiants que app/voix/phrases.csv)
TEXTES = {
    "A01": "Bonjour. Ici le service des prix agricoles. Nos prix viennent du système public d'information sur les marchés et sont vérifiés par une personne.",
    "P00": "Pour le maïs, tapez 1. Pour le soja, tapez 2. Pour le haricot, tapez 3.",
    "M01": "Pour les prix du jour sur 4 marchés, tapez 1.",
    "M02": "Pour juger l'offre d'un acheteur, tapez 2.",
    "M03": "Pour poser votre question à voix haute, tapez 3.",
    "M03B": "Pour poser votre question à voix haute, tapez 3 : bientôt disponible.",
    "M04": "Pour réécouter, tapez 4.",
    "R01": "Pour une autre information, tapez 1, 2 ou 3. Pour réécouter, tapez 4.",
    "V05": "Cette fonction arrive bientôt.",
    # Ajoutées pour le moteur
    "AV01": "Ce prix est un repère, pas une garantie.",
    "AV02": "Source : le système public d'information sur les marchés du Bénin.",
    "E01": "Cette touche n'est pas valide.",
    "S01": "Je n'ai rien entendu.",
    "N01": "Je n'ai pas compris.",
    "F01": "Merci de votre appel. Au revoir.",
    "O01": "Tapez le prix proposé pour un sac de 100 kilos, puis dièse.",
    "O02": "Ce montant n'est pas valide.",
    "X01": "Posez votre question après le bip.",
    "D01": "Il n'y a pas de prix récent pour ce produit.",
}

NOMS_PRODUITS = {"mais": "Maïs blanc", "soja": "Soja", "haricot": "Haricot blanc"}
TOUCHE_PRODUIT = {"1": "mais", "2": "soja", "3": "haricot"}


# Phrases construites avec des données (nombres et dates en toutes lettres)
def phrase_entete_prix(produit):
    return f"{NOMS_PRODUITS[produit]}, prix de détail au kilo."


def phrase_marche(p):
    return (f"{p['marche']} : {en_lettres(p['prix_fcfa'])} {francs(p['prix_fcfa'])}, "
            f"relevé le {date_en_lettres(p['date_releve'])}.")


def phrase_cent_kilos(p):
    total = arrondi(p["prix_fcfa"]) * 100
    return (f"Soit environ {en_lettres(total)} francs pour cent kilos "
            f"au prix de détail à {p['marche']}.")


def phrases_offre(o):
    ecart = o["ecart_kg"]
    e = arrondi(abs(ecart))
    if e == 0:
        verdict = "L'offre est égale au prix de détail."
    elif ecart < 0:
        verdict = f"L'offre est {en_lettres(e)} {francs(e)} plus basse que le prix de détail."
    else:
        verdict = f"L'offre est {en_lettres(e)} {francs(e)} plus haute que le prix de détail."
    return [
        f"L'acheteur propose {en_lettres(o['offre_kg'])} {francs(o['offre_kg'])} le kilo.",
        (f"Au détail, le kilo est à {en_lettres(o['reference_kg'])} "
         f"{francs(o['reference_kg'])} à {o['marche']}, "
         f"relevé le {date_en_lettres(o['date_releve'])}."),
        verdict,
    ]

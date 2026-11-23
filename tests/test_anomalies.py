"""Détection des prix anormaux : règles A–D, sans LLM ni réseau."""

from __future__ import annotations

from datetime import date, timedelta

from app.ia.anomalies import analyser, analyser_prix, charger_seuils


def _j(jours: int, base: date = date(2025, 6, 15)) -> date:
    return base - timedelta(days=jours)


def test_charger_seuils_valeurs_attendues() -> None:
    s = charger_seuils()
    assert s["seuil_A_pct"] == 30
    assert s["ecart_max_A_jours"] == 21
    assert s["seuil_B_pct"] == 50
    assert s["fenetre_B_jours"] == 3
    assert s["min_voisins_B"] == 1
    assert s["fenetre_C_mois"] == 12
    assert s["marge_C_pct"] == 15
    assert s["min_observations_C"] == 8
    assert s["facteur_10_ratio"] == 8
    assert s["confusion_sac_kilo_ratio"] == 80
    assert s["unites_acceptees"] == ["Kilogramme", "kg", "sac_100kg"]


def test_prix_normal_ok_sans_raison() -> None:
    historique = [{"date": _j(7), "prix": 200.0}]
    voisins = [
        {"date": date(2025, 6, 15), "prix": 205.0, "marche": "abomey"},
        {"date": date(2025, 6, 14), "prix": 195.0, "marche": "cove"},
    ]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=200.0,
        unite="kg",
        historique=historique,
        voisins=voisins,
    )
    assert r["statut"] == "ok"
    assert r["raisons"] == []
    assert r["motif"] == ""


def test_hausse_10_pct_ok() -> None:
    historique = [{"date": _j(5), "prix": 200.0}]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=220.0,  # +10 %
        historique=historique,
    )
    assert r["statut"] == "ok"
    assert r["raisons"] == []


def test_hausse_40_pct_en_8_jours_regle_A() -> None:
    historique = [{"date": _j(8), "prix": 200.0}]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=280.0,  # +40 %
        historique=historique,
    )
    assert r["statut"] == "a_verifier"
    assert "A_variation_dernier_prix" in r["raisons"]
    assert "40" in r["motif"] or "Variation" in r["motif"]


def test_deux_fois_mediane_voisins_regle_B() -> None:
    # Médiane des voisins = 200 → prix 400 = +100 % > 50 %
    voisins = [
        {"date": date(2025, 6, 15), "prix": 180.0, "marche": "abomey"},
        {"date": date(2025, 6, 14), "prix": 200.0, "marche": "cove"},
        {"date": date(2025, 6, 13), "prix": 220.0, "marche": "abomey"},
    ]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=400.0,
        voisins=voisins,
    )
    assert r["statut"] == "a_verifier"
    assert "B_ecart_marches_voisins" in r["raisons"]


def test_hors_plage_historique_regle_C() -> None:
    # 8 points entre 180 et 220 ; bornes [180*0.85=153 ; 220*1.15=253]
    historique = [
        {"date": date(2025, 1, 10) + timedelta(days=i * 20), "prix": 180.0 + (i % 5) * 10}
        for i in range(8)
    ]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=140.0,  # sous min × 0,85
        historique=historique,
    )
    assert r["statut"] == "a_verifier"
    assert "C_hors_plage_historique" in r["raisons"]

    r_haut = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=300.0,  # au-dessus de max × 1,15
        historique=historique,
    )
    assert r_haut["statut"] == "a_verifier"
    assert "C_hors_plage_historique" in r_haut["raisons"]


def test_prix_nul_ou_negatif_regle_D() -> None:
    for valeur in (0.0, -5.0):
        r = analyser_prix(
            produit="mais",
            marche="bohicon",
            date_prix=date(2025, 6, 15),
            prix=valeur,
        )
        assert r["statut"] == "a_verifier"
        assert "D_prix_nul_ou_negatif" in r["raisons"]


def test_prix_dix_fois_precedent_regle_D() -> None:
    historique = [{"date": _j(3), "prix": 200.0}]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=2000.0,  # ×10
        historique=historique,
    )
    assert r["statut"] == "a_verifier"
    assert "D_facteur_10" in r["raisons"]


def test_prix_precedent_trop_vieux_A_ne_se_declenche_pas() -> None:
    # +40 % mais dernier prix il y a 30 jours (> 21) → A ignorée
    historique = [{"date": _j(30), "prix": 200.0}]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=280.0,
        historique=historique,
    )
    assert "A_variation_dernier_prix" not in r["raisons"]
    assert r["statut"] == "ok"
    assert r["raisons"] == []


def test_pas_de_voisin_B_ne_se_declenche_pas() -> None:
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=999.0,
        voisins=[],
    )
    assert "B_ecart_marches_voisins" not in r["raisons"]


def test_historique_insuffisant_C_ne_se_declenche_pas() -> None:
    # 7 points seulement (< 8) ; prix hors plage théorique → C ignorée
    historique = [
        {"date": date(2025, 2, 1) + timedelta(days=i * 15), "prix": 200.0}
        for i in range(7)
    ]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=50.0,
        historique=historique,
    )
    assert "C_hors_plage_historique" not in r["raisons"]


def test_haricot_sans_historique_fao_reste_correct() -> None:
    """Haricot noir à Bohicon : pas d'historique FAO → pas d'invention, statut ok."""
    r = analyser_prix(
        produit="haricot",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=350.0,
        unite="kg",
        historique=None,
        voisins=None,
    )
    assert r["statut"] == "ok"
    assert r["raisons"] == []
    assert r["motif"] == ""


def test_unite_inattendue_regle_D() -> None:
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=200.0,
        unite="litre",
    )
    assert r["statut"] == "a_verifier"
    assert "D_unite_inattendue" in r["raisons"]


def test_confusion_sac_kilo_regle_D() -> None:
    historique = [{"date": _j(2), "prix": 200.0}]
    r = analyser_prix(
        produit="mais",
        marche="bohicon",
        date_prix=date(2025, 6, 15),
        prix=200.0 * 80,  # ×80
        historique=historique,
    )
    assert r["statut"] == "a_verifier"
    assert "D_confusion_sac_kilo" in r["raisons"]
    assert "D_facteur_10" in r["raisons"]


def test_analyser_entree_listes() -> None:
    resultats = analyser(
        prix_a_analyser=[
            {
                "id": 1,
                "produit": "mais",
                "marche": "bohicon",
                "date": date(2025, 6, 15),
                "prix": 200.0,
                "historique": [{"date": _j(7), "prix": 200.0}],
            },
            {
                "id": 2,
                "produit": "mais",
                "marche": "bohicon",
                "date": date(2025, 6, 15),
                "prix": 0.0,
            },
        ]
    )
    assert resultats[0]["statut"] == "ok"
    assert resultats[0]["prix_id"] == 1
    assert resultats[1]["statut"] == "a_verifier"
    assert "D_prix_nul_ou_negatif" in resultats[1]["raisons"]

from pathlib import Path

from app.dialogue.moteur import Evenement, Moteur
from tests.fakes import FakeJournal, services_fakes


def texte(tour):
    return " ".join(p.texte for p in tour.phrases)


def nouvel_appel(**kw):
    moteur = Moteur(services_fakes(**kw.pop("fakes", {})), **kw)
    sess = moteur.nouvelle_session("test")

    def jouer(type_, valeur=None):
        return moteur.traiter(sess, Evenement(type=type_, valeur=valeur))

    return jouer


def au_menu(**kw):
    jouer = nouvel_appel(**kw)
    jouer("DECROCHE")
    jouer("TOUCHE", "1")  # maïs
    return jouer


def test_accueil():
    jouer = nouvel_appel()
    tour = jouer("DECROCHE")
    assert tour.etat == "CHOIX_PRODUIT"
    assert "service des prix agricoles" in texte(tour)
    assert tour.attente == "touche"
    assert tour.touches_valides == ["1", "2", "3"]


def test_parcours_nominal():
    jouer = au_menu()
    tour = jouer("TOUCHE", "1")
    t = texte(tour)
    assert tour.etat == "MENU_PRINCIPAL"
    assert "Bohicon" in t and "cent trente-sept" in t
    assert "vingt-cinq octobre" in t
    assert "repère" in t and "Source" in t


def test_avertissement_dit_une_seule_fois():
    jouer = au_menu()
    assert "repère" in texte(jouer("TOUCHE", "1"))
    assert "repère" not in texte(jouer("TOUCHE", "1"))


def test_touche_invalide_puis_fin():
    jouer = nouvel_appel()
    jouer("DECROCHE")
    tour = jouer("TOUCHE", "9")
    assert tour.etat == "CHOIX_PRODUIT" and "pas valide" in texte(tour) and not tour.fin
    jouer("TOUCHE", "9")
    assert jouer("TOUCHE", "9").fin


def test_silence_repete_puis_fin():
    jouer = nouvel_appel()
    jouer("DECROCHE")
    tour = jouer("SILENCE")
    assert "rien entendu" in texte(tour) and not tour.fin
    assert jouer("SILENCE").fin


def test_touche_4_rejoue_mot_pour_mot():
    jouer = au_menu()
    prix = jouer("TOUCHE", "1")
    rejoue = jouer("TOUCHE", "4")
    assert [p.texte for p in rejoue.phrases] == [p.texte for p in prix.phrases]


def test_offre_douze_mille():
    jouer = au_menu()
    tour = jouer("TOUCHE", "2")
    assert tour.attente == "montant"
    for c in "12000":
        jouer("TOUCHE", c)
    tour = jouer("TOUCHE", "#")
    t = texte(tour)
    assert tour.etat == "MENU_PRINCIPAL"
    assert "cent vingt" in t and "cent trente-sept" in t
    assert "dix-sept" in t and "plus basse" in t


def test_montant_vide_refuse():
    jouer = au_menu()
    jouer("TOUCHE", "2")
    tour = jouer("TOUCHE", "#")
    assert "pas valide" in texte(tour) and tour.attente == "montant"


def test_montant_trop_long_refuse():
    jouer = au_menu()
    jouer("TOUCHE", "2")
    for c in "12345678":
        tour = jouer("TOUCHE", c)
    assert "pas valide" in texte(tour)


def test_prix_absent():
    jouer = au_menu(fakes={"sans_prix": True})
    tour = jouer("TOUCHE", "1")
    assert "pas de prix récent" in texte(tour)
    assert "4" in tour.touches_valides


def test_voix_desactivee():
    jouer = nouvel_appel(voix_active=False)
    jouer("DECROCHE")
    menu = jouer("TOUCHE", "1")
    assert "bientôt disponible" in texte(menu)
    tour = jouer("TOUCHE", "3")
    assert "arrive bientôt" in texte(tour) and tour.etat == "MENU_PRINCIPAL"


def test_voix_active():
    jouer = au_menu()
    tour = jouer("TOUCHE", "3")
    assert tour.etat == "QUESTION_VOIX" and tour.attente == "voix"


def test_raccroche_termine():
    jouer = au_menu()
    assert jouer("RACCROCHE").fin


def test_journal_enregistre_les_evenements():
    journal = FakeJournal()
    jouer = nouvel_appel(fakes={"journal": journal})
    jouer("DECROCHE")
    jouer("TOUCHE", "1")
    assert ("test", "ACCUEIL", "DECROCHE:") in journal.lignes
    assert len(journal.lignes) == 2


def test_moteur_independant_du_canal():
    code = Path("app/dialogue/moteur.py").read_text(encoding="utf-8")
    imports = [
        ligne.lower()
        for ligne in code.splitlines()
        if ligne.startswith(("import ", "from "))
    ]
    for interdit in ("twilio", "fastapi", "app.api"):
        assert not any(interdit in ligne for ligne in imports)

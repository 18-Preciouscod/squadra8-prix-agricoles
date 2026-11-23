"""Jouer un appel dans le terminal : python -m app.dialogue.console"""
import os

from app.dialogue.moteur import Evenement, Moteur
from tests.fakes import services_fakes


def main():
    voix = os.getenv("QUESTION_VOIX_ACTIVE", "true").lower() == "true"
    moteur = Moteur(services_fakes(), voix_active=voix)
    sess = moteur.nouvelle_session("console")
    tour = moteur.traiter(sess, Evenement(type="DECROCHE"))
    while True:
        for p in tour.phrases:
            print(f"  [{p.id}] {p.texte}")
        if tour.fin:
            print("--- fin de l'appel ---")
            break
        print(f"  (attend : {tour.attente} {tour.touches_valides})")
        saisie = input("touche (vide = silence, q = raccrocher) > ").strip()
        if saisie == "q":
            evenements = [Evenement(type="RACCROCHE")]
        elif saisie == "":
            evenements = [Evenement(type="SILENCE")]
        else:
            evenements = [Evenement(type="TOUCHE", valeur=c)
                          for c in saisie.replace(" ", "")]
        for ev in evenements:
            tour = moteur.traiter(sess, ev)
            if tour.fin:
                break


if __name__ == "__main__":
    main()
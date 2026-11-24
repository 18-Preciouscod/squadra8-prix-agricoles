"""Génère les clips audio des phrases fixes (et, avec --dynamiques, des prix de démo).

Usage :
    python -m app.voix.generer_clips                 # génère ce qui manque ou a changé
    python -m app.voix.generer_clips --force         # refait tout
    python -m app.voix.generer_clips --dynamiques    # ajoute les phrases de prix (faux prix)
"""
import csv
import json
import sys
from pathlib import Path

from app.dialogue import textes_fr as T
from app.voix.piper_tts import PiperTTS

CSV_PATH = Path(__file__).with_name("phrases.csv")


def ecrire_csv(chemin=CSV_PATH):
    """phrases.csv : liste lisible par l'équipe (colonne vide pour l'écoute)."""
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["identifiant", "texte", "clip_ok"])
        for identifiant, texte in T.TEXTES.items():
            w.writerow([identifiant, texte, ""])


def generer(tts, force=False):
    """Génère les clips manquants ou modifiés. Renvoie (générés, ignorés)."""
    tts.dossier_clips.mkdir(parents=True, exist_ok=True)
    manifeste_chemin = tts.dossier_clips / "manifest.json"
    manifeste = {}
    if manifeste_chemin.exists():
        manifeste = json.loads(manifeste_chemin.read_text(encoding="utf-8"))
    generes = ignores = 0
    for identifiant, texte in T.TEXTES.items():
        chemin = tts.dossier_clips / f"{identifiant}.wav"
        empreinte = tts.empreinte(texte)
        if not force and chemin.exists() and manifeste.get(identifiant) == empreinte:
            ignores += 1
            continue
        tts.synthetiser_vers(texte, chemin)
        manifeste[identifiant] = empreinte
        generes += 1
    manifeste_chemin.write_text(json.dumps(manifeste, indent=1), encoding="utf-8")
    ecrire_csv()
    return generes, ignores


def phrases_dynamiques_demo():
    """Phrases de prix construites avec les faux prix (pour tester le cache)."""
    from tests.fakes import PRIX
    textes = []
    for produit, liste in PRIX.items():
        textes.append(T.phrase_entete_prix(produit))
        textes += [T.phrase_marche(p) for p in liste]
        textes.append(T.phrase_cent_kilos(liste[0]))
    return textes


def main():
    tts = PiperTTS()
    generes, ignores = generer(tts, force="--force" in sys.argv)
    print(f"clips générés : {generes}, déjà à jour : {ignores}")
    print(f"dossier : {tts.dossier_clips}")
    if "--dynamiques" in sys.argv:
        textes = phrases_dynamiques_demo()
        for t in textes:
            tts.fichier_dynamique(t)
        print(f"phrases de prix prêtes : {len(textes)}")


if __name__ == "__main__":
    main()

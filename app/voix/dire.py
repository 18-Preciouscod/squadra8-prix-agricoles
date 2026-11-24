"""Dire une phrase et l'écouter : python -m app.voix.dire "Bonjour" """
import os
import sys

from app.voix.piper_tts import PiperTTS


def main():
    texte = " ".join(sys.argv[1:]) or "Bonjour. Ici le service des prix agricoles."
    chemin = PiperTTS().fichier_dynamique(texte)
    print(chemin)
    if hasattr(os, "startfile"):  # Windows
        os.startfile(chemin)


if __name__ == "__main__":
    main()

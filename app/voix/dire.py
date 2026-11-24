"""Dire une phrase et l'écouter : python -m app.voix.dire "Bonjour" """

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from app.voix.piper_tts import PiperTTS


def _ecouter(chemin: str) -> None:
    if hasattr(os, "startfile"):  # Windows
        os.startfile(chemin)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin" and shutil.which("afplay"):
        subprocess.run(["afplay", chemin], check=False)
        return
    if shutil.which("aplay"):
        subprocess.run(["aplay", chemin], check=False)


def main() -> None:
    texte = " ".join(sys.argv[1:]) or "Bonjour. Ici le service des prix agricoles."
    chemin = PiperTTS().fichier_dynamique(texte)
    print(chemin)
    _ecouter(str(chemin))


if __name__ == "__main__":
    main()

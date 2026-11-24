"""Voix Piper : synthèse, cache et ajout des URL audio aux Tours.

Tous les fichiers audio (phrases fixes et phrases dynamiques) vont dans un seul
dossier, voix/clips, qui sera servi sous /audio par l'application.
"""
import hashlib
import os
import threading
import wave
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def _chemin(variable, defaut):
    valeur = os.getenv(variable)
    if not valeur:
        return defaut
    p = Path(valeur)
    return p if p.is_absolute() else RACINE / p


class PiperTTS:
    def __init__(self, dossier_voix=None, nom_voix=None, dossier_clips=None):
        self.dossier_voix = Path(dossier_voix) if dossier_voix else _chemin(
            "PIPER_VOIX_DIR", RACINE / "models" / "piper")
        self.nom_voix = nom_voix or os.getenv("PIPER_VOIX", "fr_FR-siwis-medium")
        # Vitesse de parole : plus la valeur est grande, plus la voix est lente.
        # 1.0 = vitesse d'origine ; 1.25 = environ 20 % plus lent.
        self.longueur = float(os.getenv("PIPER_LONGUEUR", "1.25"))
        self.dossier_clips = Path(dossier_clips) if dossier_clips else _chemin(
            "VOIX_CLIPS_DIR", RACINE / "voix" / "clips")
        self._voix = None
        self._verrou = threading.Lock()

    # ---------- synthèse réelle ----------
    def _charger(self):
        if self._voix is None:
            from piper import (
                PiperVoice,  # import tardif : les tests n'en ont pas besoin
            )
            modele = self.dossier_voix / f"{self.nom_voix}.onnx"
            if not modele.exists():
                raise FileNotFoundError(
                    f"Voix Piper introuvable : {modele}. "
                    "Télécharger : python -m piper.download_voices " + self.nom_voix)
            self._voix = PiperVoice.load(str(modele))

    def synthetiser_vers(self, texte, chemin):
        """Écrit le texte parlé dans chemin (.wav). Écriture atomique."""
        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        with self._verrou:
            self._charger()
            tmp = chemin.with_suffix(".tmp")
            with wave.open(str(tmp), "wb") as wav:
                self._voix.synthesize_wav(texte, wav, syn_config=self._config())
            os.replace(tmp, chemin)

    def _config(self):
        from piper import SynthesisConfig
        return SynthesisConfig(length_scale=self.longueur)

    # ---------- cache ----------
    def empreinte(self, texte):
        """Change si le texte, la voix ou la vitesse changent (clips alors refaits)."""
        brut = f"{self.nom_voix}|{self.longueur}|{texte}".encode()
        return hashlib.sha1(brut).hexdigest()[:16]

    def fichier_dynamique(self, texte):
        """Fichier audio d'une phrase calculée ; synthétisé une seule fois."""
        chemin = self.dossier_clips / f"DYN-{self.empreinte(texte)}.wav"
        if not chemin.exists():
            self.synthetiser_vers(texte, chemin)
        return chemin

    def url_dynamique(self, texte):
        return f"/audio/{self.fichier_dynamique(texte).name}"


def ajouter_audio(tour, tts):
    """Renvoie le Tour avec une URL audio pour chaque phrase qui n'en a pas."""
    phrases = []
    for p in tour.phrases:
        if p.audio is None:
            p = p.model_copy(update={"audio": tts.url_dynamique(p.texte)})
        phrases.append(p)
    return tour.model_copy(update={"phrases": phrases})

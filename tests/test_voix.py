import csv
import time
import wave
from pathlib import Path

import pytest

from app.dialogue import textes_fr as T
from app.dialogue.moteur import Evenement, Moteur, Phrase, Tour
from app.voix import generer_clips
from app.voix.piper_tts import PiperTTS, ajouter_audio
from tests.fakes import services_fakes


class TTSFactice(PiperTTS):
    """Écrit un silence d'une seconde au lieu d'appeler Piper."""

    def __init__(self, dossier):
        super().__init__(dossier_voix=dossier, dossier_clips=dossier / "clips")
        self.appels = 0

    def synthetiser_vers(self, texte, chemin):
        self.appels += 1
        Path(chemin).parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(chemin), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b"\x00\x00" * 16000)


@pytest.fixture
def tts(tmp_path, monkeypatch):
    monkeypatch.setattr(generer_clips, "CSV_PATH", tmp_path / "phrases.csv")
    return TTSFactice(tmp_path)


def test_un_clip_par_phrase_fixe(tts):
    generes, _ = generer_clips.generer(tts)
    fichiers = sorted(tts.dossier_clips.glob("*.wav"))
    assert generes == len(T.TEXTES) == len(fichiers)
    for f in fichiers:
        with wave.open(str(f)) as w:
            assert w.getnframes() / w.getframerate() > 0.5


def test_csv_coherent_avec_textes(tts, tmp_path):
    chemin = tmp_path / "phrases.csv"
    generer_clips.ecrire_csv(chemin)
    with open(chemin, encoding="utf-8-sig") as f:
        ids = [ligne["identifiant"] for ligne in csv.DictReader(f, delimiter=";")]
    assert ids == list(T.TEXTES)


def test_clips_deja_a_jour_ne_sont_pas_refaits(tts):
    generer_clips.generer(tts)
    appels = tts.appels
    generes, ignores = generer_clips.generer(tts)
    assert generes == 0 and ignores == len(T.TEXTES) and tts.appels == appels


def test_phrase_modifiee_est_regeneree(tts, monkeypatch):
    generer_clips.generer(tts)
    monkeypatch.setitem(T.TEXTES, "F01", "Merci. À bientôt.")
    generes, _ = generer_clips.generer(tts)
    assert generes == 1


def test_force_refait_tout(tts):
    generer_clips.generer(tts)
    generes, _ = generer_clips.generer(tts, force=True)
    assert generes == len(T.TEXTES)


def test_cache_dynamique(tts):
    a = tts.fichier_dynamique("Bohicon : cent trente-sept francs.")
    b = tts.fichier_dynamique("Bohicon : cent trente-sept francs.")
    assert a == b and tts.appels == 1
    tts.fichier_dynamique("Autre phrase.")
    assert tts.appels == 2


def test_empreinte_depend_du_texte_et_de_la_voix(tts):
    assert tts.empreinte("a") == tts.empreinte("a")
    assert tts.empreinte("a") != tts.empreinte("b")
    autre = TTSFactice(tts.dossier_voix)
    autre.nom_voix = "autre_voix"
    assert tts.empreinte("a") != autre.empreinte("a")


def test_empreinte_depend_de_la_vitesse(tts):
    avant = tts.empreinte("a")
    tts.longueur = 1.5
    assert tts.empreinte("a") != avant


def test_ajouter_audio_complete_les_phrases_calculees(tts):
    tour = Tour(etat="X", attente="touche", phrases=[
        Phrase(id="R01", texte="fixe", audio="/audio/R01.wav"),
        Phrase(id="DYN", texte="calculée"),
    ])
    habille = ajouter_audio(tour, tts)
    assert habille.phrases[0].audio == "/audio/R01.wav"
    assert habille.phrases[1].audio.startswith("/audio/DYN-")
    assert (tts.dossier_clips / habille.phrases[1].audio.split("/")[-1]).exists()


def test_parcours_complet_avec_audio(tts):
    moteur = Moteur(services_fakes())
    sess = moteur.nouvelle_session("t")
    moteur.traiter(sess, Evenement(type="DECROCHE"))
    tour = moteur.traiter(sess, Evenement(type="TOUCHE", valeur="1"))
    tour = moteur.traiter(sess, Evenement(type="TOUCHE", valeur="1"))
    tour = ajouter_audio(tour, tts)
    assert all(p.audio for p in tour.phrases)


MODELE = Path("models/piper/fr_FR-siwis-medium.onnx")


@pytest.mark.skipif(not MODELE.exists(), reason="voix Piper non téléchargée")
def test_vitesse_reelle(tmp_path):
    vraie = PiperTTS(dossier_clips=tmp_path)
    vraie.fichier_dynamique("Chauffe.")  # chargement de la voix, non mesuré
    t = time.perf_counter()
    vraie.fichier_dynamique("Combien le maïs à Bohicon ?")
    duree = time.perf_counter() - t
    print(f"synthèse : {duree:.2f} s")
    assert duree < 1.5  # objectif du plan : 1 s ; marge pour un petit processeur

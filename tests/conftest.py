"""Configuration pytest : pas d'appel FAO réel pendant les tests."""

from __future__ import annotations

import os
from pathlib import Path

# Avant tout import de l'app : désactiver la maj FAO au démarrage.
os.environ["MAJ_FAO_AU_DEMARRAGE"] = "false"

# CSV d'exemple versionné (pas le vrai data/raw/prix_fao.csv).
_CSV_EXEMPLE = Path(__file__).resolve().parent / "donnees" / "prix_fao_exemple.csv"
os.environ.setdefault("SOURCE_PRIX", "fao")
os.environ.setdefault("PRIX_FAO_CSV", str(_CSV_EXEMPLE))


def pytest_configure() -> None:
    """Vide les caches si l'environnement a changé."""
    try:
        from app.config import get_settings

        get_settings.cache_clear()
    except Exception:  # noqa: BLE001 — import optionnel au tout début
        pass
    try:
        from app.services.source_prix import get_source_prix

        get_source_prix.cache_clear()
    except Exception:  # noqa: BLE001
        pass

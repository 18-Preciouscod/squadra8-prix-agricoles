"""Source des prix pour la touche 1 (plan B : CSV FAO, puis base).

Aucun prix inventé. Chaque prix porte sa date de relevé.
"""

from __future__ import annotations

import csv
import logging
import unicodedata
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.ia.anomalies import analyser_prix
from app.services.calculs import arrondir_f, vers_100kg
from data.scripts.maj_fao import MARCHES_MVP, PRODUITS_MVP

logger = logging.getLogger(__name__)

# Ordre stable pour prix_du_jour (frozenset MARCHES_MVP n'a pas d'ordre).
ORDRE_MARCHES = (
    "Bohicon",
    "Houndjro (Abomey)",
    "Azogotchébou (Covè)",
)

# Alias d'entrée → nom FAO exact (après normalisation sans accents / casse).
_ALIAS_PRODUITS: dict[str, str] = {
    "mais": "Maïs Blanc",
    "mais blanc": "Maïs Blanc",
    "mais jaune": "Maïs Jaune",
    "soja": "Soja",
    "haricot": "Haricot blanc",
    "haricot blanc": "Haricot blanc",
    "haricot noir": "Haricot noir",
    "haricot rouge": "Haricot rouge",
}


def _sans_accents(texte: str) -> str:
    decomp = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decomp if unicodedata.category(c) != "Mn")


def normaliser_cle(texte: str) -> str:
    return " ".join(_sans_accents(texte).casefold().split())


def resoudre_produit(produit: str) -> str | None:
    """Retourne le nom FAO exact, ou None si inconnu."""
    brut = (produit or "").strip()
    if not brut:
        return None
    if brut in PRODUITS_MVP:
        return brut
    return _ALIAS_PRODUITS.get(normaliser_cle(brut))


def resoudre_marche(marche: str) -> str | None:
    """Marché MVP exact uniquement — aucun alias (pas d'Abomey → Houndjro)."""
    brut = (marche or "").strip()
    if brut in MARCHES_MVP:
        return brut
    return None


def _formater_prix(ligne: dict[str, Any]) -> dict[str, Any]:
    prix_kg = float(ligne["prix"])
    return {
        "produit": ligne["produit"],
        "marche": ligne["marche"],
        "prix_kg": prix_kg,
        "prix_fcfa": prix_kg,
        "prix_100kg": vers_100kg(prix_kg),
        "prix_kg_annonce": arrondir_f(prix_kg),
        "date_releve": ligne["date"],
        "source": ligne.get("source") or "",
        "unite": ligne.get("unite") or "",
        "type_prix": ligne.get("type") or "",
        "devise": ligne.get("devise") or "",
    }


class SourcePrix(ABC):
    """Interface commune FAO / base."""

    @abstractmethod
    def dernier_prix(self, produit: str, marche: str) -> dict | None:
        """Dernier prix « ok » pour un couple, ou None."""

    @abstractmethod
    def prix_du_jour(self, produit: str) -> list[dict]:
        """Prix disponibles par marché MVP (ordre stable), liste vide si aucun."""


class SourceBaseNonPrete(SourcePrix):
    """Placeholder tant que SQLAlchemy n'a pas de table Prix."""

    def dernier_prix(self, produit: str, marche: str) -> dict | None:
        raise RuntimeError("base non prête : SOURCE_PRIX=base sans table Prix")

    def prix_du_jour(self, produit: str) -> list[dict]:
        raise RuntimeError("base non prête : SOURCE_PRIX=base sans table Prix")


class SourceFaoCsv(SourcePrix):
    """Lit data/raw/prix_fao.csv (ou PRIX_FAO_CSV), filtre anomalies."""

    def __init__(self, chemin: str | Path | None = None) -> None:
        settings = get_settings()
        self._chemin = Path(chemin) if chemin else Path(settings.prix_fao_csv)
        self._lignes: list[dict[str, str]] = []
        self._signature: tuple[float, int] | None = None
        self._charger_si_besoin()

    def _signature_fichier(self) -> tuple[float, int] | None:
        if not self._chemin.is_file():
            return None
        st = self._chemin.stat()
        return (st.st_mtime, st.st_size)

    def _charger_si_besoin(self) -> None:
        sig = self._signature_fichier()
        if sig == self._signature:
            return
        self._signature = sig
        self._lignes = []
        if sig is None:
            logger.warning("CSV FAO absent ou inaccessible : %s", self._chemin)
            return
        try:
            with self._chemin.open("r", encoding="utf-8-sig", newline="") as f:
                lecteur = csv.DictReader(f)
                for row in lecteur:
                    self._lignes.append({k: (row.get(k) or "").strip() for k in (lecteur.fieldnames or [])})
        except OSError as exc:
            logger.warning("CSV FAO illisible (%s) : %s", self._chemin, exc)
            self._lignes = []
            self._signature = None

    def _lignes_mvp_detail(self) -> list[dict[str, Any]]:
        self._charger_si_besoin()
        retenues: list[dict[str, Any]] = []
        for row in self._lignes:
            produit = row.get("produit") or ""
            marche = row.get("marche") or ""
            if produit not in PRODUITS_MVP or marche not in MARCHES_MVP:
                continue
            type_prix = (row.get("type") or "").strip().casefold()
            # MVP : uniquement le détail (libellé CSV « detail »).
            if type_prix and type_prix not in {"detail", "détail", "retail"}:
                continue
            date = (row.get("date") or "").strip()[:10]
            if not date:
                continue
            brut = row.get("prix")
            if brut is None or str(brut).strip() == "":
                continue
            try:
                prix = float(str(brut).replace(",", "."))
            except ValueError:
                continue
            retenues.append(
                {
                    "produit": produit,
                    "marche": marche,
                    "date": date,
                    "prix": prix,
                    "unite": row.get("unite") or "",
                    "source": row.get("source") or "",
                    "type": row.get("type") or "detail",
                    "devise": row.get("devise") or "",
                }
            )
        return retenues

    def _dernier_ok(self, produit_fao: str, marche_fao: str) -> dict[str, Any] | None:
        toutes = self._lignes_mvp_detail()
        couple = [r for r in toutes if r["produit"] == produit_fao and r["marche"] == marche_fao]
        if not couple:
            return None
        couple.sort(key=lambda r: r["date"])

        voisins_bruts = [
            {"date": r["date"], "prix": r["prix"], "marche": r["marche"]}
            for r in toutes
            if r["produit"] == produit_fao and r["marche"] != marche_fao
        ]

        historique_ok: list[dict[str, Any]] = []
        retenu: dict[str, Any] | None = None

        for releve in couple:
            resultat = analyser_prix(
                produit=produit_fao,
                marche=marche_fao,
                date_prix=releve["date"],
                prix=float(releve["prix"]),
                unite=releve.get("unite") or None,
                historique=historique_ok,
                voisins=voisins_bruts,
            )
            if resultat.get("statut") == "ok":
                historique_ok.append(
                    {
                        "date": releve["date"],
                        "prix": float(releve["prix"]),
                        "valide": True,
                    }
                )
                retenu = releve
            # a_verifier : ignoré pour l'annonce (pas ajouté comme valide)

        return retenu

    def dernier_prix(self, produit: str, marche: str) -> dict | None:
        produit_fao = resoudre_produit(produit)
        marche_fao = resoudre_marche(marche) if marche else None
        if not produit_fao or not marche_fao:
            return None
        retenu = self._dernier_ok(produit_fao, marche_fao)
        if retenu is None:
            return None
        return _formater_prix(retenu)

    def prix_du_jour(self, produit: str) -> list[dict]:
        produit_fao = resoudre_produit(produit)
        if not produit_fao:
            return []
        resultats: list[dict] = []
        for marche in ORDRE_MARCHES:
            if marche not in MARCHES_MVP:
                continue
            prix = self.dernier_prix(produit_fao, marche)
            if prix is not None:
                resultats.append(prix)
        return resultats


@lru_cache
def get_source_prix() -> SourcePrix:
    """Fabrique la source selon SOURCE_PRIX (cache vidable)."""
    settings = get_settings()
    choix = (settings.source_prix or "fao").strip().casefold()
    if choix in {"fao", "csv"}:
        return SourceFaoCsv(settings.prix_fao_csv)
    if choix in {"base", "db", "sql"}:
        return SourceBaseNonPrete()
    raise ValueError(f"SOURCE_PRIX inconnu : {settings.source_prix!r} (attendu : fao | base)")

"""Comprend l'intention via Groq (JSON strict). Jamais de prix.

Responsable : Gopal.

Règle : l'IA comprend seulement (intention, produit, marché).
Les prix viennent ensuite de la base, jamais du modèle.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.config import get_settings
from app.ia.regles import comprendre_par_regles

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 3.0
Intentions = Literal["prix", "juger_offre", "autre", "inconnu"]

SYSTEM_PROMPT = """Tu analyses une phrase d'un producteur agricole du Bénin (département du Zou).
Tu renvoies UNIQUEMENT un objet JSON valide, sans markdown, avec exactement ces clés :
- intention : "prix" | "juger_offre" | "autre" | "inconnu"
- produit : code parmi "mais", "soja", "haricot", ou null si absent / flou
- marche : code parmi "bohicon", "abomey", "cove", ou null si absent / flou
- confiance : nombre entre 0 et 1

Interdits : ne donne jamais de prix, de montant, de devise, ni de conseil d'achat/vente.
Si la demande est hors sujet, intention = "autre".
Si tu ne comprends pas, intention = "inconnu".
"""


class IntentionResult(BaseModel):
    """Sortie structurée : compréhension seule, aucun prix."""

    intention: Intentions
    produit: str | None = None
    marche: str | None = None
    confiance: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Literal["groq", "regles"] = "groq"

    @field_validator("produit", "marche", mode="before")
    @classmethod
    def _vide_vers_none(cls, value: Any) -> Any:
        if value is None:
            return None
        text = str(value).strip().lower()
        return text or None


def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )


def _extraire_json(texte: str) -> dict[str, Any]:
    """Récupère un objet JSON même s'il est entouré de texte parasite."""
    texte = texte.strip()
    try:
        data = json.loads(texte)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", texte, flags=re.DOTALL)
    if not match:
        raise ValueError("pas de JSON dans la réponse du modèle")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("JSON non objet")
    return data


def _appeler_groq(texte: str) -> IntentionResult:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY / GROQ_API_KEY manquante")

    options: dict[str, Any] = {}
    if settings.llm_reasoning_effort:
        options["reasoning_effort"] = settings.llm_reasoning_effort

    response = _client().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texte.strip()},
        ],
        temperature=0,
        max_tokens=400,
        **options,
    )
    brut = (response.choices[0].message.content or "").strip()
    data = _extraire_json(brut)
    # Sécurité : si le modèle glisse un prix, on l'ignore (clés non prévues).
    data.pop("prix", None)
    data.pop("montant", None)
    data.pop("price", None)
    return IntentionResult.model_validate({**data, "source": "groq"})


def comprendre(texte: str) -> dict:
    """Retourne l'intention, le produit et le marché, sans aucun prix.

    Essaie Groq ; en cas d'erreur, délai ou JSON invalide → règles de secours.
    """
    texte = (texte or "").strip()
    if not texte:
        return IntentionResult(
            intention="inconnu",
            produit=None,
            marche=None,
            confiance=0.0,
            source="regles",
        ).model_dump()

    try:
        return _appeler_groq(texte).model_dump()
    except (OpenAIError, ValidationError, ValueError, RuntimeError, TimeoutError) as exc:
        logger.warning("Groq indisponible ou réponse invalide, repli sur règles : %s", exc)
        return comprendre_par_regles(texte)

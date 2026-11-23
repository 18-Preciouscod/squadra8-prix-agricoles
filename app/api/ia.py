"""Routes de l'IA (transcription et intention). L'IA ne renvoie jamais de prix.

Responsable : Gopal.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ia.intention import comprendre

router = APIRouter()


class IntentionIn(BaseModel):
    texte: str = Field(min_length=1, max_length=2000)


class IntentionOut(BaseModel):
    intention: str
    produit: str | None = None
    marche: str | None = None
    confiance: float
    source: str


@router.post("/intention", response_model=IntentionOut)
def post_intention(body: IntentionIn) -> IntentionOut:
    """Comprend l'intention (Groq → Gemini → règles). Aucun prix dans la réponse."""
    resultat = comprendre(body.texte)
    # Ceinture : retirer toute clé de prix si un jour elle apparaissait.
    resultat.pop("prix", None)
    resultat.pop("montant", None)
    return IntentionOut.model_validate(resultat)


# TODO : POST /transcrire (contrat 5.3, Guillaume).

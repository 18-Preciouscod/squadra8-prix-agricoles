"""Routes publiques de consultation des prix."""
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from app.services.prix_service import prix_du_jour

router = APIRouter()


@router.get("/prix")
def consulter_prix(
    produit: str = Query(..., pattern="^(mais|soja|haricot)$"),
    date_reference: date | None = None,
):
    """Ne publie que les prix de détail au kilo validés et âgés de 60 jours maximum."""
    try:
        lignes = prix_du_jour(produit, date_reference=date_reference)
    except Exception:
        raise HTTPException(503, "Service des prix temporairement indisponible.") from None
    return {
        "produit": produit,
        "date_reference": (date_reference or date.today()).isoformat(),
        "fraicheur_max_jours": 60,
        "prix": lignes,
        "message": None if lignes else "Aucun prix validé et suffisamment récent n'est disponible.",
    }

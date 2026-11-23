"""Démarre FastAPI et branche les routes.

Responsable : Gopal.
"""

from fastapi import FastAPI

from app.api import admin, ia, prix, sim, twilio
from app.config import get_settings

app = FastAPI(
    title="Squadra 8 – Prix agricoles",
    description="Service téléphonique de prix agricoles pour les producteurs du Zou.",
    version="0.1.0",
)
app.state.settings = get_settings()

app.include_router(sim.router, prefix="/api/sim", tags=["simulateur"])
app.include_router(prix.router, prefix="/api", tags=["prix"])
app.include_router(ia.router, prefix="/api/ia", tags=["ia"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(twilio.router, prefix="/twilio", tags=["twilio"])


@app.get("/sante")
def sante() -> dict[str, str]:
    """Indique que l'application répond."""
    return {"statut": "ok"}


@app.get("/health")
def health() -> dict[str, bool]:
    """Même chose que /sante, au format prévu par le plan (/health → {"ok": true})."""
    return {"ok": True}

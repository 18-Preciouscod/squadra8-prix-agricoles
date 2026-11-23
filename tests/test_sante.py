"""Vérifie que l'application démarre et répond."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sante() -> None:
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_health() -> None:
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"ok": True}

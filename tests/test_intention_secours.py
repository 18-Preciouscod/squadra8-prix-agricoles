"""Chaîne de secours Groq → Gemini → règles, sans appels réseau."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.config import get_settings
from app.ia.intention import IntentionResult, comprendre


@pytest.fixture(autouse=True)
def _vider_cache_settings() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _reponse_llm(contenu: str) -> MagicMock:
    message = SimpleNamespace(content=contenu)
    choice = SimpleNamespace(message=message)
    return MagicMock(choices=[choice])


JSON_PRIX_MAIS = (
    '{"intention":"prix","produit":"mais","marche":"bohicon","confiance":0.9}'
)


def test_groq_ok_source_groq() -> None:
    with (
        patch("app.ia.intention.get_settings") as mock_settings,
        patch("app.ia.intention.OpenAI") as mock_openai,
    ):
        mock_settings.return_value = SimpleNamespace(
            openai_api_key="gsk_test",
            openai_base_url="https://api.groq.com/openai/v1",
            openai_model="openai/gpt-oss-120b",
            llm_reasoning_effort=None,
            gemini_api_key="gemini-test",
            gemini_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            gemini_model="gemini-3.5-flash-lite",
        )
        client = mock_openai.return_value
        client.chat.completions.create.return_value = _reponse_llm(JSON_PRIX_MAIS)

        resultat = comprendre("prix du maïs à Bohicon")

    assert resultat["source"] == "groq"
    assert resultat["intention"] == "prix"
    assert resultat["produit"] == "mais"
    assert resultat["marche"] == "bohicon"
    assert "prix" not in resultat


def test_groq_ko_gemini_ok_source_gemini() -> None:
    with (
        patch("app.ia.intention.get_settings") as mock_settings,
        patch("app.ia.intention._appeler_groq", side_effect=RuntimeError("groq down")),
        patch("app.ia.intention.OpenAI") as mock_openai,
    ):
        mock_settings.return_value = SimpleNamespace(
            openai_api_key="gsk_test",
            openai_base_url="https://api.groq.com/openai/v1",
            openai_model="openai/gpt-oss-120b",
            llm_reasoning_effort=None,
            gemini_api_key="gemini-test",
            gemini_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            gemini_model="gemini-3.5-flash-lite",
        )
        client = mock_openai.return_value
        client.chat.completions.create.return_value = _reponse_llm(JSON_PRIX_MAIS)

        resultat = comprendre("prix du maïs à Bohicon")

    assert resultat["source"] == "gemini"
    assert resultat["intention"] == "prix"
    assert resultat["produit"] == "mais"


def test_groq_ko_gemini_ko_source_regles() -> None:
    with (
        patch("app.ia.intention.get_settings") as mock_settings,
        patch("app.ia.intention._appeler_groq", side_effect=RuntimeError("groq down")),
        patch("app.ia.intention._appeler_gemini", side_effect=RuntimeError("gemini down")),
    ):
        mock_settings.return_value = SimpleNamespace(
            openai_api_key="gsk_test",
            gemini_api_key="gemini-test",
        )
        resultat = comprendre("prix du maïs à Bohicon")

    assert resultat["source"] == "regles"
    assert resultat["intention"] == "prix"
    assert resultat["produit"] == "mais"
    assert resultat["marche"] == "bohicon"


def test_groq_ko_sans_cle_gemini_source_regles() -> None:
    with (
        patch("app.ia.intention.get_settings") as mock_settings,
        patch("app.ia.intention._appeler_groq", side_effect=RuntimeError("groq down")),
        patch("app.ia.intention._appeler_gemini") as mock_gemini,
    ):
        mock_settings.return_value = SimpleNamespace(
            openai_api_key="gsk_test",
            gemini_api_key="",
        )
        resultat = comprendre("prix du soja à Abomey")

    mock_gemini.assert_not_called()
    assert resultat["source"] == "regles"
    assert resultat["intention"] == "prix"
    assert resultat["produit"] == "soja"
    assert resultat["marche"] == "abomey"


def test_intention_result_accepte_source_gemini() -> None:
    r = IntentionResult(
        intention="autre",
        produit=None,
        marche=None,
        confiance=0.5,
        source="gemini",
    )
    assert r.source == "gemini"

"""Lit les variables d'environnement (fichier .env).

Responsable : Gopal.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application, lus depuis l'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://squadra8:squadra8@localhost:5432/prix_agricoles"
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4.1-mini"
    fernet_key: str = ""
    hash_pepper: str = ""
    admin_email: str = ""
    admin_password_initial: str = ""
    question_voix_active: bool = True
    whisper_modele: str = "small"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""


@lru_cache
def get_settings() -> Settings:
    """Retourne les paramètres (lus une seule fois)."""
    return Settings()

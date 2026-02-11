"""
Application configuration.

Responsibility:
    Centralizes all application settings using pydantic-settings.
    Environment variables and .env files are loaded here.
    Other modules import `settings` from this module instead of
    reading env vars directly — single source of truth.

Future extension points:
    - Add AI provider API keys (e.g. OPENAI_API_KEY)
    - Add model selection settings (e.g. MODEL_NAME, TEMPERATURE)
    - Add rate-limit / quota configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Immutable application settings populated from environment variables."""

    APP_NAME: str = "Anki AI Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Future: AI provider settings will go here
    # OPENAI_API_KEY: str = ""
    # MODEL_NAME: str = "gpt-4"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

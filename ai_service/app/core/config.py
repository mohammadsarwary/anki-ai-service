"""
Application configuration.

Responsibility:
    Centralizes all application settings using pydantic-settings.
    Environment variables and .env files are loaded here.
    Other modules import `settings` from this module instead of
    reading env vars directly - single source of truth.

Future extension points:
    - Add AI provider API keys (e.g. OPENAI_API_KEY)
    - Add model selection settings (e.g. MODEL_NAME, TEMPERATURE)
    - Add rate-limit / quota configuration
"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Immutable application settings populated from environment variables."""

    APP_NAME: str = "Anki AI Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # AI Provider Selection
    AI_PROVIDER: str = "openrouter"  # "openrouter" or "google_gemini"

    # Google Gemini
    GOOGLE_API_KEY: str = "AIzaSyBPl8iUuzfB8saYFk-Rlmb3f7oZhdzbt6s"
    GOOGLE_GEMINI_MODEL: str = "gemini-3-flash-preview"

    # Cerebras settings
    CEREBRAS_API_KEY: str = "csk-2m9wdwmvewn64xerppct8pfre9wrx2vpmthw28t3rvntx2y5"
    CEREBRAS_MODEL: str = "llama3.1-8b"
    CEREBRAS_BASE_URL: str = "https://api.cerebras.ai/v1"

    # Backward-compatible aliases for renamed settings (legacy OPENROUTER_* env vars)
    CEREBRAS_MAX_TOKENS: int = Field(
        default=2000,
        validation_alias=AliasChoices("CEREBRAS_MAX_TOKENS", "OPENROUTER_MAX_TOKENS"),
    )
    CEREBRAS_REFERER: str = Field(
        default="https://www.youtube.com/",
        validation_alias=AliasChoices("CEREBRAS_REFERER", "OPENROUTER_REFERER"),
    )
    CEREBRAS_SITE_TITLE: str = Field(
        default="anki-ai",
        validation_alias=AliasChoices("CEREBRAS_SITE_TITLE", "OPENROUTER_SITE_TITLE"),
    )

    LARAVEL_API_URL: str = "http://anki-ai-backend.test"
    LARAVEL_TIMEOUT: int = 5

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

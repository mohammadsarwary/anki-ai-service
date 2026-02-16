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

    LARAVEL_API_URL: str = "http://anki-ai-backend.test"  
    LARAVEL_TIMEOUT: int = 5
    OPENROUTER_API_KEY: str = "sk-MKjxNYeNmqRgW6iO6VlX78agSCmM89HjcqLT8SbyCCAMUd7c"  # کلید API
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"  # URL پایه
    OPENROUTER_MODEL: str = "deepseek-r1-0528"  # نام مدل
    OPENROUTER_MAX_TOKENS: int = 2000  # حداکثر توکن‌ها
    OPENROUTER_REFERER: str = "https://www.youtube.com/"  # برای HTTP-Referer header
    OPENROUTER_SITE_TITLE: str = "anki-ai"  # برای X-Title header

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

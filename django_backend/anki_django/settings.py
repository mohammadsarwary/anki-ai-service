"""Django settings for the Anki AI migration backend."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    DAILY_AI_LIMIT=(int, 100),
)
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-only-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "testserver"])

INSTALLED_APPS = []
if importlib.util.find_spec("unfold"):
    INSTALLED_APPS.extend(["unfold", "unfold.contrib.filters"])

INSTALLED_APPS.extend(
    [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "rest_framework",
        "corsheaders",
        "apps.accounts",
        "apps.decks",
        "apps.reviews",
        "apps.ai",
        "apps.practice",
        "apps.gamification",
        "apps.sync",
        "apps.admin_panel",
    ]
)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "anki_django.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "anki_django.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default=""),
        "PORT": env("DB_PORT", default=""),
        "OPTIONS": {},
    }
}
if DATABASES["default"]["ENGINE"].endswith("mysql"):
    DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.EmailOrLaravelBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "apps.accounts.hashers.LaravelBcryptPasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.BearerTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "anki_django.exceptions.api_exception_handler",
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)

AI_PROVIDER = env("AI_PROVIDER", default="cerebras")
CEREBRAS_API_KEY = env("CEREBRAS_API_KEY", default=env("OPENROUTER_API_KEY", default=""))
CEREBRAS_BASE_URL = env("CEREBRAS_BASE_URL", default=env("OPENROUTER_BASE_URL", default="https://api.cerebras.ai/v1"))
CEREBRAS_MODEL = env("CEREBRAS_MODEL", default=env("OPENROUTER_MODEL", default="llama3.1-8b"))
CEREBRAS_MAX_TOKENS = env.int("CEREBRAS_MAX_TOKENS", default=env.int("OPENROUTER_MAX_TOKENS", default=2000))
CEREBRAS_REFERER = env("CEREBRAS_REFERER", default=env("OPENROUTER_REFERER", default="https://example.com"))
CEREBRAS_SITE_TITLE = env("CEREBRAS_SITE_TITLE", default=env("OPENROUTER_SITE_TITLE", default="anki-ai"))
DAILY_AI_LIMIT = env("DAILY_AI_LIMIT")

UNFOLD = {
    "SITE_TITLE": "Anki AI Admin",
    "SITE_HEADER": "Anki AI",
    "SITE_SUBHEADER": "Learning, AI, and operations",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
}

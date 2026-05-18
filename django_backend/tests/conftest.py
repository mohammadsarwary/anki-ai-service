import pytest
from rest_framework.test import APIClient

from apps.accounts.models import AuthToken, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="password123", name="User")


@pytest.fixture
def auth_client(api_client, user):
    _token, raw = AuthToken.issue(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
    return api_client


@pytest.fixture
def generated_card():
    return {
        "front": "ephemeral",
        "difficulty": "medium",
        "back": {
            "definition": "lasting for a short time",
            "pronunciation": {"text": "ih-FEM-er-uhl", "hint": "stress second syllable", "tts": {"text": "ephemeral", "lang": "en"}},
            "part_of_speech": "adjective",
            "usage": "Used for temporary things",
            "examples": [{"text": "The moment was ephemeral.", "tts": None}],
            "memory_tip": "Think of a short-lived event",
        },
    }

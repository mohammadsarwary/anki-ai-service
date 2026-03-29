import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.deps import get_current_user

@pytest.fixture
def client():
    """Test client for API tests."""
    app.dependency_overrides[get_current_user] = lambda: {"user_id": 1}
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()



@pytest.fixture
def mock_card_response():
    """Mock response from AI provider."""
    return {
        "front": "ephemeral",
        "difficulty": "medium",
        "back": {
            "definition": "lasting for a short time",
            "pronunciation": {
                "text": "ih-FEM-er-uhl",
                "hint": "stress on second syllable",
                "tts": {"text": "ephemeral", "lang": "en"}
            },
            "part_of_speech": "adjective",
            "usage": "Used to describe temporary things",
            "examples": [
                {"text": "The ephemeral beauty...", "tts": None}
            ],
            "memory_tip": "Think of cherry blossoms"
        }
    }

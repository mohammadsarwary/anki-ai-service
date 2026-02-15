import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client for API tests."""
    return TestClient(app)



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
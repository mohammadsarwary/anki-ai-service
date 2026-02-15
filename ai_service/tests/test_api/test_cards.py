import pytest
from unittest.mock import patch, AsyncMock
from app.models.request import Level

def test_generate_card_success(client, mock_card_response):
    with patch(
        "app.services.card_generation_service.CardGenerationService.generate_card",
        new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = mock_card_response

        response = client.post("/api/v1/generate-flashcards", json={
            "term": "ephemeral",
            "level": "beginner",
        })
        assert response.status_code == 200
        assert response.json()["front"] == "ephemeral"
        

def test_generate_card_invalid_level(client):
    response = client.post("/api/v1/generate-flashcards", json={
        "term": "test",
        "level": "exper",
    })
    assert response.status_code == 422
    assert "validation_error" in response.json()["type"]

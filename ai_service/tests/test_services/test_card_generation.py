import pytest
from unittest.mock import patch,MagicMock
from app.services.card_generation_service import CardGenerationService
from app.core.exceptions import APIRateLimitError,APIProviderError
import openai
from app.models.request import Level  
from app.core.exceptions import InvalidResponseError 

@pytest.mark.asyncio
async def test_generate_card_rate_limit():
    service = CardGenerationService()
    with patch('app.services.card_generation_service.client') as mock_client:
        mock_client.chat.completions.create.side_effect = openai.RateLimitError(
            "Rate limit",
            response=MagicMock(),
            body={}
        )
        with pytest.raises(APIRateLimitError):
            await service.generate_card(
                term="test",
                language="en",
                target_language="fa",
                level="beginner"  
            )


@pytest.mark.asyncio
async def test_generate_card_json_parse_error():
    service = CardGenerationService()
    with patch("app.services.card_generation_service.client") as mock_client:
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="invalid json"))]
        )
        
        with pytest.raises(InvalidResponseError):
            await service.generate_card(
                term="test",
                language="en",
                target_language="fa",
                level="beginner"
            )
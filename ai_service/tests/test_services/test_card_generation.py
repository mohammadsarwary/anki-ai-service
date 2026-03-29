import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import APIRateLimitError, InvalidResponseError
from app.services.card_generation_service import CardGenerationService


@pytest.mark.asyncio
async def test_generate_card_delegates_to_provider_errors():
    service = CardGenerationService()
    service.provider = MagicMock()
    service.provider.generate_card = AsyncMock(side_effect=APIRateLimitError())

    with pytest.raises(APIRateLimitError):
        await service.generate_card(
            term="test",
            language="en",
            target_language="fa",
            level="beginner",
        )


@pytest.mark.asyncio
async def test_generate_card_invalid_response_bubbles_up():
    service = CardGenerationService()
    service.provider = MagicMock()
    service.provider.generate_card = AsyncMock(side_effect=InvalidResponseError())

    with pytest.raises(InvalidResponseError):
        await service.generate_card(
            term="test",
            language="en",
            target_language="fa",
            level="beginner",
        )

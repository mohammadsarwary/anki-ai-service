# app/services/card_generation_service.py
from app.providers import get_ai_provider
from app.models.response import CardGenerationResponse, CardGenerationFromTopicResponse

class CardGenerationService:
    """Service that delegates to AI providers."""
    
    def __init__(self):
        self.provider = get_ai_provider()
    
    async def generate_card(
        self, 
        term: str, 
        language: str, 
        target_language: str, 
        level: str
    ) -> CardGenerationResponse:
        return await self.provider.generate_card(term, language, target_language, level)
    
    async def generate_card_from_topic(
        self,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str
    ) -> CardGenerationFromTopicResponse:
        return await self.provider.generate_cards_from_topic(
            topic, count, level, language, target_language
        )

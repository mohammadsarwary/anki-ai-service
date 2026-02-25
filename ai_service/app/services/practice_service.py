from app.providers import get_ai_provider
from app.models.response import PracticeSentenceResponse

class PracticeService:
    """Service that delegates to AI providers."""
    
    def __init__(self):
        self.provider = get_ai_provider()
    
    async def generate_practice_sentence(
        self, 
        target_word: str, 
        user_sentence: str,
        language: str
    ) -> PracticeSentenceResponse:
        return await self.provider.generate_practice_sentence(
            target_word, user_sentence, language
        )
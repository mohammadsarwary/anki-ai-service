
from abc import ABC, abstractmethod
from app.models.response import CardGenerationResponse, CardGenerationFromTopicResponse,PracticeSentenceResponse


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_card(
        self, 
        term: str, 
        language: str,
        target_language: str,
        level: str,
    ) -> CardGenerationResponse:
        """Generate a single flashcard."""
        pass

    @abstractmethod
    async def generate_cards_from_topic(
        self,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str,
    ) -> CardGenerationFromTopicResponse:
        """Generate multiple flashcards from a topic."""
        pass

    @abstractmethod
    async def generate_practice_sentence(
        self, 
        target_word: str, 
        user_sentence: str,
        language: str
    ) -> PracticeSentenceResponse:
        """Generate a practice sentence."""
        pass
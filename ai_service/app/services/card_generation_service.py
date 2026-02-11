"""
Card generation service.

Responsibility:
    Encapsulates the business logic for generating flashcards.
    Route handlers delegate to this service — they never contain
    domain logic themselves.  This keeps the API layer thin and
    makes the core logic independently testable.

    Currently returns a **placeholder / mock** response.
    The real implementation will be injected here later
    (e.g. call to an LLM provider).

Future extension points:
    - Swap the mock with an actual AI provider call
    - Add caching (e.g. Redis) to avoid duplicate generations
    - Add retry / fallback logic for provider failures
    - Accept a pluggable "generator" strategy via dependency injection
"""

from turtle import back
from app.models.request import CardGenerationRequest
from app.models.response import CardBack, CardGenerationResponse
from app.utils.logger import logger


class CardGenerationService:
    

    async def generate_card(
        self,
        term:str,
        language:str,
        target_language:str,
        level:str, 
    ) :
        """
        Generate a flashcard for the given term.

        This is a placeholder implementation that returns mock data.
        Replace the body of this function with a real AI provider call
        when ready.
        """
        return {
            "front": term,
            "back": {
                "definition": "Temporary mock definition",
                "pronunciation": {
                    "text": "mock pronunciation",
                    "hint": None
                },
                "part_of_speech": ["noun"],
                "usage": "Mock usage explanation",
                "examples": {
                    "simple": "Simple example sentence.",
                    "natural": "Natural example sentence."
                },
                "memory_tip": "Mock memory tip"
            },
            "difficulty": "medium"
        }

       
"""
Request models.

Responsibility:
    Defines Pydantic schemas for incoming API request payloads.
    Validation, type coercion, and documentation happen here
    so that route handlers stay thin.

Future extension points:
    - Add optional fields (e.g. context, tags, deck_id)
    - Add custom validators (e.g. supported language codes)
    - Add batch generation request model
"""
from enum import Enum
from pydantic import BaseModel, Field


class Level(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
 
class CardGenerationRequest(BaseModel):
    """Payload for the card generation endpoint."""

    term: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The word or phrase to generate a flashcard for.",
        examples=["ephemeral"],
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=10,
        description="ISO language code of the source term.",
        examples=["en"],
    )
    target_language: str = Field(
        default="fa",
        min_length=2,
        max_length=10,
        description="ISO language code for the card's target language.",
        examples=["fa"],
    )
    level: Level = Field(
        default=Level.BEGINNER,
        description="Learner proficiency level.",
    )


class CardGenerationFromTopicRequest(BaseModel):
    """
    Payload for card generation from topic endpoint.
    """
    topic:str=Field(
        ...,
        min_length=10,
        max_length=500,
        description="The topic to generate flashcards for.",
        examples=["At the end of the day"],
    )

    count:int=Field(
        default=5,
        description="Number of flashcards to generate.",
    )

    level: Level = Field(
        default=Level.BEGINNER,
        description="Learner proficiency level.",
    )

    language: str = Field(
        default="en",
        min_length=2,
        max_length=10,
        description="ISO language code of the source term.",
        examples=["en"],
    )
    
    target_language: str = Field(
        default="fa",
        min_length=2,
        max_length=10,
        description="ISO language code for the card's target language.",
        examples=["fa"],
    )
    
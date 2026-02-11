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

from pydantic import BaseModel, Field


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
    level: str = Field(
        default="beginner",
        description="Learner proficiency level.",
        examples=["beginner", "intermediate", "advanced"],
    )

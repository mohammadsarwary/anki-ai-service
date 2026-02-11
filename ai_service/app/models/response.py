"""
Response models.

Responsibility:
    Defines Pydantic schemas for outgoing API response payloads.
    Keeps the API contract explicit and versioned independently
    of internal data structures.

Future extension points:
    - Add richer back-of-card fields (audio_url, image_url)
    - Add metadata (generation_model, latency_ms)
    - Add batch generation response model
"""

from typing import Optional

from pydantic import BaseModel, Field


class CardBack(BaseModel):
    """Structured content for the back side of a flashcard."""

    definition: str = Field(
        default="",
        description="Primary definition or translation of the term.",
    )
    example: str = Field(
        default="",
        description="Example sentence using the term.",
    )
    phonetic: Optional[str] = Field(
        default=None,
        description="Phonetic transcription (IPA or simplified).",
    )


class CardGenerationResponse(BaseModel):
    """Payload returned by the card generation endpoint."""

    front: str = Field(
        default="",
        description="Front side of the flashcard (the prompt shown to the learner).",
    )
    back: CardBack = Field(
        default_factory=CardBack,
        description="Structured back side of the flashcard.",
    )
    difficulty: str = Field(
        default="medium",
        description="Estimated difficulty of the card.",
        examples=["easy", "medium", "hard"],
    )

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

from typing import List, Optional

from pydantic import BaseModel, Field


class TTS(BaseModel):
    """Text-to-Speech configuration for audio generation.
    
    This model contains the information needed to generate
    audio pronunciation for a word or sentence.
    """
    
    text: str = Field(
        description="The text to be converted to speech (natural form, not phonetic).",
    )
    lang: str = Field(
        default="en-US",
        description="Language code for TTS engine (e.g., 'en-US', 'en-GB').",
    )


class Pronunciation(BaseModel):
    """Pronunciation information for a term.
    
    Contains both visual pronunciation guide and TTS configuration.
    """
    
    text: Optional[str] = Field(
        default=None,
        description="Written pronunciation guide (not IPA, user-friendly format).",
        examples=["ih-FEM-er-uhl"],
    )
    hint: Optional[str] = Field(
        default=None,
        description="Helpful pronunciation hint (e.g., 'stress on second syllable').",
    )
    tts: Optional[TTS] = Field(
        default=None,
        description="TTS configuration for audio generation.",
    )


class Example(BaseModel):
    """Example sentence demonstrating word usage.
    
    Each example includes the sentence and optional TTS configuration.
    """
    
    text: str = Field(
        description="Example sentence using the term.",
        examples=["The ephemeral beauty of cherry blossoms makes them special."],
    )
    tts: Optional[TTS] = Field(
        default=None,
        description="TTS configuration for this example sentence.",
    )


class CardBack(BaseModel):
    """Structured content for the back side of a flashcard.
    
    This model contains all the educational content that appears
    on the back of a flashcard, including definition, pronunciation,
    examples, and memory aids.
    """
    
    definition: str = Field(
        default="",
        description="Primary definition or translation of the term.",
    )
    pronunciation: Optional[Pronunciation] = Field(
        default=None,
        description="Pronunciation guide and TTS configuration.",
    )
    part_of_speech: Optional[str] = Field(
        default=None,
        description="Grammatical category (noun, verb, adjective, etc.).",
        examples=["noun", "verb", "adjective", "adverb"],
    )
    usage: Optional[str] = Field(
        default=None,
        description="Real-life explanation of how to use this word.",
    )
    examples: List[Example] = Field(
        default_factory=list,
        description="List of example sentences demonstrating usage.",
    )
    memory_tip: Optional[str] = Field(
        default=None,
        description="Short and helpful memory tip for remembering the word.",
    )


class CardGenerationResponse(BaseModel):
    """Payload returned by the card generation endpoint.
    
    This is the top-level response model that contains both
    the front (prompt) and back (content) of a flashcard.
    """
    
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


class CardGenerationFromTopicResponse(BaseModel):
    """
    Payload returned by the card generation from topic endpoint.
    """

    cards:List[CardGenerationResponse]=Field(default_factory=list)


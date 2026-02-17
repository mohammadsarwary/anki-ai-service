"""Google Gemini AI provider implementation."""

import json
import re

import google.generativeai as genai

from app.providers.base import AIProvider
from app.models.response import (
    CardBack,
    CardGenerationFromTopicResponse,
    CardGenerationResponse,
    TTS,
    Pronunciation,
    Example,
)
from app.core.config import settings
from app.core.exceptions import APIProviderError, InvalidResponseError
from app.utils.logger import logger


class GoogleGeminiProvider(AIProvider):
    """Google Gemini AI provider."""
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GOOGLE_GEMINI_MODEL)
    
    async def generate_cards_from_topic(
        self,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str,
    ) -> CardGenerationFromTopicResponse:
        """Generate multiple flashcards from a topic."""
        
        prompt = f'''You are a JSON API. You MUST respond with ONLY valid JSON.

        Generate {count} flashcards about "{topic}" at {level} level.

        Return a JSON array with exactly {count} cards in this format:
        [
            {{
                "front": "word",
                "difficulty": "easy|medium|hard",
                "back": {{
                    "definition": "Simple definition in {target_language}",
                    "pronunciation": {{
                        "text": "pronunciation guide",
                        "hint": "helpful hint or null",
                        "tts": {{ "text": "word", "lang": "{language}" }}
                    }},
                    "part_of_speech": "noun/verb/etc or null",
                    "usage": "How to use this word or null",
                    "examples": [
                        {{ "text": "Example sentence", "tts": {{ "text": "Example sentence", "lang": "{language}" }} }}
                    ],
                    "memory_tip": "Memory tip or null"
                }}
            }}
        ]

        INPUT:
        - Topic: "{topic}"
        - Count: {count}
        - Level: "{level}"
        - Language: "{language}"
        - Target Language: "{target_language}"

        RESPOND WITH JSON ONLY:'''
        
        logger.info("Generating cards from topic: '%s'", topic)
        
        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            logger.info("Raw response: %s", raw)
        except Exception as e:
            logger.error("Google Gemini error: %s", e)
            raise APIProviderError()
        
        # Clean markdown if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()
        
        # Parse cards
        cards = []
        for card_data in data:
            card = self._parse_card(card_data)
            cards.append(card)
        
        return CardGenerationFromTopicResponse(cards=cards)
    
    async def generate_card(
        self,
        term: str,
        language: str,
        target_language: str,
        level: str,
    ) -> CardGenerationResponse:
        """Generate a single flashcard."""
        
        prompt = f'''You are a JSON API. You MUST respond with ONLY valid JSON.

        Generate a flashcard for "{term}" in this EXACT format:

        {{
            "front": "{term}",
            "difficulty": "easy",
            "back": {{
                "definition": "Definition in {target_language}",
                "pronunciation": {{
                    "text": "pronunciation guide",
                    "hint": null,
                    "tts": {{ "text": "{term}", "lang": "{language}" }}
                }},
                "part_of_speech": "Part of speech in {target_language}",
                "usage": "Usage in {target_language}",
                "examples": [
                    {{ "text": "Example in {language}", "tts": {{ "text": "...", "lang": "{language}" }} }}
                ],
                "memory_tip": "Memory tip in {target_language}"
            }}
        }}

        INPUT:
        - Word: "{term}"
        - Level: "{level}"
        - Source Language: "{language}"
        - Target Language: "{target_language}"

        RESPOND WITH JSON ONLY:'''
        
        logger.info("Generating card for term: '%s'", term)
        
        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            logger.info("Raw response: %s", raw)
        except Exception as e:
            logger.error("Google Gemini error: %s", e)
            raise APIProviderError()
        
        # Clean markdown if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()
        
        return self._parse_card(data, default_term=term)
    
    def _parse_card(self, data: dict, default_term: str = "") -> CardGenerationResponse:
        """Parse card data from AI response."""
        
        back_data = data.get("back", {})
        
        # Parse pronunciation
        pronunciation = None
        pronunciation_data = back_data.get("pronunciation", {})
        if pronunciation_data:
            tts = None
            tts_data = pronunciation_data.get("tts")
            if tts_data:
                tts = TTS(
                    text=tts_data.get("text", ""),
                    lang=tts_data.get("lang", "en-US"),
                )
            pronunciation = Pronunciation(
                text=pronunciation_data.get("text", ""),
                hint=pronunciation_data.get("hint"),
                tts=tts,
            )
        
        # Parse examples
        example_list = []
        for ex in back_data.get("examples", []):
            tts = None
            if ex.get("tts"):
                tts = TTS(
                    text=ex["tts"].get("text", ""),
                    lang=ex["tts"].get("lang", "en-US"),
                )
            example_list.append(Example(
                text=ex.get("text", ""),
                tts=tts,
            ))
        
        return CardGenerationResponse(
            front=data.get("front", default_term),
            back=CardBack(
                definition=back_data.get("definition", ""),
                pronunciation=pronunciation,
                part_of_speech=back_data.get("part_of_speech"),
                usage=back_data.get("usage"),
                examples=example_list,
                memory_tip=back_data.get("memory_tip"),
            ),
            difficulty=data.get("difficulty", "medium"),
        )

"""Google Gemini AI provider implementation."""

import json

import google.generativeai as genai

from app.providers.base import AIProvider
from app.models.response import (
    CardGenerationFromTopicResponse,
    CardGenerationResponse,
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

        QUALITY RULES:
        - Return exactly {count} cards
        - Each "front" must be unique
        - "definition" must be concise and non-empty
        - "examples" must contain at least one natural sentence

        RESPOND WITH JSON ONLY:'''
        
        logger.info("Generating cards from topic: '%s'", topic)
        
        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            logger.info("Raw response: %s", raw)
        except Exception as e:
            logger.error("Google Gemini error: %s", e)
            raise APIProviderError()
        
        raw = self._clean_json_text(raw)
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()
        
        cards = self._parse_card_list(data, expected_count=count)
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

        QUALITY RULES:
        - "front" must exactly match "{term}"
        - "definition" must be concise and non-empty
        - "examples" must contain at least one natural sentence
        - Use difficulty from: easy, medium, hard

        RESPOND WITH JSON ONLY:'''
        
        logger.info("Generating card for term: '%s'", term)
        
        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            logger.info("Raw response: %s", raw)
        except Exception as e:
            logger.error("Google Gemini error: %s", e)
            raise APIProviderError()
        
        raw = self._clean_json_text(raw)
        
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()
        
        card = self._parse_card(data, default_front=term)
        if card.front != term:
            raise InvalidResponseError(detail="AI response changed the requested term")
        return card

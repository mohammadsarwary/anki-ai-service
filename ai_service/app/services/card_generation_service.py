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


from app.utils.logger import logger
from openai import OpenAI
import json
import openai
from fastapi import HTTPException
from app.models.response import CardBack, CardGenerationResponse, TTS, Pronunciation, Example
from app.core.config import settings
from app.core.exceptions import APIProviderError,APIRateLimitError,InvalidResponseError

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

class CardGenerationService:
    

    async def generate_card(
        self,
        term:str,
        language:str,
        target_language:str,
        level:str, 
    )->CardGenerationResponse:


        prompt = f'''You are a flashcard designer. Generate ONE flashcard for "{term}".

            INPUT:
            - Word: "{term}"
            - Level: "{level}"
            - Source Language: "{language}"
            - Target Language: "{target_language}"

            OUTPUT RULES:
            1. Return ONLY valid JSON (no markdown, no code blocks)
            2. Use plain text only (no HTML, no emojis, no markdown)
            3. Translate these fields to Target Language ({target_language}):
            - definition
            - part_of_speech
            - usage
            - memory_tip
            4. Keep examples in the source language ({language})
            5. pronunciation.tts.text must be the natural word, not phonetic

            JSON STRUCTURE:
            {{
            "front": "{term}",
            "difficulty": "easy|medium|hard",
            "back": {{
                "definition": "Definition in {target_language}",
                "pronunciation": {{
                "text": "Pronunciation guide",
                "hint": "Pronunciation hint or null",
                "tts": {{ "text": "{term}", "lang": "{language}" }}
                }},
                "part_of_speech": "Part of speech in {target_language}",
                "usage": "Usage explanation in {target_language}",
                "examples": [
                {{ "text": "Example in {language}", "tts": {{ "text": "...", "lang": "{language}" }} }}
                ],
                "memory_tip": "Memory tip in {target_language} or null"
            }}
            }}'''
        

        logger.info("Generating card for term: '%s'", term)
        
        try:
            response=client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful flashcard generator. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.OPENROUTER_MAX_TOKENS,
                extra_headers={
                    "HTTP-Referer": settings.OPENROUTER_REFERER,
                    "X-Title": settings.OPENROUTER_SITE_TITLE,
                },
            )

        #Error exception
        except openai.RateLimitError as e:
            logger.warning("Rate limit by provider")
            raise APIRateLimitError()

        except openai.APIError as e:
            logger.warning("Open AI error:%s",e)
            raise APIProviderError()

        raw=response.choices[0].message.content.strip()
        logger.info("Raw response: %s", raw)

        try:
            data=json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()

        back_data=data.get("back",{})

        # 1.parse pronunciation 
        pronunciation=None
        pronunciation_data=back_data.get("pronunciation",{})
        if pronunciation_data:
            tts=None
            tts_data=pronunciation_data.get("tts")
            if tts_data:
                tts=TTS(
                    text=tts_data.get("text",""),
                    lang=tts_data.get("lang","en-US")
                )
            pronunciation=Pronunciation(
                text=pronunciation_data.get("text",""),
                hint=pronunciation_data.get("hint",""),
                tts=tts
            )

        # 2.parse examples lists
        example_list=[]
        for ex in back_data.get("examples",[]):
            tts=None
            if ex.get("tts"):
                tts=TTS(
                    text=ex["tts"].get("text",""),
                    lang=ex["tts"].get("lang","en-US")
                )
            example_list.append(Example(
                text=ex.get("text",""),
                tts=tts
            ))
        
        # 3.create Cardback
        return CardGenerationResponse(
            front=data.get("front", term),
            back=CardBack(
                definition=back_data.get("definition", ""),
                examples=example_list,
                pronunciation=pronunciation,
                part_of_speech=back_data.get("part_of_speech", ""),
                usage=back_data.get("usage", ""),
                memory_tip=back_data.get("memory_tip", ""),
            ),
            difficulty=data.get("difficulty", "medium"),
        )

       
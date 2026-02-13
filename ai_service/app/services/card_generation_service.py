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


        prompt = (

            f'You are an expert English teacher and UX-focused flashcard designer.\n\n'
            f'Your task is to generate ONE flashcard for the word "{term}" at {level} level.\n\n'
            f'CRITICAL OUTPUT RULES:\n'
            f'- Output VALID JSON ONLY - NO markdown, NO code blocks, NO explanations outside JSON\n'
            f'- ABSOLUTELY NO HTML TAGS - Use plain text only\n'
            f'- NO EMOJIS - Use plain text only\n'
            f'- NO MARKDOWN FORMATTING - Use plain text only\n'
            f'- All content must be structured JSON with nested objects\n'
            f'- Missing data should be returned as null or empty array\n'
            f'- Friendly, natural, learner-focused tone\n'
            f'- Avoid dictionary tone\n\n'
            f'Input:\n'
            f'Word: "{term}"\n'
            f'Level: "{level}"\n'
            f'Language: "{language}"\n'
            f'Target Language: "{target_language}"\n\n'
            f'Return JSON format EXACTLY like this:\n\n'
            f'{{\n'
            f'  "front": "{term}",\n'
            f'  "difficulty": "easy|medium|hard",\n'
            f'  "back": {{\n'
            f'    "definition": "Simple and friendly definition",\n'
            f'    "pronunciation": {{\n'
            f'      "text": "Written pronunciation guide (not IPA)",\n'
            f'      "hint": "Helpful pronunciation hint or null if not available",\n'
            f'      "tts": {{\n'
            f'        "text": "{term}",\n'
            f'        "lang": "en-US"\n'
            f'      }}\n'
            f'    }},\n'
            f'    "part_of_speech": "noun|verb|adjective|etc or null if not applicable",\n'
            f'    "usage": "Real-life explanation of how to use this word or null if not available",\n'
            f'    "examples": [\n'
            f'      {{\n'
            f'        "text": "Simple example sentence",\n'
            f'        "tts": {{ "text": "Simple example sentence", "lang": "en-US" }}\n'
            f'      }},\n'
            f'      {{\n'
            f'        "text": "Natural/native example sentence",\n'
            f'        "tts": {{ "text": "Natural/native example sentence", "lang": "en-US" }}\n'
            f'      }}\n'
            f'    ],\n'
            f'    "memory_tip": "Short and helpful memory tip or null if not available"\n'
            f'  }}\n'
            f'}}\n\n'
            f'Requirements:\n'
            f'- difficulty must be exactly "easy", "medium", or "hard"\n'
            f'- examples must be an array (can be empty if not available)\n'
            f'- definition is required and must be non-empty\n'
            f'- pronunciation can be null if not available\n'
            f'- If pronunciation is present and pronunciation.tts is present, pronunciation.tts.text MUST be the natural word (NOT phonetic)\n'
            f'- If pronunciation.tts is present, pronunciation.tts.lang MUST be "en-US" by default\n'
            f'- part_of_speech can be null if not applicable\n'
            f'- usage can be null if not available\n'
            f'- memory_tip can be null if not available\n'
            f'- NO HTML tags anywhere in the response\n'
            f'- NO EMOJIS anywhere in the response\n'
            f'- NO MARKDOWN formatting anywhere in the response'
        )

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

        except openai.RateLimitError as e:
            logger.warning("Rate limit by provider")
            raise HTTPException(status_code=429, detail="AI provider is temporarily rate-limited. Please try again in a few minutes.")   

        except openai.APIError as e:
            logger.error("OpenAI error: %s", e)
            raise HTTPException(status_code=502, detail="AI provider returned an error. Please try again later.")


        raw=response.choices[0].message.content.strip()
        logger.info("Raw response: %s", raw)

        try:
            data=json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise HTTPException(status_code=502, detail="AI provider returned invalid JSON. Please try again later.")

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
                definition=data.get("definition", ""),
                examples=example_list,
                pronunciation=pronunciation,
                part_of_speech=data.get("part_of_speech", ""),
                usage=data.get("usage", ""),
                memory_tip=data.get("memory_tip", ""),
            ),
            difficulty=data.get("difficulty", "medium"),
        )

       
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


from click import prompt
from app.utils.logger import logger
from openai import OpenAI
import json
import openai
from fastapi import HTTPException
from app.models.response import CardBack, CardGenerationFromTopicResponse, CardGenerationResponse, TTS, Pronunciation, Example
from app.core.config import settings
from app.core.exceptions import APIProviderError,APIRateLimitError,InvalidResponseError
import re
client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

class CardGenerationService:
    
    async def generate_card_from_topic(
        self,
        topic:str,
        count:int,
        level:str,
        language:str,
        target_language:str,
    )->CardGenerationFromTopicResponse:
        prompt=f'''
        
        You are an expert English teacher and UX-focused flashcard designer.

        Your task is to generate {count} flashcards about "{topic}" at {level} level.

        CRITICAL OUTPUT RULES:
        - Output VALID JSON ONLY - NO markdown, NO code blocks, NO explanations outside JSON
        - ABSOLUTELY NO HTML TAGS - Use plain text only
        - NO EMOJIS - Use plain text only
        - NO MARKDOWN FORMATTING - Use plain text only
        - All content must be structured JSON with nested objects
        - Missing data should be returned as null or empty array
        - Friendly, natural, learner-focused tone
        - Avoid dictionary tone

        Input:
        Topic: "{topic}"
        Count: {count}
        Level: "{level}"
        Language: "{language}"
        Target Language: "{target_language}"

        Return JSON format EXACTLY like this:

        [
        {{
            "front": "word1",
            "difficulty": "easy|medium|hard",
            "back": {{
            "definition": "Simple and friendly definition",
            "pronunciation": {{
                "text": "Written pronunciation guide (not IPA)",
                "hint": "Helpful pronunciation hint or null if not available",
                "tts": {{
                "text": "word1",
                "lang": "en-US"
                }}
            }},
            "part_of_speech": "noun|verb|adjective|etc or null if not applicable",
            "usage": "Real-life explanation of how to use this word or null if not available",
            "examples": [
                {{
                "text": "Simple example sentence",
                "tts": {{ "text": "Simple example sentence", "lang": "en-US" }}
                }},
                {{
                "text": "Natural/native example sentence",
                "tts": {{ "text": "Natural/native example sentence", "lang": "en-US" }}
                }}
            ],
            "memory_tip": "Short and helpful memory tip or null if not available"
            }}
        }},
        {{
            "front": "word2",
            "difficulty": "easy|medium|hard",
            "back": {{
            "definition": "Simple and friendly definition",
            "pronunciation": {{
                "text": "Written pronunciation guide (not IPA)",
                "hint": "Helpful pronunciation hint or null if not available",
                "tts": {{
                "text": "word2",
                "lang": "en-US"
                }}
            }},
            "part_of_speech": "noun|verb|adjective|etc or null if not applicable",
            "usage": "Real-life explanation of how to use this word or null if not available",
            "examples": [
                {{
                "text": "Simple example sentence",
                "tts": {{ "text": "Simple example sentence", "lang": "en-US" }}
                }},
                {{
                "text": "Natural/native example sentence",
                "tts": {{ "text": "Natural/native example sentence", "lang": "en-US" }}
                }}
            ],
            "memory_tip": "Short and helpful memory tip or null if not available"
            }}
        }}
        ]

        Requirements:
        - difficulty must be exactly "easy", "medium", or "hard"
        - examples must be an array (can be empty if not available)
        - definition is required and must be non-empty
        - pronunciation can be null if not available
        - If pronunciation is present and pronunciation.tts is present, pronunciation.tts.text MUST be the natural word (NOT phonetic)
        - Each example MUST be an object that includes a tts object
        - If example.tts is present, example.tts.lang MUST be "en-US" by default
        - part_of_speech can be null if not applicable
        - usage can be null if not available
        - memory_tip can be null if not available
        - NO HTML tags anywhere in the response
        - NO EMOJIS anywhere in the response
        - NO MARKDOWN formatting anywhere in the response
        - Generate exactly {count} cards
        '''
        logger.info("Generating card from topic: '%s'", topic)
        try:
            response=client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a JSON API. You MUST respond with ONLY valid JSON. No thinking, no reasoning, no explanation. Start with { and end with }."},
                    {"role": "user", "content": prompt},
                ],
                response_format={ "type": "json_object" },
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
        
        logger.info("AI response: %s",response)
        raw=response.choices[0].message.content.strip()
        logger.info("Raw Response: %s",raw)

        # raw=re.sub(r'^```(?:json)?\s*', '', raw) 
        # raw=re.sub(r'\s*```$', '', raw)
        # raw=raw.strip()

        try:
            data=json.loads(raw)
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()

        #parse cards list
        cards=[]
        for card_data in data:
            back_data=card_data.get("back",{})

            # parse pronuncation
            pronunciation=None
            pronunciation_data=back_data.get("pronunciation",{})

            if pronunciation_data:
                tts=None
                tts_data=pronunciation_data.get("tts")
                if tts_data:
                    tts=TTS(
                        text=tts_data.get("text",""),
                        lang=tts_data.get("lang", "en-US"),
                    )
                pronunciation=Pronunciation(
                    text=pronunciation_data.get("text",""),
                    hint=pronunciation_data.get("hint"),
                    tts=tts,
                )
            
            #parse examples
            example_list=[]
            for ex in back_data.get("examples",[]):
                tts=TTS(
                    text=ex.get("tts",{}).get("text",""),
                    lang=ex.get("tts",{}).get("lang", "en-US"),
                )
                example_list.append(Example(
                    text=ex.get("text",""),
                    tts=tts,
                )
                )
            
            # create card
            cards.append(CardGenerationResponse(
                front=card_data.get("front",""),
                back=CardBack(
                    definition=back_data.get("definition",""),
                    pronunciation=pronunciation,
                    part_of_speech=back_data.get("part_of_speech"),
                    usage=back_data.get("usage"),
                    examples=example_list,
                    memory_tip=back_data.get("memory_tip"),
                ),
                difficulty=card_data.get("difficulty",'medium')
            ))
        
        return CardGenerationFromTopicResponse(cards=cards)

            
            

    async def generate_card(
        self,
        term:str,
        language:str,
        target_language:str,
        level:str, 
    )->CardGenerationResponse:


        prompt = f'''You are a JSON API. You MUST respond with ONLY valid JSON.

        CRITICAL RULES:
        1. Start your response with {{ and end with }}
        2. Do NOT write any thinking, reasoning, or explanation
        3. Do NOT use markdown code blocks
        4. Do NOT write anything before or after the JSON

        Generate a flashcard for "{term}" in this EXACT format:

        {{"front": "{term}", "difficulty": "easy", "back": {{"definition": "Definition in {target_language}", "pronunciation": {{"text": "pronunciation guide", "hint": null, "tts": {{"text": "{term}", "lang": "{language}"}}}}, "part_of_speech": "Part of speech in {target_language}", "usage": "Usage in {target_language}", "examples": [{{"text": "Example in {language}", "tts": {{"text": "...", "lang": "{language}"}}}}], "memory_tip": "Memory tip in {target_language}"}}}}

        INPUT:
        - Word: "{term}"
        - Level: "{level}"
        - Source Language: "{language}"
        - Target Language: "{target_language}"

        RESPOND WITH JSON ONLY:'''
                

        logger.info("Generating card for term: '%s'", term)
        
        try:
            response=client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a JSON API. You MUST respond with ONLY valid JSON. No thinking, no reasoning, no explanation. Start with { and end with }."},
                    {"role": "user", "content": prompt},
                ],
                response_format={ "type": "json_object" },
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

        raw=re.sub(r'^```(?:json)?\s*', '', raw) 
        raw=re.sub(r'\s*```$', '', raw)
        raw=raw.strip()

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

       
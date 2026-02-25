"""OpenRouter AI provider implementation."""

from openai import OpenAI
import json
import openai
import re

from app.providers.base import AIProvider
from app.models.response import (
    CardBack,
    CardGenerationFromTopicResponse,
    CardGenerationResponse,
    TTS,
    Pronunciation,
    Example,
    PracticeSentenceData,
    PracticeSentenceResponse
)
from app.core.config import settings
from app.core.exceptions import APIProviderError, APIRateLimitError, InvalidResponseError
from app.utils.logger import logger


class OpenRouterProvider(AIProvider):
    """OpenRouter AI provider using OpenAI-compatible API."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.CEREBRAS_API_KEY,
            base_url=settings.CEREBRAS_BASE_URL,
        )
    
    async def generate_cards_from_topic(
        self,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str,
    ) -> CardGenerationFromTopicResponse:
        """Generate multiple flashcards from a topic."""
        
        prompt = f'''You are an expert language learning flashcard generator.

            TASK: Generate {count} flashcards about "{topic}" for {level} level learners.

            OUTPUT FORMAT: Return ONLY valid JSON with this structure:
            {{
                "cards": [
                    {{
                        "front": "word or phrase",
                        "difficulty": "easy|medium|hard",
                        "back": {{
                            "definition": "Definition in {target_language}",
                            "pronunciation": {{
                                "text": "pronunciation guide",
                                "hint": "helpful hint or null",
                                "tts": {{ "text": "word", "lang": "{language}" }}
                            }},
                            "part_of_speech": "noun|verb|adjective|idiom|phrase",
                            "usage": "How to use this word",
                            "examples": [{{ "text": "Example sentence", "tts": {{ "text": "...", "lang": "{language}" }} }}],
                            "memory_tip": "Memory technique"
                        }}
                    }}
                ]
            }}

            LEVEL GUIDELINES:
            - beginner: Common words, simple definitions, basic examples
            - intermediate: Everyday vocabulary, moderate complexity
            - advanced: Academic words, nuanced definitions, complex examples

            QUALITY RULES:
            - Each card MUST have a UNIQUE word (no duplicates)
            - Words must be directly relevant to "{topic}"
            - Examples must be natural and practical
            - Definitions in {target_language}, examples in {language}

            Generate {count} unique flashcards now:'''

        logger.info("Generating card from topic: '%s'", topic)
        try:
            response = self.client.chat.completions.create(
                model=settings.CEREBRAS_MODEL,
                messages=[
                    {"role": "system", "content": "You are a JSON API. You MUST respond with ONLY valid JSON. No thinking, no reasoning, no explanation. Start with { and end with }."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
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
        for card_data in data.get("cards",[]):
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
            response = self.client.chat.completions.create(
                model=settings.CEREBRAS_MODEL,
                messages=[
                    {"role": "system", "content": "You are a JSON API. You MUST respond with ONLY valid JSON. No thinking, no reasoning, no explanation. Start with { and end with }."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
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


    async def generate_practice_sentence(
        self,
        target_word:str,
        user_sentence:str,  
        language:str
    ) -> PracticeSentenceResponse:
        """Generate a practice sentence."""

        prompt = f"""
        You are a helpful language learning assistant evaluating a student's sentence creation practice.

        Target word: {target_word}
        User's sentence: {user_sentence}
        Language: {language}

        Your task:
        1. Evaluate how naturally the user used the target word in their sentence
        2. Assign a naturalness score from 0-100 where:
        - 90-100: Excellent, native-like usage
        - 75-89: Very good, natural and correct
        - 60-74: Good, understandable but could be improved
        - 40-59: Okay, awkward or unnatural phrasing
        - 0-39: Poor, incorrect usage or doesn't make sense
        3. Provide exactly 3 alternative example sentences showing better usage of the word
        4. Give encouraging feedback - NEVER be harsh or discouraging
        5. Consider grammar, context, and naturalness

        Return a JSON object with:
        - naturalness_score (integer 0-100): The naturalness score
        - feedback_message (string): Short encouraging message (max 100 chars)
        - suggestions (array): Exactly 3 example sentences showing better usage
        - grammar_notes (string|null): Brief grammar tip if needed, null if sentence is perfect
        - encouragement (string): Motivational closing message

        IMPORTANT:
        - Always be positive and encouraging
        - Focus on learning, not grading
        - Provide actionable suggestions
        - Keep suggestions simple and clear
        - Return ONLY valid JSON, no markdown formatting
        """.strip()

        

        pass

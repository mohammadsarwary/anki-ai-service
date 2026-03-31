"""OpenRouter AI provider implementation."""

import json

import openai
from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import APIProviderError, APIRateLimitError, InvalidResponseError
from app.models.response import (
    CardGenerationFromTopicResponse,
    CardGenerationResponse,
    PracticeSentenceData,
    PracticeSentenceResponse,
)
from app.providers.base import AIProvider
from app.utils.logger import logger


class OpenRouterProvider(AIProvider):
    """OpenRouter AI provider using OpenAI-compatible API."""

    TOPIC_TRUNCATION_DETAIL = "AI output truncated before valid JSON completion"

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.CEREBRAS_API_KEY,
            base_url=settings.CEREBRAS_BASE_URL,
        )

    def _create_json_completion(self, prompt: str, system_prompt: str) -> tuple[str, str | None]:
        try:
            response = self.client.chat.completions.create(
                model=settings.CEREBRAS_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.CEREBRAS_MAX_TOKENS,
                extra_headers={
                    "HTTP-Referer": settings.CEREBRAS_REFERER,
                    "X-Title": settings.CEREBRAS_SITE_TITLE,
                },
            )
        except openai.RateLimitError:
            logger.warning("Rate limit by provider")
            raise APIRateLimitError()
        except openai.APIError as exc:
            logger.warning("OpenAI API error: %s", exc)
            raise APIProviderError()

        choice = response.choices[0]
        finish_reason = choice.finish_reason
        raw = (choice.message.content or "").strip()

        logger.info("Completion finish reason: %s", finish_reason)
        logger.info("Raw response: %s", raw)

        return self._clean_json_text(raw), finish_reason

    def _build_topic_prompt(
        self,
        *,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str,
        compact: bool,
    ) -> str:
        if compact:
            return f'''You are an expert language learning flashcard generator.

TASK: Generate exactly {count} flashcards about "{topic}" for {level} learners.

Return ONLY valid JSON in this exact structure (no markdown, no extra text):
{{
  "cards": [
    {{
      "front": "word or short phrase",
      "difficulty": "easy|medium|hard",
      "back": {{
        "definition": "short definition in {target_language}",
        "pronunciation": {{
          "text": "pronunciation guide",
          "hint": null,
          "tts": {{ "text": "term", "lang": "{language}" }}
        }},
        "part_of_speech": "noun|verb|adjective|idiom|phrase",
        "usage": "short usage note",
        "examples": [
          {{ "text": "single natural sentence", "tts": {{ "text": "single natural sentence", "lang": "{language}" }} }}
        ],
        "memory_tip": "short memory tip"
      }}
    }}
  ]
}}

RULES:
- Exactly {count} cards, and each "front" must be unique.
- Keep each card concise.
- Use exactly 1 example per card.
- Use only fields shown above.
- Definitions in {target_language}, examples in {language}.'''

        return f'''You are an expert language learning flashcard generator.

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
- "front" must be a single useful word or short phrase with no numbering
- "definition" must be concise, learner-friendly, and never empty
- "examples" must contain at least one natural sentence
- Examples must be natural and practical
- Definitions in {target_language}, examples in {language}
- If you are unsure, still return your best valid JSON guess and keep every required field non-empty'''

    async def generate_cards_from_topic(
        self,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str,
    ) -> CardGenerationFromTopicResponse:
        """Generate multiple flashcards from a topic."""
        logger.info("Generating card from topic: '%s'", topic)

        system_prompt = (
            "You are a JSON API. You MUST respond with ONLY valid JSON. "
            "No thinking, no reasoning, no explanation. Start with { and end with }."
        )
        
        prompt = self._build_topic_prompt(
            topic=topic,
            count=count,
            level=level,
            language=language,
            target_language='en',
            compact=False,
        )
        logger.info("Prompt: '%s' ",prompt)

        raw, finish_reason = self._create_json_completion(prompt, system_prompt=system_prompt)

        should_retry_compact = finish_reason == "length"
        data = None

        if not should_retry_compact:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                if self._is_likely_truncated_json(raw):
                    should_retry_compact = True
                else:
                    logger.error("Failed to parse AI response as JSON: %s", raw)
                    raise InvalidResponseError(detail="AI response must be valid JSON")

        if should_retry_compact:
            logger.warning(
                "Retrying topic generation with compact prompt due to possible truncation "
                "(finish_reason=%s)",
                finish_reason,
            )

            compact_prompt = self._build_topic_prompt(
                topic=topic,
                count=count,
                level=level,
                language=language,
                target_language=target_language,
                compact=True,
            )

            retry_raw, retry_finish_reason = self._create_json_completion(
                compact_prompt,
                system_prompt=system_prompt,
            )

            if retry_finish_reason == "length":
                raise InvalidResponseError(detail=self.TOPIC_TRUNCATION_DETAIL)

            try:
                data = json.loads(retry_raw)
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON after retry: %s", retry_raw)
                if self._is_likely_truncated_json(retry_raw):
                    raise InvalidResponseError(detail=self.TOPIC_TRUNCATION_DETAIL)
                raise InvalidResponseError(detail="AI response must be valid JSON")

        if not isinstance(data, dict):
            raise InvalidResponseError(detail="AI response must be a JSON object with a 'cards' field")

        cards = self._parse_card_list(data.get("cards"), expected_count=count)
        return CardGenerationFromTopicResponse(cards=cards)

    async def generate_card(
        self,
        term: str,
        language: str,
        target_language: str,
        level: str,
    ) -> CardGenerationResponse:
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

QUALITY RULES:
- "definition" must be short, clear, and non-empty
- "examples" must contain at least one natural sentence
- "front" must exactly match "{term}"
- Use difficulty from: easy, medium, hard

RESPOND WITH JSON ONLY:'''

        logger.info("Generating card for term: '%s'", term)

        system_prompt = (
            "You are a JSON API. You MUST respond with ONLY valid JSON. "
            "No thinking, no reasoning, no explanation. Start with { and end with }."
        )
        raw, _ = self._create_json_completion(prompt, system_prompt=system_prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()

        card = self._parse_card(data, default_front=term)
        if card.front != term:
            raise InvalidResponseError(detail="AI response changed the requested term")
        return card

    async def generate_practice_sentence(
        self,
        target_word: str,
        user_sentence: str,
        language: str,
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
- score_label (string): Qualitative label based on score - "Excellent" for 90-100, "Very Good" for 75-89, "Good" for 60-74, "Fair" for 40-59, "Needs Improvement" for 0-39
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

        logger.info("Generating practice sentence feedback for word: '%s'", target_word)

        system_prompt = (
            "You are a helpful language learning assistant evaluating a student's sentence "
            "creation practice. You MUST respond with ONLY valid JSON. No thinking, no "
            "reasoning, no explanation. Start with { and end with }."
        )

        raw, _ = self._create_json_completion(prompt, system_prompt=system_prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", raw)
            raise InvalidResponseError()

        return PracticeSentenceResponse(
            success=True,
            data=PracticeSentenceData(
                naturalness_score=data.get("naturalness_score", 0),
                feedback_message=data.get("feedback_message", ""),
                suggestions=data.get("suggestions", []),
                score_label=data.get("score_label", "Good"),
                grammar_notes=data.get("grammar_notes"),
                encouragement=data.get("encouragement", ""),
                user_sentence=user_sentence,
            ),
        )

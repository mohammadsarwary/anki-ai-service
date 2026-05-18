from __future__ import annotations

import json
from abc import ABC, abstractmethod

import openai
from django.conf import settings
from openai import OpenAI

from apps.ai.exceptions import APIProviderError, APIRateLimitError, InvalidResponseError


def _clean_json_text(raw: str) -> str:
    raw = (raw or "").strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def _likely_truncated(raw: str) -> bool:
    return raw.count("{") > raw.count("}") or raw.count("[") > raw.count("]")


class AIProvider(ABC):
    @abstractmethod
    def create_json_completion(self, prompt: str, system_prompt: str) -> tuple[dict, int, str | None]:
        raise NotImplementedError


class OpenAICompatibleProvider(AIProvider):
    TOPIC_TRUNCATION_DETAIL = "AI output truncated before valid JSON completion"

    def __init__(self):
        if not settings.CEREBRAS_API_KEY:
            raise APIProviderError("AI provider API key is not configured")
        self.client = OpenAI(api_key=settings.CEREBRAS_API_KEY, base_url=settings.CEREBRAS_BASE_URL)
        self.model = settings.CEREBRAS_MODEL

    def create_json_completion(self, prompt: str, system_prompt: str) -> tuple[dict, int, str | None]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=settings.CEREBRAS_MAX_TOKENS,
                extra_headers={"HTTP-Referer": settings.CEREBRAS_REFERER, "X-Title": settings.CEREBRAS_SITE_TITLE},
            )
        except openai.RateLimitError as exc:
            raise APIRateLimitError() from exc
        except openai.APIError as exc:
            raise APIProviderError(str(exc)) from exc

        choice = response.choices[0]
        raw = _clean_json_text(choice.message.content or "")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            if choice.finish_reason == "length" or _likely_truncated(raw):
                raise InvalidResponseError(self.TOPIC_TRUNCATION_DETAIL) from exc
            raise InvalidResponseError() from exc
        tokens = getattr(getattr(response, "usage", None), "total_tokens", 0) or 0
        return data, tokens, choice.finish_reason


def get_ai_provider() -> AIProvider:
    return OpenAICompatibleProvider()

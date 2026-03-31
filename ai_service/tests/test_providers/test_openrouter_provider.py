import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import InvalidResponseError
from app.providers.openrouter import OpenRouterProvider


def _completion(raw: str, *, finish_reason: str = "stop") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(content=raw),
            )
        ]
    )


def _cards_payload(count: int) -> str:
    cards = []
    for index in range(count):
        cards.append(
            {
                "front": f"term-{index}",
                "difficulty": "easy",
                "back": {
                    "definition": f"definition-{index}",
                    "pronunciation": {
                        "text": f"term-{index}",
                        "hint": None,
                        "tts": {"text": f"term-{index}", "lang": "en"},
                    },
                    "part_of_speech": "noun",
                    "usage": f"usage-{index}",
                    "examples": [
                        {
                            "text": f"example sentence {index}",
                            "tts": {"text": f"example sentence {index}", "lang": "en"},
                        }
                    ],
                    "memory_tip": f"memory-{index}",
                },
            }
        )
    return json.dumps({"cards": cards})


@pytest.mark.asyncio
async def test_generate_cards_from_topic_retries_once_on_finish_reason_length():
    provider = OpenRouterProvider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = MagicMock(
        side_effect=[
            _completion('{"cards":[{"front":"term-0"', finish_reason="length"),
            _completion(_cards_payload(2), finish_reason="stop"),
        ]
    )

    response = await provider.generate_cards_from_topic(
        topic="travel vocabulary",
        count=2,
        level="beginner",
        language="en",
        target_language="fa",
    )

    assert len(response.cards) == 2
    assert provider.client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_cards_from_topic_raises_truncation_error_after_retry_failure():
    provider = OpenRouterProvider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = MagicMock(
        side_effect=[
            _completion('{"cards":[{"front":"term-0"', finish_reason="length"),
            _completion('{"cards":[{"front":"term-0"', finish_reason="stop"),
        ]
    )

    with pytest.raises(InvalidResponseError) as exc_info:
        await provider.generate_cards_from_topic(
            topic="travel vocabulary",
            count=2,
            level="beginner",
            language="en",
            target_language="fa",
        )

    assert exc_info.value.detail == provider.TOPIC_TRUNCATION_DETAIL
    assert provider.client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_cards_from_topic_does_not_retry_on_non_truncation_json_error():
    provider = OpenRouterProvider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = MagicMock(
        return_value=_completion('{"cards":[}', finish_reason="stop")
    )

    with pytest.raises(InvalidResponseError) as exc_info:
        await provider.generate_cards_from_topic(
            topic="travel vocabulary",
            count=2,
            level="beginner",
            language="en",
            target_language="fa",
        )

    assert exc_info.value.detail == "AI response must be valid JSON"
    assert provider.client.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_generate_cards_from_topic_no_retry_for_valid_first_response():
    provider = OpenRouterProvider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = MagicMock(
        return_value=_completion(_cards_payload(2), finish_reason="stop")
    )

    response = await provider.generate_cards_from_topic(
        topic="travel vocabulary",
        count=2,
        level="beginner",
        language="en",
        target_language="fa",
    )

    assert len(response.cards) == 2
    assert provider.client.chat.completions.create.call_count == 1

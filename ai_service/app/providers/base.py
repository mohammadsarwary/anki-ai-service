
from abc import ABC, abstractmethod
import re

from app.core.exceptions import InvalidResponseError
from app.models.response import (
    CardBack,
    CardGenerationFromTopicResponse,
    CardGenerationResponse,
    Example,
    PracticeSentenceResponse,
    Pronunciation,
    TTS,
)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_card(
        self, 
        term: str, 
        language: str,
        target_language: str,
        level: str,
    ) -> CardGenerationResponse:
        """Generate a single flashcard."""
        pass

    @abstractmethod
    async def generate_cards_from_topic(
        self,
        topic: str,
        count: int,
        level: str,
        language: str,
        target_language: str,
    ) -> CardGenerationFromTopicResponse:
        """Generate multiple flashcards from a topic."""
        pass

    @abstractmethod
    async def generate_practice_sentence(
        self, 
        target_word: str, 
        user_sentence: str,
        language: str
    ) -> PracticeSentenceResponse:
        """Generate a practice sentence."""
        pass

    @staticmethod
    def _clean_json_text(raw: str) -> str:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    @staticmethod
    def _is_likely_truncated_json(raw: str) -> bool:
        """Heuristic for detecting JSON that was cut off mid-generation."""
        cleaned = raw.strip()
        if not cleaned or cleaned[0] not in "{[":
            return False

        stack: list[str] = []
        in_string = False
        escape = False

        for char in cleaned:
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char in "{[":
                stack.append(char)
            elif char == "}":
                if not stack or stack[-1] != "{":
                    return False
                stack.pop()
            elif char == "]":
                if not stack or stack[-1] != "[":
                    return False
                stack.pop()

        if in_string or cleaned.endswith("\\"):
            return True

        if stack:
            return True

        return cleaned[-1] in {",", ":"}

    @staticmethod
    def _require_non_empty_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidResponseError(detail=f"Missing or invalid '{field_name}' in AI response")
        return value.strip()

    @staticmethod
    def _optional_string(value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidResponseError(detail=f"Invalid '{field_name}' in AI response")
        cleaned = value.strip()
        return cleaned or None

    def _parse_tts(self, data: object, field_name: str) -> TTS | None:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise InvalidResponseError(detail=f"Invalid '{field_name}' in AI response")
        return TTS(
            text=self._require_non_empty_string(data.get("text"), f"{field_name}.text"),
            lang=self._require_non_empty_string(data.get("lang"), f"{field_name}.lang"),
        )

    def _parse_pronunciation(self, data: object) -> Pronunciation | None:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise InvalidResponseError(detail="Invalid 'pronunciation' in AI response")

        text = self._optional_string(data.get("text"), "pronunciation.text")
        hint = self._optional_string(data.get("hint"), "pronunciation.hint")
        tts = self._parse_tts(data.get("tts"), "pronunciation.tts")

        if not any([text, hint, tts]):
            return None

        return Pronunciation(text=text, hint=hint, tts=tts)

    def _parse_examples(self, data: object) -> list[Example]:
        if not isinstance(data, list) or not data:
            raise InvalidResponseError(detail="AI response must include at least one example")

        examples: list[Example] = []
        for index, example_data in enumerate(data):
            if not isinstance(example_data, dict):
                raise InvalidResponseError(detail=f"Invalid example at index {index}")
            examples.append(
                Example(
                    text=self._require_non_empty_string(example_data.get("text"), f"examples[{index}].text"),
                    tts=self._parse_tts(example_data.get("tts"), f"examples[{index}].tts"),
                )
            )
        return examples

    def _parse_card(self, data: object, default_front: str = "") -> CardGenerationResponse:
        if not isinstance(data, dict):
            raise InvalidResponseError(detail="AI response card must be a JSON object")

        back_data = data.get("back")
        if not isinstance(back_data, dict):
            raise InvalidResponseError(detail="AI response card must include a valid 'back' object")

        front = self._require_non_empty_string(data.get("front", default_front), "front")
        definition = self._require_non_empty_string(back_data.get("definition"), "back.definition")
        difficulty = self._require_non_empty_string(data.get("difficulty", "medium"), "difficulty").lower()
        if difficulty not in {"easy", "medium", "hard"}:
            raise InvalidResponseError(detail="Invalid 'difficulty' value in AI response")

        return CardGenerationResponse(
            front=front,
            back=CardBack(
                definition=definition,
                pronunciation=self._parse_pronunciation(back_data.get("pronunciation")),
                part_of_speech=self._optional_string(back_data.get("part_of_speech"), "back.part_of_speech"),
                usage=self._optional_string(back_data.get("usage"), "back.usage"),
                examples=self._parse_examples(back_data.get("examples")),
                memory_tip=self._optional_string(back_data.get("memory_tip"), "back.memory_tip"),
            ),
            difficulty=difficulty,
        )

    def _parse_card_list(self, data: object, expected_count: int | None = None) -> list[CardGenerationResponse]:
        if not isinstance(data, list) or not data:
            raise InvalidResponseError(detail="AI response must include a non-empty cards list")

        cards = [self._parse_card(card_data) for card_data in data]

        if expected_count is not None and len(cards) != expected_count:
            raise InvalidResponseError(
                detail=f"AI response returned {len(cards)} cards instead of {expected_count}"
            )

        normalized_fronts = [card.front.casefold() for card in cards]
        if len(normalized_fronts) != len(set(normalized_fronts)):
            raise InvalidResponseError(detail="AI response contains duplicate card fronts")

        return cards

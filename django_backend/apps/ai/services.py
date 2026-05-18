from __future__ import annotations

import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.ai.exceptions import InvalidResponseError
from apps.ai.models import AIGeneration
from apps.ai.providers import get_ai_provider
from apps.decks.models import Card, Deck


def normalize_card(data: dict, default_front: str | None = None) -> dict:
    front = str(data.get("front") or default_front or "").strip()
    back = data.get("back") if isinstance(data.get("back"), dict) else {}
    definition = str(back.get("definition") or data.get("definition") or "").strip()
    if not front or not definition:
        raise InvalidResponseError("AI card response is missing front or back.definition")
    pronunciation = back.get("pronunciation") if isinstance(back.get("pronunciation"), dict) else None
    examples = back.get("examples") if isinstance(back.get("examples"), list) else []
    normalized_examples = []
    for example in examples:
        if isinstance(example, dict) and example.get("text"):
            normalized_examples.append({"text": str(example["text"]), "tts": example.get("tts")})
        elif isinstance(example, str):
            normalized_examples.append({"text": example, "tts": None})
    return {
        "front": front,
        "difficulty": data.get("difficulty") if data.get("difficulty") in ["easy", "medium", "hard"] else "medium",
        "back": {
            "definition": definition,
            "pronunciation": pronunciation,
            "part_of_speech": back.get("part_of_speech"),
            "usage": back.get("usage"),
            "examples": normalized_examples,
            "memory_tip": back.get("memory_tip"),
        },
    }


class AICardService:
    def __init__(self, provider=None):
        self.provider = provider

    def _provider(self):
        if self.provider is None:
            self.provider = get_ai_provider()
        return self.provider

    def _system(self) -> str:
        return "You are a JSON API. Respond with valid JSON only, no markdown, no extra text."

    def generate_card(self, term: str, language: str = "en", target_language: str = "fa", level: str = "beginner") -> tuple[dict, int]:
        prompt = f"""
Generate one language-learning flashcard for "{term}" at {level} level.
Return exactly this JSON shape:
{{"front":"{term}","difficulty":"easy|medium|hard","back":{{"definition":"definition in {target_language}","pronunciation":{{"text":"guide","hint":null,"tts":{{"text":"{term}","lang":"{language}"}}}},"part_of_speech":"noun|verb|adjective|phrase|null","usage":"usage note","examples":[{{"text":"example in {language}","tts":{{"text":"example in {language}","lang":"{language}"}}}}],"memory_tip":"short tip"}}}}
"""
        data, tokens, _ = self._provider().create_json_completion(prompt, self._system())
        return normalize_card(data, default_front=term), tokens

    def generate_cards_from_topic(
        self,
        topic: str,
        count: int = 10,
        language: str = "en",
        target_language: str = "fa",
        level: str = "beginner",
    ) -> tuple[list[dict], int]:
        prompt = f"""
Generate exactly {count} unique flashcards about "{topic}" for {level} learners.
Return JSON object: {{"cards":[{{"front":"word","difficulty":"easy|medium|hard","back":{{"definition":"in {target_language}","pronunciation":{{"text":"guide","hint":null,"tts":{{"text":"word","lang":"{language}"}}}},"part_of_speech":"noun","usage":"usage","examples":[{{"text":"sentence","tts":{{"text":"sentence","lang":"{language}"}}}}],"memory_tip":"tip"}}}}]}}
"""
        data, tokens, finish_reason = self._provider().create_json_completion(prompt, self._system())
        cards = data.get("cards")
        if not isinstance(cards, list):
            raise InvalidResponseError("AI response must be a JSON object with a cards field")
        return [normalize_card(card) for card in cards[:count]], tokens

    def generate_cards_from_text(self, text: str, count: int = 10) -> tuple[list[dict], int]:
        prompt = f"""
Extract {count} useful flashcards from this text.
Text: {text}
Return JSON object with cards array using fields front, difficulty, back.definition, back.examples.
"""
        data, tokens, _ = self._provider().create_json_completion(prompt, self._system())
        cards = data.get("cards", data if isinstance(data, list) else [])
        if not isinstance(cards, list):
            raise InvalidResponseError("AI response must include cards")
        return [normalize_card(card) for card in cards[:count]], tokens

    def analyze_sentence(self, sentence: str, target_word: str) -> tuple[dict, int]:
        prompt = f"""
Analyze this sentence for grammar and usage of "{target_word}": "{sentence}".
Return JSON: {{"is_correct":true,"quality_score":0,"grammar_issues":[],"suggestions":[]}}
"""
        data, tokens, _ = self._provider().create_json_completion(prompt, self._system())
        return {
            "is_correct": bool(data.get("is_correct", False)),
            "quality_score": int(data.get("quality_score", 0)),
            "grammar_issues": data.get("grammar_issues") if isinstance(data.get("grammar_issues"), list) else [],
            "suggestions": data.get("suggestions") if isinstance(data.get("suggestions"), list) else [],
        }, tokens

    def improve_card(self, front: str, back: str) -> tuple[dict, int]:
        prompt = f"""
Improve this flashcard. Front: {front}. Back: {back}.
Return JSON: {{"improved_front":"...","improved_back":"...","suggestions":[]}}
"""
        data, tokens, _ = self._provider().create_json_completion(prompt, self._system())
        return {
            "improved_front": data.get("improved_front", front),
            "improved_back": data.get("improved_back", back),
            "suggestions": data.get("suggestions") if isinstance(data.get("suggestions"), list) else [],
        }, tokens

    def practice_sentence(self, target_word: str, user_sentence: str, language: str = "en") -> tuple[dict, int]:
        prompt = f"""
Evaluate this student's sentence in {language}.
Target word: {target_word}
Sentence: {user_sentence}
Return JSON: {{"naturalness_score":0,"score_label":"Good","feedback_message":"...","user_sentence":"{user_sentence}","suggestions":[],"grammar_notes":null,"encouragement":"..."}}
"""
        data, tokens, _ = self._provider().create_json_completion(prompt, self._system())
        score = max(0, min(100, int(data.get("naturalness_score", 0))))
        return {
            "naturalness_score": score,
            "score_label": data.get("score_label", "Good"),
            "feedback_message": data.get("feedback_message", ""),
            "user_sentence": user_sentence,
            "suggestions": data.get("suggestions") if isinstance(data.get("suggestions"), list) else [],
            "grammar_notes": data.get("grammar_notes"),
            "encouragement": data.get("encouragement"),
        }, tokens

    def practice_feedback(self, correct_answer: str, user_answer: str, language: str = "en", context: dict | None = None) -> tuple[dict, int]:
        prompt = f"""
Evaluate a flashcard practice answer in {language}.
Correct answer: {correct_answer}
User answer: {user_answer}
Context: {context or {}}
Return JSON: {{"is_correct":true,"feedback":"short helpful feedback","suggestions":[],"pronunciation":null,"confidence_score":0}}
"""
        data, tokens, _ = self._provider().create_json_completion(prompt, self._system())
        return {
            "is_correct": bool(data.get("is_correct", False)),
            "feedback": data.get("feedback", ""),
            "suggestions": data.get("suggestions") if isinstance(data.get("suggestions"), list) else [],
            "pronunciation": data.get("pronunciation"),
            "confidence_score": data.get("confidence_score"),
        }, tokens

    def usage_stats(self, user) -> dict:
        today = timezone.now().date()
        generations = AIGeneration.objects.filter(user=user, created_at__date=today)
        used = generations.count()
        tokens = sum(g.tokens_used or 0 for g in generations)
        return {
            "generations_today": used,
            "tokens_used_today": tokens,
            "daily_limit": settings.DAILY_AI_LIMIT,
            "remaining": max(0, settings.DAILY_AI_LIMIT - used),
        }


class AIJobService:
    def __init__(self, card_service: AICardService | None = None):
        self.card_service = card_service or AICardService()

    def enqueue_text_generation(self, user, text: str, count: int, deck: Deck | None = None) -> AIGeneration:
        return AIGeneration.objects.create(
            user=user,
            deck=deck,
            prompt=text,
            generation_type="text",
            input_payload={"text": text, "count": count},
            status="pending",
            provider=settings.AI_PROVIDER,
            ai_provider=settings.AI_PROVIDER,
            model_name=settings.CEREBRAS_MODEL,
            generated_cards=[],
        )

    def process_one(self, generation: AIGeneration) -> AIGeneration:
        generation.status = "processing"
        generation.save(update_fields=["status", "updated_at"])
        start = time.perf_counter()
        try:
            payload = generation.input_payload or {}
            if generation.generation_type == "topic":
                cards, tokens = self.card_service.generate_cards_from_topic(
                    payload["topic"],
                    payload.get("count", 10),
                    payload.get("language", "en"),
                    payload.get("target_language", "fa"),
                    payload.get("level", "beginner"),
                )
            else:
                cards, tokens = self.card_service.generate_cards_from_text(payload["text"], payload.get("count", 10))
            with transaction.atomic():
                if generation.deck:
                    for card in cards:
                        Card.objects.create(
                            deck=generation.deck,
                            front=card["front"],
                            back=card["back"]["definition"],
                            example_sentence=(card["back"].get("examples") or [{}])[0].get("text"),
                            pronunciation=(card["back"].get("pronunciation") or {}).get("text"),
                            difficulty=card["difficulty"],
                        )
                generation.generated_cards = cards
                generation.cards_accepted = len(cards) if generation.deck else 0
                generation.tokens_used = tokens
                generation.result = {"cards": cards}
                generation.status = "completed"
                generation.latency_ms = int((time.perf_counter() - start) * 1000)
                generation.error_message = None
                generation.save()
        except Exception as exc:
            generation.status = "failed"
            generation.error_message = str(exc)
            generation.latency_ms = int((time.perf_counter() - start) * 1000)
            generation.save(update_fields=["status", "error_message", "latency_ms", "updated_at"])
        return generation

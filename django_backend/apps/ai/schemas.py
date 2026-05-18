from __future__ import annotations

from rest_framework import serializers


LEVELS = ["beginner", "intermediate", "advanced"]


class TTSField(serializers.Serializer):
    text = serializers.CharField()
    lang = serializers.CharField(default="en-US")


class PronunciationField(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hint = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tts = TTSField(required=False, allow_null=True)


class ExampleField(serializers.Serializer):
    text = serializers.CharField()
    tts = TTSField(required=False, allow_null=True)


class CardBackField(serializers.Serializer):
    definition = serializers.CharField(allow_blank=True)
    pronunciation = PronunciationField(required=False, allow_null=True)
    part_of_speech = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    usage = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    examples = ExampleField(many=True, required=False)
    memory_tip = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class GeneratedCardField(serializers.Serializer):
    front = serializers.CharField()
    back = CardBackField()
    difficulty = serializers.ChoiceField(choices=["easy", "medium", "hard"], default="medium")


class GenerateCardRequest(serializers.Serializer):
    term = serializers.CharField(min_length=1, max_length=500)
    language = serializers.CharField(min_length=2, max_length=10, default="en", required=False)
    target_language = serializers.CharField(min_length=2, max_length=10, default="fa", required=False)
    level = serializers.ChoiceField(choices=LEVELS, default="beginner", required=False)


class GenerateTopicRequest(serializers.Serializer):
    topic = serializers.CharField(min_length=1, max_length=500)
    count = serializers.IntegerField(min_value=1, max_value=20, default=10, required=False)
    language = serializers.CharField(min_length=2, max_length=10, default="en", required=False)
    target_language = serializers.CharField(min_length=2, max_length=10, default="fa", required=False)
    level = serializers.ChoiceField(choices=LEVELS, default="beginner", required=False)
    deck_id = serializers.UUIDField(required=False, allow_null=True)


class GenerateTextRequest(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=5000)
    count = serializers.IntegerField(min_value=1, max_value=20, default=10, required=False)
    deck_id = serializers.UUIDField(required=False, allow_null=True)


class AnalyzeSentenceRequest(serializers.Serializer):
    sentence = serializers.CharField(min_length=1, max_length=1000)
    target_word = serializers.CharField(min_length=1, max_length=120)


class PracticeSentenceRequest(serializers.Serializer):
    target_word = serializers.CharField(min_length=1, max_length=120)
    user_sentence = serializers.CharField(min_length=5, max_length=500)
    language = serializers.CharField(min_length=2, max_length=10, default="en", required=False)

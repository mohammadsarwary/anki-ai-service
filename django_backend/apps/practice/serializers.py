from rest_framework import serializers


class PracticeFeedbackRequest(serializers.Serializer):
    card_id = serializers.UUIDField(required=False, allow_null=True)
    correct_answer = serializers.CharField(min_length=1)
    user_answer = serializers.CharField(min_length=1)
    language = serializers.CharField(max_length=10, default="en", required=False, allow_null=True)
    context = serializers.DictField(required=False, allow_null=True)


class SentencePracticeRequest(serializers.Serializer):
    target_word = serializers.CharField(max_length=100)
    user_sentence = serializers.CharField(max_length=500)
    card_id = serializers.UUIDField(required=False, allow_null=True)
    language = serializers.CharField(max_length=10, default="en", required=False, allow_null=True)

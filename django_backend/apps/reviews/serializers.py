from __future__ import annotations

from rest_framework import serializers

from apps.decks.serializers import CardSerializer
from apps.reviews.models import Review, ReviewState


class ReviewStateSerializer(serializers.ModelSerializer):
    ease_factor = serializers.FloatField()
    is_due = serializers.BooleanField(read_only=True)
    card = CardSerializer(read_only=True)

    class Meta:
        model = ReviewState
        fields = [
            "id",
            "card_id",
            "user_id",
            "interval_minutes",
            "next_review_at",
            "ease_factor",
            "repetition_count",
            "last_reviewed_at",
            "is_due",
            "card",
        ]


class ReviewSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "card_id", "user_id", "rating", "response_time_ms", "reviewed_at", "created_at", "card"]


class ReviewSubmitSerializer(serializers.Serializer):
    card_id = serializers.UUIDField()
    rating = serializers.ChoiceField(choices=["again", "hard", "good", "easy"])
    response_time_ms = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    client_review_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)

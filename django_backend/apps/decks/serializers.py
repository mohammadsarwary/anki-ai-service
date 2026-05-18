from __future__ import annotations

from rest_framework import serializers

from apps.decks.models import Card, Category, Deck


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description", "deck_count", "created_at", "updated_at"]


class CardSerializer(serializers.ModelSerializer):
    deck_id = serializers.UUIDField(required=False)

    class Meta:
        model = Card
        fields = [
            "id",
            "deck_id",
            "front",
            "back",
            "example_sentence",
            "pronunciation",
            "audio_url",
            "image_url",
            "difficulty",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DeckSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)
    category_detail = CategorySerializer(source="category_ref", read_only=True)
    category = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = [
            "id",
            "user_id",
            "name",
            "description",
            "is_public",
            "category",
            "category_detail",
            "is_featured",
            "image_url",
            "card_count",
            "created_at",
            "updated_at",
            "cards",
        ]
        read_only_fields = ["id", "user_id", "card_count", "created_at", "updated_at", "cards"]

    def get_category(self, obj):
        if obj.category_ref:
            return CategorySerializer(obj.category_ref).data
        return obj.category


class DeckWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ["name", "description", "is_public", "category", "category_ref", "image_url"]
        extra_kwargs = {field: {"required": False} for field in fields}


class BatchCardSerializer(serializers.Serializer):
    deck_id = serializers.UUIDField()
    cards = serializers.ListField(min_length=1, max_length=50)

    def validate_cards(self, value):
        serializer = CardSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

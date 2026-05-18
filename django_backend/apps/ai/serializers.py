from rest_framework import serializers

from apps.ai.models import AIGeneration


class AIGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIGeneration
        fields = [
            "id",
            "user_id",
            "deck_id",
            "prompt",
            "generated_cards",
            "cards_accepted",
            "ai_provider",
            "tokens_used",
            "status",
            "latency_ms",
            "provider",
            "model_name",
            "error_message",
            "result",
            "created_at",
        ]

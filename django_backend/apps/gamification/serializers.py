from rest_framework import serializers

from apps.gamification.models import Challenge, DailyStreak


class ChallengeSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.IntegerField(read_only=True)
    date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = Challenge
        fields = ["id", "type", "title", "target_count", "current_count", "completed", "progress_percentage", "date", "created_at"]


class DailyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStreak
        fields = ["id", "date", "cards_reviewed", "study_duration_seconds", "created_at"]

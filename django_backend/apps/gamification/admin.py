try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from django.contrib import admin

from apps.gamification.models import Challenge, DailyStreak


@admin.register(DailyStreak)
class DailyStreakAdmin(ModelAdmin):
    list_display = ["user", "date", "cards_reviewed", "study_duration_seconds"]
    list_filter = ["date"]
    search_fields = ["user__email"]


@admin.register(Challenge)
class ChallengeAdmin(ModelAdmin):
    list_display = ["user", "type", "title", "current_count", "target_count", "completed", "date"]
    list_filter = ["type", "completed", "date"]
    search_fields = ["user__email", "title"]

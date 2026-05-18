try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from django.contrib import admin

from apps.reviews.models import Review, ReviewState


@admin.register(ReviewState)
class ReviewStateAdmin(ModelAdmin):
    list_display = ["user", "card", "interval_minutes", "ease_factor", "repetition_count", "next_review_at", "last_reviewed_at"]
    list_filter = ["next_review_at", "last_reviewed_at"]
    search_fields = ["user__email", "card__front"]
    autocomplete_fields = ["user", "card"]


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ["user", "card", "rating", "response_time_ms", "reviewed_at"]
    list_filter = ["rating", "reviewed_at"]
    search_fields = ["user__email", "card__front", "client_review_id"]
    autocomplete_fields = ["user", "card"]

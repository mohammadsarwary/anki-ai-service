from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.ai.models import AIGeneration
from apps.decks.models import Card, Deck
from apps.reviews.models import Review


class AnalyticsService:
    def dashboard_stats(self) -> dict:
        return {
            "total_users": get_user_model().objects.count(),
            "total_decks": Deck.all_objects.count(),
            "total_cards": Card.all_objects.count(),
            "reviews_today": Review.objects.filter(created_at__date=timezone.localdate()).count(),
            "active_users_week": get_user_model().objects.filter(reviews__created_at__gte=timezone.now() - timezone.timedelta(days=7)).distinct().count(),
            "ai_generations_today": AIGeneration.objects.filter(created_at__date=timezone.localdate()).count(),
            "pending_ai_jobs": AIGeneration.objects.filter(status="pending").count(),
            "failed_ai_jobs": AIGeneration.objects.filter(status="failed").count(),
        }

    def series(self, model, days: int = 30):
        start = timezone.localdate() - timezone.timedelta(days=days - 1)
        values = (
            model.objects.filter(created_at__date__gte=start)
            .values("created_at__date")
            .annotate(count=Count("id"))
            .order_by("created_at__date")
        )
        mapped = {item["created_at__date"].isoformat(): item["count"] for item in values}
        return {str(start + timezone.timedelta(days=i)): mapped.get(str(start + timezone.timedelta(days=i)), 0) for i in range(days)}

    def top_users(self, limit: int = 10):
        return get_user_model().objects.annotate(reviews_count=Count("reviews")).order_by("-reviews_count")[:limit]

    def popular_decks(self, limit: int = 10):
        return Deck.objects.filter(is_public=True).annotate(cards_count=Count("cards")).order_by("-cards_count")[:limit]

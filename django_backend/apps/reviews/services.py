from __future__ import annotations

from decimal import Decimal

from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.reviews.models import Review, ReviewState


class SpacedRepetitionService:
    def calculate_next_review(self, state: ReviewState, rating: str) -> dict:
        ease_factor = Decimal(state.ease_factor)
        interval = state.interval_minutes

        if rating == "again":
            ease_factor = max(Decimal("1.3"), ease_factor - Decimal("0.2"))
            interval = 1
        elif rating == "hard":
            ease_factor = max(Decimal("1.3"), ease_factor - Decimal("0.15"))
            interval = 10
        elif rating == "good":
            interval = 1440 if interval == 0 else int(interval * float(ease_factor))
        elif rating == "easy":
            ease_factor = min(Decimal("2.5"), ease_factor + Decimal("0.15"))
            interval = 4320 if interval == 0 else int(interval * float(ease_factor) * 1.3)

        return {
            "interval_minutes": int(interval),
            "ease_factor": round(ease_factor, 2),
            "next_review_at": timezone.now() + timezone.timedelta(minutes=int(interval)),
            "repetition_count": state.repetition_count + 1,
        }


class StatisticsService:
    def get_review_statistics(self, user, period: str = "today") -> dict:
        now = timezone.now()
        if period == "week":
            start = now - timezone.timedelta(days=7)
        elif period == "month":
            start = now - timezone.timedelta(days=30)
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        reviews = Review.objects.filter(user=user, reviewed_at__gte=start)
        total = reviews.count()
        good = reviews.filter(rating__in=["good", "easy"]).count()
        return {
            "total_reviews": total,
            "accuracy": round((good / total) * 100, 2) if total else 0,
            "average_response_time_ms": reviews.aggregate(avg=Avg("response_time_ms"))["avg"] or 0,
            "rating_breakdown": dict(reviews.values_list("rating").annotate(count=Count("id"))),
        }

    def refresh_user_statistics(self, user):
        stats = user.statistics
        total_reviews = Review.objects.filter(user=user).count()
        good_reviews = Review.objects.filter(user=user, rating__in=["good", "easy"]).count()
        stats.total_cards_reviewed = total_reviews
        stats.average_accuracy = round((good_reviews / total_reviews) * 100, 2) if total_reviews else 0
        stats.save()

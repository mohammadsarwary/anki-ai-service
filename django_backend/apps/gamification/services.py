from __future__ import annotations

from django.db.models import Sum
from django.utils import timezone

from apps.gamification.models import Challenge, DailyStreak


class StreakService:
    def record_session(self, user, cards_reviewed: int = 0, study_duration_seconds: int = 0):
        today = timezone.localdate()
        streak, _ = DailyStreak.objects.get_or_create(user=user, date=today)
        streak.cards_reviewed += cards_reviewed
        streak.study_duration_seconds += study_duration_seconds
        streak.save()
        self.refresh_user_streak(user)
        return streak

    def refresh_user_streak(self, user):
        today = timezone.localdate()
        stats = user.statistics
        current = 0
        cursor = today
        while DailyStreak.objects.filter(user=user, date=cursor).exists():
            current += 1
            cursor -= timezone.timedelta(days=1)
        stats.current_streak = current
        stats.longest_streak = max(stats.longest_streak, current)
        stats.total_study_time_seconds = DailyStreak.objects.filter(user=user).aggregate(total=Sum("study_duration_seconds"))["total"] or 0
        stats.save()


class ChallengeService:
    DEFAULTS = [
        ("finish_review", "Finish today's reviews", 10),
        ("daily_goal", "Study for 10 minutes", 600),
    ]

    def ensure_daily_challenges(self, user):
        today = timezone.localdate()
        for challenge_type, title, target in self.DEFAULTS:
            Challenge.objects.get_or_create(
                user=user,
                type=challenge_type,
                date=today,
                defaults={"title": title, "target_count": target},
            )
        return Challenge.objects.filter(user=user, date=today)

    def increment_review_challenges(self, user, amount: int = 1):
        for challenge in self.ensure_daily_challenges(user).filter(type="finish_review", completed=False):
            challenge.current_count += amount
            challenge.completed = challenge.current_count >= challenge.target_count
            challenge.save(update_fields=["current_count", "completed", "updated_at"])

    def increment_study_challenges(self, user, seconds: int):
        for challenge in self.ensure_daily_challenges(user).filter(type="daily_goal", completed=False):
            challenge.current_count += seconds
            challenge.completed = challenge.current_count >= challenge.target_count
            challenge.save(update_fields=["current_count", "completed", "updated_at"])

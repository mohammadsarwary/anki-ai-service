from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.gamification.services import ChallengeService


class Command(BaseCommand):
    help = "Create missing daily challenges for active users."

    def handle(self, *args, **options):
        count = 0
        for user in get_user_model().objects.filter(is_active=True):
            ChallengeService().ensure_daily_challenges(user)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Generated challenges for {count} users"))

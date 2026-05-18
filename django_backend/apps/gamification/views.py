from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gamification.models import Challenge, DailyStreak
from apps.gamification.serializers import ChallengeSerializer, DailyStreakSerializer
from apps.gamification.services import ChallengeService, StreakService


class CurrentStreakView(APIView):
    def get(self, request):
        today = timezone.localdate()
        streak = DailyStreak.objects.filter(user=request.user, date=today).first()
        return Response(
            {
                "success": True,
                "data": {
                    "current_streak": request.user.statistics.current_streak,
                    "longest_streak": request.user.statistics.longest_streak,
                    "today": DailyStreakSerializer(streak).data if streak else None,
                },
            }
        )


class RecordSessionView(APIView):
    def post(self, request):
        cards = int(request.data.get("cards_reviewed", 0) or 0)
        seconds = int(request.data.get("study_duration_seconds", 0) or 0)
        streak = StreakService().record_session(request.user, cards_reviewed=cards, study_duration_seconds=seconds)
        ChallengeService().increment_study_challenges(request.user, seconds)
        return Response({"success": True, "data": DailyStreakSerializer(streak).data})


class DailyChallengesView(APIView):
    def get(self, request):
        challenges = ChallengeService().ensure_daily_challenges(request.user)
        return Response({"success": True, "data": ChallengeSerializer(challenges, many=True).data})


class CompleteChallengeView(APIView):
    def post(self, request, pk):
        challenge = get_object_or_404(Challenge, pk=pk, user=request.user)
        challenge.current_count = challenge.target_count
        challenge.completed = True
        challenge.save(update_fields=["current_count", "completed", "updated_at"])
        return Response({"success": True, "data": ChallengeSerializer(challenge).data})

from django.urls import path

from apps.gamification.views import CompleteChallengeView, CurrentStreakView, DailyChallengesView, RecordSessionView

urlpatterns = [
    path("streaks/current", CurrentStreakView.as_view()),
    path("streaks/record-session", RecordSessionView.as_view()),
    path("challenges/daily", DailyChallengesView.as_view()),
    path("challenges/<uuid:pk>/complete", CompleteChallengeView.as_view()),
]

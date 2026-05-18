from django.urls import path

from apps.reviews.views import DeckDueCardsView, DueTodayView, ReviewHistoryView, ReviewStatisticsView, ReviewSubmitView

urlpatterns = [
    path("reviews/", ReviewSubmitView.as_view()),
    path("reviews", ReviewSubmitView.as_view()),
    path("reviews/due-today", DueTodayView.as_view()),
    path("reviews/history", ReviewHistoryView.as_view()),
    path("reviews/statistics", ReviewStatisticsView.as_view()),
    path("decks/<uuid:deck_id>/due-cards", DeckDueCardsView.as_view()),
]

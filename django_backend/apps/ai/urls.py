from django.urls import path

from apps.ai.views import (
    AnalyzeSentenceView,
    GenerateCardView,
    GenerateFlashcardsV1View,
    GenerateFromTextView,
    GenerateFromTopicV1View,
    GenerateFromTopicView,
    GenerationDetailView,
    ImproveCardView,
    UsageView,
)

urlpatterns = [
    path("ai/generate-from-text", GenerateFromTextView.as_view()),
    path("ai/generate-from-topic", GenerateFromTopicView.as_view()),
    path("ai/generate-card", GenerateCardView.as_view()),
    path("ai/analyze-sentence", AnalyzeSentenceView.as_view()),
    path("ai/improve-card", ImproveCardView.as_view()),
    path("ai/usage", UsageView.as_view()),
    path("ai/generations/<uuid:pk>", GenerationDetailView.as_view()),
    path("v1/generate-flashcards", GenerateFlashcardsV1View.as_view()),
    path("v1/generate-from-topic", GenerateFromTopicV1View.as_view()),
]

from django.urls import path

from apps.practice.views import GeneratePracticeSentenceV1View, PracticeFeedbackView, SentencePracticeView

urlpatterns = [
    path("ai/practice-feedback", PracticeFeedbackView.as_view()),
    path("ai/sentence-practice", SentencePracticeView.as_view()),
    path("v1/generate-practice-sentence", GeneratePracticeSentenceV1View.as_view()),
]

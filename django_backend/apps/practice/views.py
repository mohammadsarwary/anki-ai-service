from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.schemas import PracticeSentenceRequest as V1PracticeSentenceRequest
from apps.ai.views import ai_error_response, validation_response
from apps.ai.services import AICardService
from apps.decks.models import Card
from apps.decks.views import require_owner
from apps.practice.serializers import PracticeFeedbackRequest, SentencePracticeRequest


class PracticeFeedbackView(APIView):
    def post(self, request):
        serializer = PracticeFeedbackRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            feedback, _tokens = AICardService().practice_feedback(
                correct_answer=data["correct_answer"],
                user_answer=data["user_answer"],
                language=data.get("language") or "en",
                context=data.get("context"),
            )
            return Response({"success": True, "data": feedback})
        except Exception as exc:
            return Response({"success": False, "message": "Unable to generate practice feedback at this time."}, status=500)


class SentencePracticeView(APIView):
    def post(self, request):
        serializer = SentencePracticeRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get("card_id"):
            card = get_object_or_404(Card.objects.select_related("deck"), pk=data["card_id"])
            require_owner(request.user, card.deck)
        try:
            result, _tokens = AICardService().practice_sentence(
                target_word=data["target_word"],
                user_sentence=data["user_sentence"],
                language=data.get("language") or "en",
            )
            return Response({"success": True, "data": result})
        except Exception:
            return Response({"success": False, "message": "Unable to evaluate your sentence at this time. Please try again."}, status=500)


class GeneratePracticeSentenceV1View(APIView):
    def post(self, request):
        serializer = V1PracticeSentenceRequest(data=request.data)
        if not serializer.is_valid():
            return validation_response(serializer)
        try:
            result, _tokens = AICardService().practice_sentence(**serializer.validated_data)
            return Response({"success": True, "data": result})
        except Exception as exc:
            return ai_error_response(exc)

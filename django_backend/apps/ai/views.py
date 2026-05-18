from __future__ import annotations

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.exceptions import AIError
from apps.ai.models import AIGeneration
from apps.ai.schemas import AnalyzeSentenceRequest, GenerateCardRequest, GenerateTextRequest, GenerateTopicRequest
from apps.ai.serializers import AIGenerationSerializer
from apps.ai.services import AICardService, AIJobService
from apps.decks.models import Card, Deck
from apps.decks.views import require_owner


def ai_error_response(exc: Exception):
    if isinstance(exc, AIError):
        return Response({"error": exc.detail}, status=exc.status_code)
    return Response({"error": str(exc)}, status=500)


def validation_response(serializer):
    return Response({"detail": serializer.errors, "type": "validation_error"}, status=422)


class GenerateCardView(APIView):
    def post(self, request):
        serializer = GenerateCardRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            card, _tokens = AICardService().generate_card(**serializer.validated_data)
            return Response(card)
        except Exception as exc:
            return ai_error_response(exc)


class GenerateFromTopicView(APIView):
    def post(self, request):
        serializer = GenerateTopicRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cards, tokens = AICardService().generate_cards_from_topic(**{k: v for k, v in serializer.validated_data.items() if k != "deck_id"})
            return Response({"cards": cards, "tokens_used": tokens})
        except Exception as exc:
            return ai_error_response(exc)


class GenerateFromTextView(APIView):
    def post(self, request):
        stats = AICardService().usage_stats(request.user)
        if stats["remaining"] <= 0:
            return Response({"success": False, "message": "Daily AI generation limit exceeded"}, status=429)

        serializer = GenerateTextRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        deck = None
        if serializer.validated_data.get("deck_id"):
            deck = get_object_or_404(Deck, pk=serializer.validated_data["deck_id"])
            require_owner(request.user, deck)
        generation = AIJobService().enqueue_text_generation(
            request.user,
            serializer.validated_data["text"],
            serializer.validated_data.get("count", 10),
            deck,
        )
        return Response(
            {
                "success": True,
                "message": "AI card generation started",
                "data": {"generation_id": str(generation.id), "status": "processing"},
            },
            status=202,
        )


class AnalyzeSentenceView(APIView):
    def post(self, request):
        serializer = AnalyzeSentenceRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data, _tokens = AICardService().analyze_sentence(**serializer.validated_data)
            return Response({"success": True, "data": data})
        except Exception as exc:
            return Response({"success": False, "message": f"Failed to analyze sentence: {exc}"}, status=500)


class ImproveCardView(APIView):
    def post(self, request):
        card_id = request.data.get("card_id")
        if not card_id:
            return Response({"card_id": ["This field is required."]}, status=422)
        card = get_object_or_404(Card.objects.select_related("deck"), pk=card_id)
        require_owner(request.user, card.deck)
        try:
            data, _tokens = AICardService().improve_card(card.front, card.back)
            return Response({"success": True, "data": data})
        except Exception as exc:
            return Response({"success": False, "message": f"Failed to improve card: {exc}"}, status=500)


class UsageView(APIView):
    def get(self, request):
        return Response({"success": True, "data": AICardService().usage_stats(request.user)})


class GenerationDetailView(APIView):
    def get(self, request, pk):
        generation = get_object_or_404(AIGeneration.objects.select_related("deck"), pk=pk, user=request.user)
        return Response({"success": True, "data": AIGenerationSerializer(generation).data})


class GenerateFlashcardsV1View(APIView):
    def post(self, request):
        serializer = GenerateCardRequest(data=request.data)
        if not serializer.is_valid():
            return validation_response(serializer)
        try:
            card, _tokens = AICardService().generate_card(**serializer.validated_data)
            return Response(card)
        except Exception as exc:
            return ai_error_response(exc)


class GenerateFromTopicV1View(APIView):
    def post(self, request):
        serializer = GenerateTopicRequest(data=request.data)
        if not serializer.is_valid():
            return validation_response(serializer)
        try:
            cards, _tokens = AICardService().generate_cards_from_topic(**{k: v for k, v in serializer.validated_data.items() if k != "deck_id"})
            return Response({"cards": cards})
        except Exception as exc:
            return ai_error_response(exc)

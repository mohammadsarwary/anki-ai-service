from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decks.models import Card, Deck
from apps.decks.views import require_owner
from apps.decks.utils import paginated_response
from apps.gamification.services import ChallengeService, StreakService
from apps.reviews.models import Review, ReviewState
from apps.reviews.serializers import ReviewSerializer, ReviewStateSerializer, ReviewSubmitSerializer
from apps.reviews.services import SpacedRepetitionService, StatisticsService


class ReviewSubmitView(APIView):
    def post(self, request):
        serializer = ReviewSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = get_object_or_404(Card.objects.select_related("deck"), pk=serializer.validated_data["card_id"])
        require_owner(request.user, card.deck)

        if client_id := serializer.validated_data.get("client_review_id"):
            existing = Review.objects.filter(client_review_id=client_id, user=request.user).first()
            if existing:
                state = ReviewState.objects.get(card=card, user=request.user)
                return Response(
                    {
                        "success": True,
                        "message": "Review submitted successfully",
                        "data": {"review": ReviewSerializer(existing).data, "review_state": ReviewStateSerializer(state).data},
                    },
                    status=201,
                )

        state, _ = ReviewState.objects.get_or_create(
            card=card,
            user=request.user,
            defaults={"interval_minutes": 0, "next_review_at": timezone.now(), "ease_factor": 2.5, "repetition_count": 0},
        )
        next_review = SpacedRepetitionService().calculate_next_review(state, serializer.validated_data["rating"])
        for field, value in next_review.items():
            setattr(state, field, value)
        state.last_reviewed_at = timezone.now()
        state.save()

        review = Review.objects.create(
            card=card,
            user=request.user,
            rating=serializer.validated_data["rating"],
            response_time_ms=serializer.validated_data.get("response_time_ms"),
            client_review_id=serializer.validated_data.get("client_review_id") or None,
        )
        StatisticsService().refresh_user_statistics(request.user)
        StreakService().record_session(request.user, cards_reviewed=1, study_duration_seconds=0)
        ChallengeService().increment_review_challenges(request.user, amount=1)
        return Response(
            {
                "success": True,
                "message": "Review submitted successfully",
                "data": {"review": ReviewSerializer(review).data, "review_state": ReviewStateSerializer(state).data},
            },
            status=201,
        )


class DueTodayView(APIView):
    def get(self, request):
        states = ReviewState.objects.filter(user=request.user, next_review_at__lte=timezone.now()).select_related("card", "card__deck")
        return Response({"success": True, "data": ReviewStateSerializer(states, many=True).data, "meta": {"total": states.count()}})


class DeckDueCardsView(APIView):
    def get(self, request, deck_id):
        deck = get_object_or_404(Deck, pk=deck_id)
        require_owner(request.user, deck)
        states = ReviewState.objects.filter(user=request.user, card__deck=deck, next_review_at__lte=timezone.now()).select_related("card")
        return Response({"success": True, "data": ReviewStateSerializer(states, many=True).data, "meta": {"total": states.count()}})


class ReviewHistoryView(APIView):
    def get(self, request):
        reviews = Review.objects.filter(user=request.user).select_related("card", "card__deck")
        if card_id := request.query_params.get("card_id"):
            reviews = reviews.filter(card_id=card_id)
        if deck_id := request.query_params.get("deck_id"):
            reviews = reviews.filter(card__deck_id=deck_id)
        if from_date := request.query_params.get("from_date"):
            reviews = reviews.filter(reviewed_at__date__gte=from_date)
        if to_date := request.query_params.get("to_date"):
            reviews = reviews.filter(reviewed_at__date__lte=to_date)
        return paginated_response(reviews.order_by("-reviewed_at"), ReviewSerializer, request, per_page=20)


class ReviewStatisticsView(APIView):
    def get(self, request):
        period = request.query_params.get("period", "today")
        period_stats = StatisticsService().get_review_statistics(request.user, period)
        stats = request.user.statistics
        return Response(
            {
                "success": True,
                "data": {
                    "period_stats": period_stats,
                    "overall_stats": {
                        "total_cards_created": stats.total_cards_created,
                        "total_cards_reviewed": stats.total_cards_reviewed,
                        "total_decks": stats.total_decks,
                        "current_streak": stats.current_streak,
                        "longest_streak": stats.longest_streak,
                        "average_accuracy": float(stats.average_accuracy),
                        "total_study_time_seconds": stats.total_study_time_seconds,
                    },
                },
            }
        )

from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import dateparse, timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decks.models import Card, Deck
from apps.reviews.models import Review, ReviewState
from apps.reviews.serializers import ReviewStateSerializer
from apps.reviews.services import SpacedRepetitionService


def iso(dt):
    return dt.isoformat().replace("+00:00", "Z") if dt else None


class SyncPushView(APIView):
    def post(self, request):
        processed_reviews = []
        conflicts = []
        user = request.user
        with transaction.atomic():
            for review_data in request.data.get("reviews", []):
                client_id = review_data.get("client_review_id")
                if not client_id:
                    conflicts.append({"error": "client_review_id is required"})
                    continue
                existing = Review.objects.filter(client_review_id=client_id).first()
                if existing:
                    processed_reviews.append({"client_review_id": client_id, "status": "already_exists", "review_id": str(existing.id)})
                    continue
                card = get_object_or_404(Card.objects.select_related("deck"), pk=review_data.get("card_id"))
                if card.deck.user_id != user.id:
                    conflicts.append({"client_review_id": client_id, "error": "Card does not belong to user"})
                    continue
                state, _ = ReviewState.objects.get_or_create(
                    card=card,
                    user=user,
                    defaults={"interval_minutes": 0, "next_review_at": timezone.now(), "ease_factor": 2.5},
                )
                next_review = SpacedRepetitionService().calculate_next_review(state, review_data["rating"])
                for field, value in next_review.items():
                    setattr(state, field, value)
                state.last_reviewed_at = dateparse.parse_datetime(review_data.get("reviewed_at")) or timezone.now()
                state.last_synced_at = timezone.now()
                state.save()
                review = Review.objects.create(
                    client_review_id=client_id,
                    card=card,
                    user=user,
                    rating=review_data["rating"],
                    response_time_ms=review_data.get("response_time_ms"),
                    reviewed_at=state.last_reviewed_at,
                )
                processed_reviews.append(
                    {
                        "client_review_id": client_id,
                        "status": "created",
                        "review_id": str(review.id),
                        "authoritative_state": {
                            "interval_minutes": state.interval_minutes,
                            "next_review_at": iso(state.next_review_at),
                            "ease_factor": float(state.ease_factor),
                            "repetition_count": state.repetition_count,
                        },
                    }
                )

            for state_data in request.data.get("review_states", []):
                card = get_object_or_404(Card.objects.select_related("deck"), pk=state_data.get("card_id"))
                if card.deck.user_id != user.id:
                    continue
                ReviewState.objects.update_or_create(
                    card=card,
                    user=user,
                    defaults={
                        "interval_minutes": state_data.get("interval_minutes", 0),
                        "next_review_at": dateparse.parse_datetime(state_data.get("next_review_at") or "") or timezone.now(),
                        "ease_factor": state_data.get("ease_factor", 2.5),
                        "repetition_count": state_data.get("repetition_count", 0),
                        "last_reviewed_at": dateparse.parse_datetime(state_data.get("last_reviewed_at") or "") if state_data.get("last_reviewed_at") else None,
                        "last_synced_at": timezone.now(),
                    },
                )
            user.sync_cursor = timezone.now()
            user.save(update_fields=["sync_cursor", "updated_at"])
        return Response(
            {
                "success": True,
                "message": "Sync push completed",
                "data": {"processed_reviews": processed_reviews, "conflicts": conflicts, "server_timestamp": iso(timezone.now())},
            }
        )


class SyncPullView(APIView):
    def get(self, request):
        since = dateparse.parse_datetime(request.query_params.get("since") or "") if request.query_params.get("since") else None
        states = ReviewState.objects.filter(user=request.user).select_related("card")
        cards = Card.objects.filter(deck__user=request.user)
        decks = Deck.objects.filter(user=request.user)
        deleted_cards = Card.all_objects.deleted().filter(deck__user=request.user)
        deleted_decks = Deck.all_objects.deleted().filter(user=request.user)
        if since:
            states = states.filter(updated_at__gt=since)
            cards = cards.filter(updated_at__gt=since)
            decks = decks.filter(updated_at__gt=since)
            deleted_cards = deleted_cards.filter(deleted_at__gt=since)
            deleted_decks = deleted_decks.filter(deleted_at__gt=since)
        data = {
            "review_states": [
                {
                    "id": str(state.id),
                    "card_id": str(state.card_id),
                    "interval_minutes": state.interval_minutes,
                    "next_review_at": iso(state.next_review_at),
                    "ease_factor": float(state.ease_factor),
                    "repetition_count": state.repetition_count,
                    "last_reviewed_at": iso(state.last_reviewed_at),
                    "updated_at": iso(state.updated_at),
                }
                for state in states
            ],
            "deleted_cards": [str(card.id) for card in deleted_cards],
            "deleted_decks": [str(deck.id) for deck in deleted_decks],
            "cards": [
                {
                    "id": str(card.id),
                    "deck_id": str(card.deck_id),
                    "front": card.front,
                    "back": card.back,
                    "example_sentence": card.example_sentence,
                    "updated_at": iso(card.updated_at),
                }
                for card in cards
            ],
            "decks": [
                {
                    "id": str(deck.id),
                    "name": deck.name,
                    "description": deck.description,
                    "is_public": deck.is_public,
                    "updated_at": iso(deck.updated_at),
                }
                for deck in decks
            ],
        }
        return Response({"success": True, "data": data, "meta": {"server_timestamp": iso(timezone.now()), "since": iso(since)}})

from __future__ import annotations

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decks.models import Card, Category, Deck
from apps.decks.serializers import BatchCardSerializer, CardSerializer, CategorySerializer, DeckSerializer, DeckWriteSerializer
from apps.decks.utils import paginated_response


def require_owner(user, deck: Deck):
    if deck.user_id != user.id:
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("This resource does not belong to the authenticated user.")


class DeckListCreateView(APIView):
    def get(self, request):
        decks = Deck.objects.filter(user=request.user).prefetch_related("cards").order_by("-created_at")
        return paginated_response(decks, DeckSerializer, request, per_page=15)

    def post(self, request):
        serializer = DeckWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deck = serializer.save(user=request.user)
        stats = getattr(request.user, "statistics", None)
        if stats:
            stats.total_decks = Deck.objects.filter(user=request.user).count()
            stats.save(update_fields=["total_decks", "updated_at"])
        return Response({"success": True, "message": "Deck created successfully", "data": DeckSerializer(deck).data}, status=201)


class DeckDetailView(APIView):
    def get_object(self, request, pk):
        deck = get_object_or_404(Deck.objects.prefetch_related("cards"), pk=pk)
        require_owner(request.user, deck)
        return deck

    def get(self, request, pk):
        return Response({"success": True, "data": DeckSerializer(self.get_object(request, pk)).data})

    def put(self, request, pk):
        deck = self.get_object(request, pk)
        serializer = DeckWriteSerializer(deck, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Deck updated successfully", "data": DeckSerializer(deck).data})

    def delete(self, request, pk):
        self.get_object(request, pk).delete()
        return Response({"success": True, "message": "Deck deleted successfully"})


class CardListCreateView(APIView):
    def get(self, request):
        cards = Card.objects.select_related("deck").filter(deck__user=request.user)
        if deck_id := request.query_params.get("deck_id"):
            deck = get_object_or_404(Deck, pk=deck_id)
            require_owner(request.user, deck)
            cards = cards.filter(deck_id=deck_id)
        return paginated_response(cards.order_by("-created_at"), CardSerializer, request, per_page=20)

    def post(self, request):
        serializer = CardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deck_id = serializer.validated_data.pop("deck_id", None)
        if not deck_id:
            return Response({"deck_id": ["This field is required."]}, status=422)
        deck = get_object_or_404(Deck, pk=deck_id)
        require_owner(request.user, deck)
        card = serializer.save(deck=deck)
        stats = getattr(request.user, "statistics", None)
        if stats:
            stats.total_cards_created = Card.objects.filter(deck__user=request.user).count()
            stats.save(update_fields=["total_cards_created", "updated_at"])
        return Response({"success": True, "message": "Card created successfully", "data": CardSerializer(card).data}, status=201)


class CardDetailView(APIView):
    def get_object(self, request, pk):
        card = get_object_or_404(Card.objects.select_related("deck"), pk=pk)
        require_owner(request.user, card.deck)
        return card

    def get(self, request, pk):
        return Response({"success": True, "data": CardSerializer(self.get_object(request, pk)).data})

    def put(self, request, pk):
        card = self.get_object(request, pk)
        serializer = CardSerializer(card, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Card updated successfully", "data": CardSerializer(card).data})

    def delete(self, request, pk):
        self.get_object(request, pk).delete()
        return Response({"success": True, "message": "Card deleted successfully"})


class CardBatchView(APIView):
    def post(self, request):
        serializer = BatchCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deck = get_object_or_404(Deck, pk=serializer.validated_data["deck_id"])
        require_owner(request.user, deck)
        created = []
        with transaction.atomic():
            for card_data in serializer.validated_data["cards"]:
                created.append(Card.objects.create(deck=deck, **card_data))
        return Response(
            {
                "success": True,
                "message": f"{len(created)} cards created successfully",
                "data": CardSerializer(created, many=True).data,
            },
            status=201,
        )


class DiscoverDecksView(APIView):
    def get(self, request):
        decks = Deck.objects.filter(is_public=True).select_related("category_ref")
        if category_id := request.query_params.get("category_id"):
            decks = decks.filter(category_ref_id=category_id)
        if search := request.query_params.get("search"):
            decks = decks.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return paginated_response(decks.order_by("-created_at"), DeckSerializer, request, per_page=15)


class FeaturedDecksView(APIView):
    def get(self, request):
        decks = Deck.objects.filter(is_public=True, is_featured=True).select_related("category_ref")[:10]
        return Response({"success": True, "data": DeckSerializer(decks, many=True).data})


class RecommendedDecksView(APIView):
    def get(self, request):
        decks = Deck.objects.filter(is_public=True).select_related("category_ref").order_by("-card_count")[:10]
        return Response({"success": True, "data": DeckSerializer(decks, many=True).data})


class TrendingDecksView(APIView):
    def get(self, request):
        decks = Deck.objects.filter(is_public=True).annotate(cards_count=Count("cards")).order_by("-cards_count")[:10]
        return Response({"success": True, "data": DeckSerializer(decks, many=True).data})


class SearchDecksView(APIView):
    def get(self, request):
        q = request.query_params.get("q")
        if not q:
            return Response({"q": ["This field is required."]}, status=422)
        decks = Deck.objects.filter(is_public=True).filter(Q(name__icontains=q) | Q(description__icontains=q))
        return Response({"success": True, "data": DeckSerializer(decks, many=True).data})


class CloneDeckView(APIView):
    def post(self, request, pk):
        original = get_object_or_404(Deck.objects.prefetch_related("cards"), pk=pk, is_public=True)
        with transaction.atomic():
            clone = Deck.objects.create(
                user=request.user,
                name=original.name,
                description=original.description,
                category=original.category,
                category_ref=original.category_ref,
                image_url=original.image_url,
            )
            for card in original.cards.all():
                Card.objects.create(
                    deck=clone,
                    front=card.front,
                    back=card.back,
                    example_sentence=card.example_sentence,
                    pronunciation=card.pronunciation,
                    audio_url=card.audio_url,
                    image_url=card.image_url,
                    difficulty=card.difficulty,
                    tags=card.tags,
                )
        return Response({"success": True, "message": "Deck cloned successfully", "data": DeckSerializer(clone).data}, status=201)


class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        return Response({"success": True, "data": CategorySerializer(categories, many=True).data})


class CategoryDetailView(APIView):
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        return Response({"success": True, "data": CategorySerializer(category).data})


class CategoryDecksView(APIView):
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        decks = Deck.objects.filter(is_public=True, category_ref=category)
        return paginated_response(decks, DeckSerializer, request, per_page=15)

from __future__ import annotations

import json
from typing import Any

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.ai.services import AICardService
from apps.decks.models import Card, Deck
from apps.web.forms import AIGenerateForm, CardForm, CardImportForm, DeckForm, LoginForm
from apps.web.utils import form_errors, format_ai_back_content, parse_card_import_content


def home(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("web:login")
    decks = Deck.objects.filter(user=request.user).order_by("-updated_at", "-created_at")
    user_cards = Card.objects.filter(deck__user=request.user)
    cards = user_cards.select_related("deck").order_by("-updated_at")[:6]
    ai_card_count = sum(1 for tags in user_cards.values_list("tags", flat=True) if "source:ai" in (tags or []))
    stats = {
        "decks": decks.count(),
        "cards": user_cards.count(),
        "easy": user_cards.filter(difficulty="easy").count(),
        "ai": ai_card_count,
    }
    return render(
        request,
        "web/home.html",
        {
            "active_nav": "home",
            "decks": decks[:5],
            "recent_cards": cards,
            "stats": stats,
        },
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("web:cards")
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        return redirect(request.GET.get("next") or "web:cards")
    return render(request, "web/login.html", {"form": form})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("web:login")


@login_required
def cards_redirect(request: HttpRequest) -> HttpResponse:
    deck = Deck.objects.filter(user=request.user).order_by("-updated_at", "-created_at").first()
    if deck:
        return redirect("web:deck_cards", deck_id=deck.id)
    return render_cards_page(request, selected_deck=None, cards=Card.objects.none())


@login_required
def decks_view(request: HttpRequest) -> HttpResponse:
    return render_decks_page(request, deck_form=DeckForm())


def render_decks_page(request: HttpRequest, *, deck_form: DeckForm, status: int = 200, show_deck_modal: bool = False) -> HttpResponse:
    decks = Deck.objects.filter(user=request.user).order_by("-updated_at", "-created_at")
    deck_count = decks.count()
    return render(
        request,
        "web/decks.html",
        {
            "active_nav": "decks",
            "decks": decks,
            "deck_count": deck_count,
            "public_decks": decks.filter(is_public=True).count(),
            "private_decks": decks.filter(is_public=False).count(),
            "total_cards": Card.objects.filter(deck__user=request.user).count(),
            "deck_form": deck_form,
            "show_deck_modal": show_deck_modal,
        },
        status=status,
    )


@login_required
def ai_page(request: HttpRequest) -> HttpResponse:
    decks = Deck.objects.filter(user=request.user).order_by("-updated_at", "-created_at")
    selected_deck = None
    requested_deck_id = request.GET.get("deck_id")
    if requested_deck_id:
        selected_deck = decks.filter(id=requested_deck_id).first()
    if selected_deck is None:
        selected_deck = decks.first()
    return render(
        request,
        "web/ai.html",
        {
            "active_nav": "ai",
            "decks": decks,
            "selected_deck": selected_deck,
            "selected_deck_id": selected_deck.id if selected_deck else None,
            "cards_json": [],
            "ai_form": AIGenerateForm(initial={"count": 10, "language": "en", "target_language": "fa", "level": "beginner"}),
        },
    )


@login_required
def deck_cards_view(request: HttpRequest, deck_id) -> HttpResponse:
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    cards = deck.cards.all().order_by("-updated_at", "-created_at")
    query = request.GET.get("q", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()
    if query:
        cards = cards.filter(Q(front__icontains=query) | Q(back__icontains=query))
    if difficulty in {"easy", "medium", "hard"}:
        cards = cards.filter(difficulty=difficulty)
    return render_cards_page(request, selected_deck=deck, cards=cards)


def render_cards_page(request: HttpRequest, *, selected_deck: Deck | None, cards) -> HttpResponse:
    decks = Deck.objects.filter(user=request.user).order_by("-updated_at", "-created_at")
    selected_deck_id = selected_deck.id if selected_deck else None
    stats = {"total": 0, "easy": 0, "medium": 0, "hard": 0}
    if selected_deck:
        aggregates = selected_deck.cards.aggregate(
            total=Count("id"),
            easy=Count("id", filter=Q(difficulty="easy")),
            medium=Count("id", filter=Q(difficulty="medium")),
            hard=Count("id", filter=Q(difficulty="hard")),
        )
        stats.update({key: aggregates.get(key) or 0 for key in stats})

    cards_list = list(cards)
    cards_json = [
        {
            "id": str(card.id),
            "front": card.front,
            "back": card.back,
            "difficulty": card.difficulty or "",
            "tags": ", ".join(card.tags or []),
            "example_sentence": card.example_sentence or "",
            "pronunciation": card.pronunciation or "",
            "update_url": reverse("web:card_update", args=[card.id]),
            "delete_url": reverse("web:card_delete", args=[card.id]),
        }
        for card in cards_list
    ]
    return render(
        request,
        "web/cards.html",
        {
            "decks": decks,
            "selected_deck": selected_deck,
            "selected_deck_id": selected_deck_id,
            "cards": cards_list,
            "cards_json": cards_json,
            "stats": stats,
            "query": request.GET.get("q", ""),
            "difficulty": request.GET.get("difficulty", ""),
            "card_form": CardForm(),
            "import_form": CardImportForm(initial={"skip_duplicates": True}),
            "deck_form": DeckForm(),
            "ai_form": AIGenerateForm(initial={"count": 10, "language": "en", "target_language": "fa", "level": "beginner"}),
            "active_nav": "cards",
        },
    )


@login_required
@require_POST
def create_deck(request: HttpRequest) -> HttpResponse:
    form = DeckForm(request.POST)
    if form.is_valid():
        deck = Deck.objects.create(
            user=request.user,
            name=form.cleaned_data["name"],
            description=form.cleaned_data["description"] or None,
            category=form.cleaned_data["category"] or None,
            is_public=form.cleaned_data["is_public"],
        )
        messages.success(request, "Deck created successfully.")
        return redirect("web:deck_cards", deck_id=deck.id)
    messages.error(request, "Please add a deck name.")
    return render_decks_page(request, deck_form=form, status=422, show_deck_modal=True)


@login_required
@require_POST
def create_card(request: HttpRequest, deck_id) -> HttpResponse:
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    form = CardForm(request.POST)
    if form.is_valid():
        Card.objects.create(deck=deck, **_card_payload(form.cleaned_data))
        messages.success(request, "Card created successfully.")
    else:
        messages.error(request, "Please complete the required card fields.")
    return redirect("web:deck_cards", deck_id=deck.id)


@login_required
@require_POST
def import_cards(request: HttpRequest, deck_id) -> HttpResponse:
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    form = CardImportForm(request.POST, request.FILES)
    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]
        messages.error(request, str(first_error))
        return redirect("web:deck_cards", deck_id=deck.id)

    parsed_cards, skipped_rows = parse_card_import_content(
        form.source_text(),
        default_difficulty=form.cleaned_data.get("default_difficulty") or "",
        default_tags=form.cleaned_data.get("default_tags") or [],
    )
    if not parsed_cards:
        messages.error(request, "No valid cards found. Use front/back columns or front - back lines.")
        return redirect("web:deck_cards", deck_id=deck.id)

    existing_fronts = set()
    if form.cleaned_data.get("skip_duplicates"):
        existing_fronts = {front.casefold() for front in deck.cards.values_list("front", flat=True)}

    created = 0
    skipped_duplicates = 0
    with transaction.atomic():
        for card_data in parsed_cards:
            front_key = card_data["front"].casefold()
            if front_key in existing_fronts:
                skipped_duplicates += 1
                continue
            Card.objects.create(deck=deck, **card_data)
            existing_fronts.add(front_key)
            created += 1

    skipped_total = skipped_rows + skipped_duplicates
    if created:
        detail = f" Skipped {skipped_total} rows." if skipped_total else ""
        messages.success(request, f"Imported {created} cards.{detail}")
    else:
        messages.error(request, f"No new cards imported. Skipped {skipped_total} rows.")
    return redirect("web:deck_cards", deck_id=deck.id)


@login_required
@require_POST
def update_card(request: HttpRequest, card_id) -> HttpResponse:
    card = get_object_or_404(Card.objects.select_related("deck"), id=card_id, deck__user=request.user)
    form = CardForm(request.POST)
    if form.is_valid():
        for field, value in _card_payload(form.cleaned_data).items():
            setattr(card, field, value)
        card.save()
        messages.success(request, "Card updated successfully.")
    else:
        messages.error(request, "Please complete the required card fields.")
    return redirect("web:deck_cards", deck_id=card.deck_id)


@login_required
@require_POST
def delete_card(request: HttpRequest, card_id) -> HttpResponse:
    card = get_object_or_404(Card.objects.select_related("deck"), id=card_id, deck__user=request.user)
    deck_id = card.deck_id
    card.delete()
    messages.success(request, "Card deleted.")
    return redirect("web:deck_cards", deck_id=deck_id)


@login_required
@require_POST
def ai_generate(request: HttpRequest, deck_id) -> JsonResponse:
    get_object_or_404(Deck, id=deck_id, user=request.user)
    form = AIGenerateForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form_errors(form)}, status=422)
    try:
        cards, tokens = AICardService().generate_cards_from_topic(**form.cleaned_data)
    except Exception as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=500)
    return JsonResponse({"success": True, "cards": cards, "tokens_used": tokens})


@login_required
@require_POST
def ai_save(request: HttpRequest, deck_id) -> JsonResponse:
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON payload."}, status=400)

    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        return JsonResponse({"success": False, "message": "No cards were provided."}, status=422)

    created_cards = []
    with transaction.atomic():
        for card_data in cards:
            if not isinstance(card_data, dict) or card_data.get("selected") is False:
                continue
            front = str(card_data.get("front") or "").strip()
            back = card_data.get("back") if isinstance(card_data.get("back"), dict) else {}
            if not front or not str(back.get("definition") or "").strip():
                continue
            examples = back.get("examples") if isinstance(back.get("examples"), list) else []
            pronunciation = back.get("pronunciation") if isinstance(back.get("pronunciation"), dict) else {}
            created_cards.append(
                Card.objects.create(
                    deck=deck,
                    front=front,
                    back=format_ai_back_content(back),
                    example_sentence=_first_example(examples),
                    pronunciation=str(pronunciation.get("text") or "").strip() or None,
                    difficulty=card_data.get("difficulty") if card_data.get("difficulty") in {"easy", "medium", "hard"} else "medium",
                    tags=["source:ai"],
                )
            )

    if not created_cards:
        return JsonResponse({"success": False, "message": "No valid selected cards to save."}, status=422)
    return JsonResponse({"success": True, "created": len(created_cards)})


def _card_payload(cleaned_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "front": cleaned_data["front"].strip(),
        "back": cleaned_data["back"].strip(),
        "difficulty": cleaned_data.get("difficulty") or None,
        "tags": cleaned_data.get("tags") or [],
        "example_sentence": (cleaned_data.get("example_sentence") or "").strip() or None,
        "pronunciation": (cleaned_data.get("pronunciation") or "").strip() or None,
    }


def _first_example(examples: list[Any]) -> str | None:
    for example in examples:
        text = example.get("text") if isinstance(example, dict) else example
        text = str(text or "").strip()
        if text:
            return text
    return None

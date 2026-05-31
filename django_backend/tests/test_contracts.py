import bcrypt
import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ai.models import AIGeneration
from apps.ai.services import AICardService
from apps.decks.models import Card, Deck
from apps.gamification.models import Challenge
from apps.reviews.models import Review, ReviewState


@pytest.mark.django_db
def test_auth_register_login_verify_and_logout(api_client):
    response = api_client.post(
        "/api/auth/register",
        {"name": "Test User", "email": "test@example.com", "password": "password123"},
        format="json",
    )
    assert response.status_code == 201
    token = response.data["data"]["token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert api_client.get("/api/auth/me").data["data"]["email"] == "test@example.com"
    verify = api_client.get("/api/auth/verify-token")
    assert verify.data["valid"] is True
    assert verify.data["email"] == "test@example.com"

    logout = api_client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert api_client.get("/api/auth/me").status_code == 403


@pytest.mark.django_db
def test_laravel_bcrypt_password_can_login(api_client):
    raw_hash = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode().replace("$2b$", "$2y$", 1)
    User.objects.create(email="legacy@example.com", name="Legacy", password=raw_hash)

    response = api_client.post("/api/auth/login", {"email": "legacy@example.com", "password": "secret123"}, format="json")

    assert response.status_code == 200
    assert response.data["data"]["token"]


@pytest.mark.django_db
def test_login_does_not_require_csrf_when_browser_session_exists():
    session_user = User.objects.create_user(email="session@example.com", password="password123", name="Session")
    User.objects.create_user(email="login@example.com", password="password123", name="Login")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(session_user)

    response = client.post("/api/auth/login", {"email": "login@example.com", "password": "password123"}, format="json")

    assert response.status_code == 200
    assert response.data["data"]["token"]


@pytest.mark.django_db
def test_deck_and_card_contract(auth_client, user):
    deck_response = auth_client.post("/api/decks", {"name": "English", "description": "Words"}, format="json")
    assert deck_response.status_code == 201
    assert deck_response.data["success"] is True
    deck_id = deck_response.data["data"]["id"]

    card_response = auth_client.post(
        "/api/cards",
        {"deck_id": deck_id, "front": "hello", "back": "سلام", "difficulty": "easy"},
        format="json",
    )
    assert card_response.status_code == 201
    assert card_response.data["data"]["deck_id"] == deck_id

    listing = auth_client.get(f"/api/cards?deck_id={deck_id}")
    assert listing.status_code == 200
    assert listing.data["meta"]["total"] == 1


@pytest.mark.django_db
def test_ai_v1_generate_flashcards_preserves_shape(auth_client, generated_card, monkeypatch):
    def fake_generate_card(self, term, language="en", target_language="fa", level="beginner"):
        return generated_card, 12

    monkeypatch.setattr(AICardService, "generate_card", fake_generate_card)
    response = auth_client.post("/api/v1/generate-flashcards", {"term": "ephemeral", "level": "beginner"}, format="json")

    assert response.status_code == 200
    assert response.data["front"] == "ephemeral"
    assert response.data["back"]["definition"]
    assert response.data["back"]["examples"][0]["text"]


@pytest.mark.django_db
def test_ai_v1_validation_error_shape(auth_client):
    response = auth_client.post("/api/v1/generate-flashcards", {"term": "test", "level": "expert"}, format="json")

    assert response.status_code == 422
    assert response.data["type"] == "validation_error"


@pytest.mark.django_db
def test_generate_from_text_enqueues_db_job(auth_client):
    response = auth_client.post("/api/ai/generate-from-text", {"text": "Python is useful.", "count": 3}, format="json")

    assert response.status_code == 202
    assert response.data["data"]["status"] == "processing"
    assert AIGeneration.objects.filter(id=response.data["data"]["generation_id"], status="pending").exists()


@pytest.mark.django_db
def test_process_ai_jobs_command(auth_client, user, generated_card, monkeypatch):
    deck = Deck.objects.create(user=user, name="AI Deck")
    AIGeneration.objects.create(
        user=user,
        deck=deck,
        prompt="Python",
        generation_type="text",
        input_payload={"text": "Python text", "count": 1},
        status="pending",
    )

    def fake_generate_cards_from_text(self, text, count=10):
        return [generated_card], 33

    monkeypatch.setattr(AICardService, "generate_cards_from_text", fake_generate_cards_from_text)
    call_command("process_ai_jobs", max_seconds=5)

    generation = AIGeneration.objects.get()
    assert generation.status == "completed"
    assert Card.objects.filter(deck=deck, front="ephemeral").exists()


@pytest.mark.django_db
def test_review_submission_updates_authoritative_state(auth_client, user):
    deck = Deck.objects.create(user=user, name="Review Deck")
    card = Card.objects.create(deck=deck, front="hello", back="سلام")

    response = auth_client.post("/api/reviews", {"card_id": str(card.id), "rating": "good", "response_time_ms": 500}, format="json")

    assert response.status_code == 201
    state = ReviewState.objects.get(card=card, user=user)
    assert state.interval_minutes == 1440
    assert Review.objects.filter(card=card, user=user).exists()


@pytest.mark.django_db
def test_sync_pull_returns_active_data_and_deleted_ids(auth_client, user):
    deck = Deck.objects.create(user=user, name="Server Deck")
    card = Card.objects.create(
        deck=deck,
        front="hello",
        back="salam",
        tags=["greeting"],
    )
    deleted_deck = Deck.objects.create(user=user, name="Deleted Deck")
    deleted_card = Card.objects.create(deck=deck, front="bye", back="khodahafez")

    deleted_card.delete()
    deleted_deck.delete()

    response = auth_client.get("/api/sync/pull")

    assert response.status_code == 200
    data = response.data["data"]
    assert data["decks"][0]["id"] == str(deck.id)
    assert data["decks"][0]["cards_count"] == 1
    assert data["decks"][0]["deleted_at"] is None
    assert data["cards"][0]["id"] == str(card.id)
    assert data["cards"][0]["created_at"]
    assert data["cards"][0]["tags"] == ["greeting"]
    assert str(deleted_deck.id) in data["deleted_decks"]
    assert str(deleted_card.id) in data["deleted_cards"]


@pytest.mark.django_db
def test_challenges_and_admin_dashboard(api_client):
    admin = User.objects.create_superuser(email="admin@example.com", password="password123", name="Admin")
    api_client.force_login(admin)

    response = api_client.get("/admin/analytics/")

    assert response.status_code == 200
    assert b"Anki AI Dashboard" in response.content

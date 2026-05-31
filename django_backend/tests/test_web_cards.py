import json

import pytest

from apps.ai.services import AICardService
from apps.accounts.models import User
from apps.decks.models import Card, Deck


@pytest.fixture
def web_client(api_client, user):
    api_client.force_login(user)
    return api_client


@pytest.mark.django_db
def test_web_card_routes_require_login(api_client, user):
    deck = Deck.objects.create(user=user, name="English")

    response = api_client.get(f"/decks/{deck.id}/cards/")

    assert response.status_code == 302
    assert response["Location"].startswith(f"/login/?next=/decks/{deck.id}/cards/")

    create_deck = api_client.post("/decks/create", {"name": "Travel"})
    assert create_deck.status_code == 302
    assert create_deck["Location"].startswith("/login/?next=/decks/create")

    import_cards = api_client.post(f"/decks/{deck.id}/cards/import", {"pasted_cards": "front,back"})
    assert import_cards.status_code == 302
    assert import_cards["Location"].startswith(f"/login/?next=/decks/{deck.id}/cards/import")


@pytest.mark.django_db
def test_web_cards_empty_state_renders(web_client):
    response = web_client.get("/cards/")

    assert response.status_code == 200
    assert b"No decks yet" in response.content


@pytest.mark.django_db
def test_web_deck_create_redirects_to_new_card_management(web_client, user):
    response = web_client.post(
        "/decks/create",
        {
            "name": "Travel English",
            "description": "Airport and hotel words",
            "category": "Travel",
            "is_public": "on",
        },
    )

    deck = Deck.objects.get(user=user, name="Travel English")
    assert response.status_code == 302
    assert response["Location"] == f"/decks/{deck.id}/cards/"
    assert deck.description == "Airport and hotel words"
    assert deck.category == "Travel"
    assert deck.is_public is True
    assert deck.card_count == 0


@pytest.mark.django_db
def test_web_deck_create_validation_reopens_modal(web_client):
    response = web_client.post("/decks/create", {"name": ""})

    assert response.status_code == 422
    assert b"Create a deck" in response.content
    assert b"Deck name is required." in response.content
    assert b'id="new-deck-modal"' in response.content


@pytest.mark.django_db
def test_web_cards_are_owner_scoped(web_client):
    other = User.objects.create_user(email="other@example.com", password="password123", name="Other")
    other_deck = Deck.objects.create(user=other, name="Private")
    other_card = Card.objects.create(deck=other_deck, front="secret", back="hidden")

    assert web_client.get(f"/decks/{other_deck.id}/cards/").status_code == 404
    assert web_client.post(f"/cards/{other_card.id}/update", {"front": "x", "back": "y"}).status_code == 404
    assert web_client.post(f"/cards/{other_card.id}/delete").status_code == 404
    assert web_client.post(f"/decks/{other_deck.id}/cards/import", {"pasted_cards": "front,back\nx,y"}).status_code == 404


@pytest.mark.django_db
def test_web_card_create_update_delete(web_client, user):
    deck = Deck.objects.create(user=user, name="Travel")

    create = web_client.post(
        f"/decks/{deck.id}/cards/create",
        {
            "front": "departure",
            "back": "a flight leaving an airport",
            "difficulty": "easy",
            "tags": "travel, airport",
            "example_sentence": "Our departure is at noon.",
            "pronunciation": "duh-PAR-chur",
        },
    )

    assert create.status_code == 302
    card = Card.objects.get(deck=deck, front="departure")
    assert card.tags == ["travel", "airport"]
    deck.refresh_from_db()
    assert deck.card_count == 1

    page = web_client.get(f"/decks/{deck.id}/cards/")
    assert page.status_code == 200
    assert b"departure" in page.content
    assert b"AI generator" in page.content
    assert b'href="/decks/"' in page.content
    assert b'href="/ai/"' in page.content
    assert b'id="ai-loading" hidden' in page.content
    assert b'id="ai-preview" hidden' in page.content

    update = web_client.post(
        f"/cards/{card.id}/update",
        {
            "front": "arrival",
            "back": "reaching a destination",
            "difficulty": "medium",
            "tags": "travel",
        },
    )

    assert update.status_code == 302
    card.refresh_from_db()
    assert card.front == "arrival"
    assert card.difficulty == "medium"

    delete = web_client.post(f"/cards/{card.id}/delete")

    assert delete.status_code == 302
    assert not Card.objects.filter(id=card.id).exists()
    deck.refresh_from_db()
    assert deck.card_count == 0


@pytest.mark.django_db
def test_web_card_import_creates_cards_from_csv(web_client, user):
    deck = Deck.objects.create(user=user, name="Travel")

    response = web_client.post(
        f"/decks/{deck.id}/cards/import",
        {
            "pasted_cards": (
                "front,back,difficulty,tags,example_sentence,pronunciation\n"
                "boarding pass,A document that lets you board a plane,easy,travel; airport,Show your boarding pass.,BOR-ding\n"
                "departure gate,The gate where passengers board before leaving,medium,airport,,\n"
            ),
            "default_tags": "imported",
            "skip_duplicates": "on",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == f"/decks/{deck.id}/cards/"
    first = Card.objects.get(deck=deck, front="boarding pass")
    second = Card.objects.get(deck=deck, front="departure gate")
    assert first.back == "A document that lets you board a plane"
    assert first.difficulty == "easy"
    assert first.tags == ["imported", "travel", "airport"]
    assert first.example_sentence == "Show your boarding pass."
    assert first.pronunciation == "BOR-ding"
    assert second.difficulty == "medium"
    deck.refresh_from_db()
    assert deck.card_count == 2

    duplicate = web_client.post(
        f"/decks/{deck.id}/cards/import",
        {"pasted_cards": "boarding pass - Duplicate definition", "skip_duplicates": "on"},
    )

    assert duplicate.status_code == 302
    assert Card.objects.filter(deck=deck, front="boarding pass").count() == 1
    deck.refresh_from_db()
    assert deck.card_count == 2


@pytest.mark.django_db
def test_web_card_import_supports_headerless_tsv(web_client, user):
    deck = Deck.objects.create(user=user, name="Travel")

    response = web_client.post(
        f"/decks/{deck.id}/cards/import",
        {
            "pasted_cards": "arrival\treaching a destination\ncustoms\ta place where bags are checked",
            "default_difficulty": "hard",
        },
    )

    assert response.status_code == 302
    assert Card.objects.get(deck=deck, front="arrival").difficulty == "hard"
    assert Card.objects.get(deck=deck, front="customs").back == "a place where bags are checked"


@pytest.mark.django_db
def test_web_sidebar_links_render_distinct_pages(web_client, user):
    deck = Deck.objects.create(user=user, name="Travel")
    Card.objects.create(deck=deck, front="boarding", back="getting on a plane")

    routes = {
        "/home/": b"Learning Dashboard",
        "/decks/": b"Deck Library",
        "/ai/": b"AI Generator",
        f"/decks/{deck.id}/cards/": b"Card Management",
    }

    for url, marker in routes.items():
        response = web_client.get(url)
        assert response.status_code == 200
        assert marker in response.content

    page = web_client.get("/home/")
    assert b'href="/home/"' in page.content
    assert b'href="/decks/"' in page.content
    assert b'href="/cards/"' in page.content
    assert b'href="/ai/"' in page.content


@pytest.mark.django_db
def test_web_ai_generate_returns_preview(web_client, user, generated_card, monkeypatch):
    deck = Deck.objects.create(user=user, name="AI Deck")

    def fake_generate_cards_from_topic(self, topic, count=10, language="en", target_language="fa", level="beginner"):
        return [generated_card], 25

    monkeypatch.setattr(AICardService, "generate_cards_from_topic", fake_generate_cards_from_topic)

    response = web_client.post(
        f"/decks/{deck.id}/ai/generate",
        {"topic": "travel phrases", "count": 5, "language": "en", "target_language": "fa", "level": "beginner"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["tokens_used"] == 25
    assert payload["cards"][0]["front"] == "ephemeral"


@pytest.mark.django_db
def test_web_ai_save_persists_selected_preview_cards(web_client, user, generated_card):
    deck = Deck.objects.create(user=user, name="AI Deck")
    generated_card["selected"] = True

    response = web_client.post(
        f"/decks/{deck.id}/ai/save",
        data=json.dumps({"cards": [generated_card]}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
    card = Card.objects.get(deck=deck, front="ephemeral")
    assert "lasting for a short time" in card.back
    assert "Pronunciation: ih-FEM-er-uhl" in card.back
    assert card.example_sentence == "The moment was ephemeral."
    assert card.pronunciation == "ih-FEM-er-uhl"
    assert card.tags == ["source:ai"]

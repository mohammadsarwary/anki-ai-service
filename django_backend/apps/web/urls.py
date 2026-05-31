from django.urls import path

from apps.web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home_page"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cards/", views.cards_redirect, name="cards"),
    path("decks/", views.decks_view, name="decks"),
    path("decks/create", views.create_deck, name="deck_create"),
    path("ai/", views.ai_page, name="ai"),
    path("decks/<uuid:deck_id>/cards/", views.deck_cards_view, name="deck_cards"),
    path("decks/<uuid:deck_id>/cards/create", views.create_card, name="card_create"),
    path("decks/<uuid:deck_id>/cards/import", views.import_cards, name="card_import"),
    path("cards/<uuid:card_id>/update", views.update_card, name="card_update"),
    path("cards/<uuid:card_id>/delete", views.delete_card, name="card_delete"),
    path("decks/<uuid:deck_id>/ai/generate", views.ai_generate, name="ai_generate"),
    path("decks/<uuid:deck_id>/ai/save", views.ai_save, name="ai_save"),
]

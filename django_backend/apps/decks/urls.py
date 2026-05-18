from django.urls import path

from apps.decks.views import (
    CardBatchView,
    CardDetailView,
    CardListCreateView,
    CategoryDecksView,
    CategoryDetailView,
    CategoryListView,
    CloneDeckView,
    DeckDetailView,
    DeckListCreateView,
    DiscoverDecksView,
    FeaturedDecksView,
    RecommendedDecksView,
    SearchDecksView,
    TrendingDecksView,
)

urlpatterns = [
    path("decks", DeckListCreateView.as_view()),
    path("decks/<uuid:pk>", DeckDetailView.as_view()),
    path("cards", CardListCreateView.as_view()),
    path("cards/<uuid:pk>", CardDetailView.as_view()),
    path("cards/batch", CardBatchView.as_view()),
    path("discover/decks", DiscoverDecksView.as_view()),
    path("discover/featured", FeaturedDecksView.as_view()),
    path("discover/recommended", RecommendedDecksView.as_view()),
    path("discover/categories", CategoryListView.as_view()),
    path("discover/trending", TrendingDecksView.as_view()),
    path("discover/search", SearchDecksView.as_view()),
    path("discover/decks/<uuid:pk>/clone", CloneDeckView.as_view()),
    path("categories/", CategoryListView.as_view()),
    path("categories", CategoryListView.as_view()),
    path("categories/<slug:slug>", CategoryDetailView.as_view()),
    path("categories/<slug:slug>/decks", CategoryDecksView.as_view()),
]

try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from django.contrib import admin

from apps.decks.models import Card, Category, Deck


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "deck_count", "created_at"]
    search_fields = ["name", "slug"]


@admin.register(Deck)
class DeckAdmin(ModelAdmin):
    list_display = ["name", "user", "is_public", "is_featured", "card_count", "category_ref", "created_at", "deleted_at"]
    list_filter = ["is_public", "is_featured", "category_ref", "deleted_at"]
    search_fields = ["name", "description", "user__email"]
    autocomplete_fields = ["user", "category_ref"]


@admin.register(Card)
class CardAdmin(ModelAdmin):
    list_display = ["front", "deck", "difficulty", "created_at", "deleted_at"]
    list_filter = ["difficulty", "deleted_at"]
    search_fields = ["front", "back", "deck__name"]
    autocomplete_fields = ["deck"]

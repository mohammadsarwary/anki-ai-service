from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    icon = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    deck_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Deck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="decks", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    category = models.CharField(max_length=255, null=True, blank=True)
    category_ref = models.ForeignKey(Category, null=True, blank=True, related_name="decks", on_delete=models.SET_NULL, db_column="category_id")
    is_featured = models.BooleanField(default=False)
    image_url = models.CharField(max_length=255, null=True, blank=True)
    card_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "decks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_public"]),
            models.Index(fields=["category"]),
            models.Index(fields=["updated_at"]),
        ]

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        return super().delete()

    def refresh_card_count(self):
        self.card_count = self.cards.count()
        self.save(update_fields=["card_count", "updated_at"])

    def __str__(self) -> str:
        return self.name


class Card(models.Model):
    DIFFICULTY_CHOICES = [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.ForeignKey(Deck, related_name="cards", on_delete=models.CASCADE)
    front = models.TextField()
    back = models.TextField()
    example_sentence = models.TextField(null=True, blank=True)
    pronunciation = models.CharField(max_length=255, null=True, blank=True)
    audio_url = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.CharField(max_length=255, null=True, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "cards"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["deck"]), models.Index(fields=["updated_at"])]

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        self.deck.refresh_card_count()

    def hard_delete(self):
        return super().delete()

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
        if self.deck_id:
            Deck.objects.filter(id=self.deck_id).update(
                card_count=Card.objects.filter(deck_id=self.deck_id).count(),
                updated_at=timezone.now(),
            )

    def __str__(self) -> str:
        return self.front[:80]

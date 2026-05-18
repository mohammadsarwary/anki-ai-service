from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.decks.models import Card


class ReviewState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(Card, related_name="review_states", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="review_states", on_delete=models.CASCADE)
    interval_minutes = models.IntegerField(default=0)
    next_review_at = models.DateTimeField(default=timezone.now)
    ease_factor = models.DecimalField(max_digits=3, decimal_places=2, default=2.5)
    repetition_count = models.IntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "review_states"
        unique_together = [["card", "user"]]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["next_review_at"]),
            models.Index(fields=["last_synced_at"]),
            models.Index(fields=["updated_at"]),
        ]

    @property
    def is_due(self) -> bool:
        return self.next_review_at <= timezone.now()

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class Review(models.Model):
    RATING_CHOICES = [("again", "Again"), ("hard", "Hard"), ("good", "Good"), ("easy", "Easy")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_review_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    card = models.ForeignKey(Card, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reviews", on_delete=models.CASCADE)
    rating = models.CharField(max_length=20, choices=RATING_CHOICES)
    response_time_ms = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "reviews"
        ordering = ["-reviewed_at"]
        indexes = [models.Index(fields=["user", "reviewed_at"]), models.Index(fields=["card"])]

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

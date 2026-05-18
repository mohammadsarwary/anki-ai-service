from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AIGeneration(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="ai_generations", on_delete=models.CASCADE)
    deck = models.ForeignKey("decks.Deck", related_name="ai_generations", null=True, blank=True, on_delete=models.SET_NULL)
    prompt = models.TextField()
    generated_cards = models.JSONField(default=list)
    cards_accepted = models.IntegerField(default=0)
    ai_provider = models.CharField(max_length=80, default="cerebras")
    tokens_used = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    latency_ms = models.IntegerField(null=True, blank=True)
    provider = models.CharField(max_length=80, default="cerebras")
    model_name = models.CharField(max_length=160, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    generation_type = models.CharField(max_length=40, default="text")
    input_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "a_i_generations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

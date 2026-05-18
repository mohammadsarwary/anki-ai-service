from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class DailyStreak(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="daily_streaks", on_delete=models.CASCADE)
    date = models.DateField()
    cards_reviewed = models.IntegerField(default=0)
    study_duration_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "daily_streaks"
        unique_together = [["user", "date"]]
        indexes = [models.Index(fields=["user", "date"])]


class Challenge(models.Model):
    TYPE_CHOICES = [
        ("master_verbs", "Master verbs"),
        ("finish_review", "Finish review"),
        ("audio_practice", "Audio practice"),
        ("daily_goal", "Daily goal"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="challenges", on_delete=models.CASCADE)
    type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    target_count = models.IntegerField()
    current_count = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "challenges"
        indexes = [models.Index(fields=["user", "date"])]

    @property
    def progress_percentage(self) -> int:
        if self.target_count <= 0:
            return 100 if self.completed else 0
        return min(100, int((self.current_count / self.target_count) * 100))

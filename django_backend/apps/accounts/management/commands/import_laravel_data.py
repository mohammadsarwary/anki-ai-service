from __future__ import annotations

import json
import os
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, UserStatistic
from apps.ai.models import AIGeneration
from apps.decks.models import Card, Category, Deck
from apps.gamification.models import Challenge, DailyStreak
from apps.reviews.models import Review, ReviewState


def parse_json(value, default):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def timestamps(model, pk, row):
    updates = {}
    for field in ["created_at", "updated_at", "deleted_at"]:
        if field in row and row[field] is not None:
            updates[field] = row[field]
    if updates:
        model.all_objects.filter(pk=pk).update(**updates) if hasattr(model, "all_objects") else model.objects.filter(pk=pk).update(**updates)


class Command(BaseCommand):
    help = "Import Laravel MySQL data into the Django schema."

    def add_arguments(self, parser):
        parser.add_argument("--host", default=os.getenv("LARAVEL_DB_HOST", "127.0.0.1"))
        parser.add_argument("--port", type=int, default=int(os.getenv("LARAVEL_DB_PORT", "3306")))
        parser.add_argument("--database", default=os.getenv("LARAVEL_DB_NAME"))
        parser.add_argument("--user", default=os.getenv("LARAVEL_DB_USER"))
        parser.add_argument("--password", default=os.getenv("LARAVEL_DB_PASSWORD", ""))

    def handle(self, *args, **options):
        if not options["database"] or not options["user"]:
            raise SystemExit("Provide --database and --user, or LARAVEL_DB_NAME/LARAVEL_DB_USER env vars.")
        import pymysql

        connection = pymysql.connect(
            host=options["host"],
            port=options["port"],
            user=options["user"],
            password=options["password"],
            database=options["database"],
            cursorclass=pymysql.cursors.DictCursor,
            charset="utf8mb4",
        )

        def rows(table):
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `{table}`")
                return cursor.fetchall()

        with transaction.atomic():
            for row in rows("users"):
                user, _ = User.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "name": row["name"],
                        "email": row["email"],
                        "password": row["password"],
                        "avatar_url": row.get("avatar_url"),
                        "level": row.get("level") or "A1",
                        "learning_language": row.get("learning_language") or "English",
                        "sync_cursor": row.get("sync_cursor"),
                        "email_verified_at": row.get("email_verified_at"),
                        "is_admin": bool(row.get("is_admin", False)),
                        "is_staff": bool(row.get("is_admin", False)),
                        "is_active": True,
                    },
                )
                timestamps(User, user.id, row)

            for row in self.safe_rows(rows, "user_statistics"):
                stat, _ = UserStatistic.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "user_id": row["user_id"],
                        "total_cards_created": row.get("total_cards_created") or 0,
                        "total_cards_reviewed": row.get("total_cards_reviewed") or 0,
                        "total_decks": row.get("total_decks") or 0,
                        "current_streak": row.get("current_streak") or 0,
                        "longest_streak": row.get("longest_streak") or 0,
                        "average_accuracy": row.get("average_accuracy") or Decimal("0"),
                        "total_study_time_seconds": row.get("total_study_time_seconds") or 0,
                    },
                )
                timestamps(UserStatistic, stat.id, row)

            for row in self.safe_rows(rows, "categories"):
                category, _ = Category.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "name": row["name"],
                        "slug": row["slug"],
                        "icon": row.get("icon"),
                        "description": row.get("description"),
                        "deck_count": row.get("deck_count") or 0,
                    },
                )
                timestamps(Category, category.id, row)

            for row in rows("decks"):
                deck, _ = Deck.all_objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "user_id": row["user_id"],
                        "name": row["name"],
                        "description": row.get("description"),
                        "is_public": bool(row.get("is_public", False)),
                        "category": row.get("category"),
                        "category_ref_id": row.get("category_id"),
                        "is_featured": bool(row.get("is_featured", False)),
                        "image_url": row.get("image_url"),
                        "card_count": row.get("card_count") or 0,
                        "deleted_at": row.get("deleted_at"),
                    },
                )
                timestamps(Deck, deck.id, row)

            for row in rows("cards"):
                card, _ = Card.all_objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "deck_id": row["deck_id"],
                        "front": row["front"],
                        "back": row["back"],
                        "example_sentence": row.get("example_sentence"),
                        "pronunciation": row.get("pronunciation"),
                        "audio_url": row.get("audio_url"),
                        "image_url": row.get("image_url"),
                        "difficulty": row.get("difficulty"),
                        "tags": parse_json(row.get("tags"), None),
                        "deleted_at": row.get("deleted_at"),
                    },
                )
                timestamps(Card, card.id, row)

            for row in self.safe_rows(rows, "review_states"):
                state, _ = ReviewState.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "card_id": row["card_id"],
                        "user_id": row["user_id"],
                        "interval_minutes": row.get("interval_minutes") or 0,
                        "next_review_at": row["next_review_at"],
                        "ease_factor": row.get("ease_factor") or Decimal("2.5"),
                        "repetition_count": row.get("repetition_count") or 0,
                        "last_reviewed_at": row.get("last_reviewed_at"),
                        "last_synced_at": row.get("last_synced_at"),
                    },
                )
                timestamps(ReviewState, state.id, row)

            for row in self.safe_rows(rows, "reviews"):
                review, _ = Review.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "client_review_id": row.get("client_review_id"),
                        "card_id": row["card_id"],
                        "user_id": row["user_id"],
                        "rating": row["rating"],
                        "response_time_ms": row.get("response_time_ms"),
                        "reviewed_at": row["reviewed_at"],
                    },
                )
                timestamps(Review, review.id, row)

            for row in self.safe_rows(rows, "daily_streaks"):
                streak, _ = DailyStreak.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "user_id": row["user_id"],
                        "date": row["date"],
                        "cards_reviewed": row.get("cards_reviewed") or 0,
                        "study_duration_seconds": row.get("study_duration_seconds") or 0,
                    },
                )
                timestamps(DailyStreak, streak.id, row)

            for row in self.safe_rows(rows, "challenges"):
                challenge, _ = Challenge.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "user_id": row["user_id"],
                        "type": row["type"],
                        "title": row["title"],
                        "target_count": row.get("target_count") or 0,
                        "current_count": row.get("current_count") or 0,
                        "completed": bool(row.get("completed", False)),
                        "date": row["date"],
                    },
                )
                timestamps(Challenge, challenge.id, row)

            for row in self.safe_rows(rows, "a_i_generations"):
                generation, _ = AIGeneration.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "user_id": row["user_id"],
                        "deck_id": row.get("deck_id"),
                        "prompt": row.get("prompt") or "",
                        "generated_cards": parse_json(row.get("generated_cards"), []),
                        "cards_accepted": row.get("cards_accepted") or 0,
                        "ai_provider": row.get("ai_provider") or "openai",
                        "tokens_used": row.get("tokens_used"),
                        "status": row.get("status") or "completed",
                        "latency_ms": row.get("latency_ms"),
                        "provider": row.get("provider") or row.get("ai_provider") or "openai",
                        "error_message": row.get("error_message"),
                        "result": parse_json(row.get("result"), None),
                    },
                )
                timestamps(AIGeneration, generation.id, row)

        connection.close()
        self.stdout.write(self.style.SUCCESS("Laravel data import completed"))

    def safe_rows(self, rows_func, table):
        try:
            return rows_func(table)
        except Exception:
            self.stdout.write(self.style.WARNING(f"Skipping missing table {table}"))
            return []

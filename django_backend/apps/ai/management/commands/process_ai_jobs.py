from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from apps.ai.models import AIGeneration
from apps.ai.services import AIJobService


class Command(BaseCommand):
    help = "Process pending AI jobs for cPanel cron."

    def add_arguments(self, parser):
        parser.add_argument("--max-seconds", type=int, default=50)
        parser.add_argument("--limit", type=int, default=10)

    def handle(self, *args, **options):
        deadline = time.monotonic() + options["max_seconds"]
        processed = 0
        service = AIJobService()
        while processed < options["limit"] and time.monotonic() < deadline:
            generation = AIGeneration.objects.filter(status="pending").order_by("created_at").first()
            if not generation:
                break
            service.process_one(generation)
            processed += 1
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} AI jobs"))

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Placeholder cPanel cron hook for future streak reminders."

    def handle(self, *args, **options):
        self.stdout.write("Streak reminder command is ready; notification provider not configured.")

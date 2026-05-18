import csv

try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from django.contrib import admin, messages
from django.http import HttpResponse

from apps.ai.models import AIGeneration
from apps.ai.services import AIJobService


@admin.action(description="Retry failed AI generations")
def retry_failed(modeladmin, request, queryset):
    updated = queryset.filter(status="failed").update(status="pending", error_message=None)
    messages.success(request, f"Queued {updated} failed AI generations for retry.")


@admin.action(description="Export selected AI generations as CSV")
def export_ai_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ai-generations.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "user", "status", "provider", "model", "tokens", "latency_ms", "created_at", "error"])
    for generation in queryset.select_related("user"):
        writer.writerow(
            [
                generation.id,
                generation.user.email,
                generation.status,
                generation.provider,
                generation.model_name,
                generation.tokens_used,
                generation.latency_ms,
                generation.created_at,
                generation.error_message,
            ]
        )
    return response


@admin.register(AIGeneration)
class AIGenerationAdmin(ModelAdmin):
    list_display = ["id", "user", "generation_type", "status", "provider", "model_name", "tokens_used", "latency_ms", "created_at"]
    list_filter = ["status", "provider", "generation_type", "created_at"]
    search_fields = ["id", "user__email", "prompt", "error_message"]
    readonly_fields = ["created_at", "updated_at", "latency_ms", "tokens_used", "result", "error_message"]
    autocomplete_fields = ["user", "deck"]
    actions = [retry_failed, export_ai_csv]

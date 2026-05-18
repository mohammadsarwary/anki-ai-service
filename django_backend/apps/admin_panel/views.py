from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from apps.ai.models import AIGeneration
from apps.admin_panel.services import AnalyticsService
from apps.reviews.models import Review


@method_decorator(staff_member_required, name="dispatch")
class AdminDashboardView(View):
    def get(self, request):
        analytics = AnalyticsService()
        return render(
            request,
            "admin_panel/dashboard.html",
            {
                "stats": analytics.dashboard_stats(),
                "reviews_per_day": analytics.series(Review, days=30),
                "ai_generations_per_day": analytics.series(AIGeneration, days=30),
                "top_users": analytics.top_users(),
                "popular_decks": analytics.popular_decks(),
            },
        )

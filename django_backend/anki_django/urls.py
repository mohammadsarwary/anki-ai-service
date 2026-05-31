"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from apps.admin_panel.views import AdminDashboardView
from anki_django.views import ApiTesterView


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", include("apps.web.urls")),
    path("health", health),
    path("api-tester/", ApiTesterView.as_view()),
    path("admin/analytics/", AdminDashboardView.as_view()),
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.decks.urls")),
    path("api/", include("apps.reviews.urls")),
    path("api/", include("apps.ai.urls")),
    path("api/", include("apps.practice.urls")),
    path("api/", include("apps.gamification.urls")),
    path("api/", include("apps.sync.urls")),
]

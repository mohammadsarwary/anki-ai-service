from django.urls import path

from apps.accounts.views import (
    AvatarView,
    LoginView,
    LogoutView,
    MeView,
    ProfileStatisticsView,
    ProfileView,
    RegisterView,
    VerifyTokenView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("auth/verify-token", VerifyTokenView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("profile", ProfileView.as_view()),
    path("profile/avatar", AvatarView.as_view()),
    path("profile/statistics", ProfileStatisticsView.as_view()),
]

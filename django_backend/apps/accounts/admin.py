try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import AuthToken, User, UserStatistic


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    model = User
    list_display = ["email", "name", "is_admin", "level", "learning_language", "created_at"]
    list_filter = ["is_admin", "is_staff", "level", "learning_language", "created_at"]
    search_fields = ["email", "name"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("name", "avatar_url", "level", "learning_language", "sync_cursor")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_admin", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("email_verified_at", "last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at", "last_login"]
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2", "is_admin", "is_staff")}),)


@admin.register(UserStatistic)
class UserStatisticAdmin(ModelAdmin):
    list_display = ["user", "total_cards_created", "total_cards_reviewed", "current_streak", "average_accuracy"]
    search_fields = ["user__email", "user__name"]


@admin.register(AuthToken)
class AuthTokenAdmin(ModelAdmin):
    list_display = ["user", "name", "created_at", "last_used_at", "expires_at"]
    search_fields = ["user__email", "name"]
    readonly_fields = ["token_hash", "created_at", "last_used_at"]

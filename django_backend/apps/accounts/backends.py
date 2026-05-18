from __future__ import annotations

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from apps.accounts.hashers import LaravelBcryptPasswordHasher


class EmailOrLaravelBackend(ModelBackend):
    """Authenticate by email and transparently upgrade Laravel bcrypt hashes."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if password is None:
            return None
        email = kwargs.get("email") or username or kwargs.get(get_user_model().USERNAME_FIELD)
        if not email:
            return None
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(email__iexact=email)
        except UserModel.DoesNotExist:
            return None

        encoded = user.password or ""
        if encoded.startswith(("$2y$", "$2a$", "$2b$")):
            if LaravelBcryptPasswordHasher().verify(password, encoded) and self.user_can_authenticate(user):
                user.set_password(password)
                user.save(update_fields=["password", "updated_at"])
                return user
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

from __future__ import annotations

from django.utils import timezone
from rest_framework import authentication, exceptions

from apps.accounts.models import AuthToken


class BearerTokenAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode()
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token_hash = AuthToken.hash_token(parts[1])
        token = AuthToken.objects.select_related("user").filter(token_hash=token_hash).first()
        if not token or token.is_expired or not token.user.is_active:
            raise exceptions.AuthenticationFailed("Invalid or expired token")
        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
        return token.user, token

from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AuthToken
from apps.accounts.serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


def token_response(user, token: str, message: str, status_code: int = status.HTTP_200_OK):
    return Response(
        {
            "success": True,
            "message": message,
            "data": {
                "user": UserSerializer(user).data,
                "token": token,
            },
        },
        status=status_code,
    )


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _, raw = AuthToken.issue(user)
        return token_response(user, raw, "User registered successfully", status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid credentials"}, status=401)
        user = serializer.validated_data["user"]
        if user.has_usable_password():
            # On Laravel hash login, Django will transparently rehash when supported.
            user.save(update_fields=["updated_at"])
        _, raw = AuthToken.issue(user)
        return token_response(user, raw, "Login successful")


class LogoutView(APIView):
    def post(self, request):
        if isinstance(request.auth, AuthToken):
            request.auth.delete()
        return Response({"success": True, "message": "Logged out successfully"})


class MeView(APIView):
    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data})


class VerifyTokenView(APIView):
    def get(self, request):
        return Response(
            {
                "valid": True,
                "user_id": str(request.user.id),
                "email": request.user.email,
                "name": request.user.name,
            }
        )


class ProfileView(APIView):
    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data})

    def put(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Profile updated successfully", "data": UserSerializer(request.user).data})


class AvatarView(APIView):
    def put(self, request):
        request.user.avatar_url = request.data.get("avatar_url")
        request.user.save(update_fields=["avatar_url", "updated_at"])
        return Response({"success": True, "message": "Avatar updated successfully", "data": UserSerializer(request.user).data})


class ProfileStatisticsView(APIView):
    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data["statistics"]})

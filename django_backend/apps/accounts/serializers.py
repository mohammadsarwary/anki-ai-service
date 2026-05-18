from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.accounts.models import User, UserStatistic


class UserStatisticSerializer(serializers.ModelSerializer):
    average_accuracy = serializers.FloatField()

    class Meta:
        model = UserStatistic
        fields = [
            "total_cards_created",
            "total_cards_reviewed",
            "total_decks",
            "current_streak",
            "longest_streak",
            "average_accuracy",
            "total_study_time_seconds",
        ]


class UserSerializer(serializers.ModelSerializer):
    statistics = UserStatisticSerializer(read_only=True)
    email_verified_at = serializers.DateTimeField(allow_null=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "avatar_url",
            "level",
            "learning_language",
            "email_verified_at",
            "created_at",
            "updated_at",
            "statistics",
        ]


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("The email has already been taken.")
        return value

    def save(self):
        return User.objects.create_user(
            email=self.validated_data["email"],
            password=self.validated_data["password"],
            name=self.validated_data["name"],
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "avatar_url", "level", "learning_language"]
        extra_kwargs = {field: {"required": False} for field in fields}

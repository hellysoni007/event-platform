from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import UserRole
from accounts.services import normalize_email


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRole.values)

    def validate_email(self, value):
        return normalize_email(value)

    def validate_password(self, value):
        validate_password(value)
        return value


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.RegexField(regex=r"^\d{6}$")

    def validate_email(self, value):
        return normalize_email(value)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return normalize_email(value)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return normalize_email(value)

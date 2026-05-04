from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import (
    LoginSerializer,
    ResendOTPSerializer,
    SignupSerializer,
    VerifyEmailSerializer,
)
from accounts.services import (
    create_or_resend_signup_otp,
    issue_new_otp,
    login_user,
    normalize_email,
    verify_email_otp,
)
from core.error_codes import ErrorCodes
from core.exceptions import DomainError


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_signup"

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        create_or_resend_signup_otp(data["email"], data["password"], data["role"])
        return Response({"detail": "Signup initiated.", "code": "SIGNUP_INITIATED"}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_verify_otp"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        verify_email_otp(data["email"], data["otp"])
        return Response({"detail": "Email verified.", "code": "EMAIL_VERIFIED"}, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_resend_otp"

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=normalize_email(email)).first()
        if not user:
            return Response({"detail": "If email exists, OTP has been resent.", "code": "OTP_RESEND_ACCEPTED"}, status=status.HTTP_202_ACCEPTED)
        if user.is_active:
            raise DomainError(
                detail="Email already exists.",
                code=ErrorCodes.EMAIL_ALREADY_EXISTS,
                status_code=status.HTTP_409_CONFLICT,
            )
        issue_new_otp(user, is_resend=True)
        return Response({"detail": "OTP resent.", "code": "OTP_RESENT"}, status=status.HTTP_202_ACCEPTED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = login_user(data["email"], data["password"])
        refresh = RefreshToken.for_user(user)
        return Response(
            {"access_token": str(refresh.access_token), "refresh_token": str(refresh)},
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
from django.shortcuts import render

# Create your views here.

from django.urls import path

from accounts.views import LoginView, RefreshView, ResendOTPView, SignupView, VerifyEmailView

urlpatterns = [
    path("signup", SignupView.as_view(), name="signup"),
    path("verify-email", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp", ResendOTPView.as_view(), name="resend-otp"),
    path("login", LoginView.as_view(), name="login"),
    path("refresh", RefreshView.as_view(), name="refresh"),
]

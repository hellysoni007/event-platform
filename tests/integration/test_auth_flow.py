import pytest
from django.contrib.auth.models import User

from accounts.models import OTPChallenge, UserProfile, UserRole
from accounts.services import hash_otp


@pytest.mark.integration
@pytest.mark.django_db
def test_signup_creates_unverified_user(api_client):
    response = api_client.post(
        "/api/v1/auth/signup",
        {"email": "newuser@example.com", "password": "StrongPassword123!", "role": "SEEKER"},
        format="json",
    )
    assert response.status_code == 201
    user = User.objects.get(email="newuser@example.com")
    assert user.is_active is False
    assert user.profile.role == UserRole.SEEKER


@pytest.mark.integration
@pytest.mark.django_db
def test_verify_email_success(api_client):
    api_client.post(
        "/api/v1/auth/signup",
        {"email": "verifyme@example.com", "password": "StrongPassword123!", "role": "SEEKER"},
        format="json",
    )
    user = User.objects.get(email="verifyme@example.com")
    challenge = OTPChallenge.objects.filter(user=user, is_active=True).latest("created_at")
    challenge.otp_hash = hash_otp("123456")
    challenge.save(update_fields=["otp_hash"])

    response = api_client.post(
        "/api/v1/auth/verify-email",
        {"email": "verifyme@example.com", "otp": "123456"},
        format="json",
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active is True


@pytest.mark.integration
@pytest.mark.django_db
def test_login_blocked_for_unverified_user(api_client):
    user = User.objects.create_user(username="usr_u1", email="u1@example.com", password="StrongPassword123!", is_active=False)
    UserProfile.objects.create(user=user, role=UserRole.SEEKER)

    response = api_client.post(
        "/api/v1/auth/login",
        {"email": "u1@example.com", "password": "StrongPassword123!"},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["code"] == "EMAIL_NOT_VERIFIED"

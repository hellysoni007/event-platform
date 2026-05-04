from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile, UserRole
from events.models import Event


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seeker_user(db):
    user = User.objects.create_user(
        username="usr_seeker123",
        email="seeker@example.com",
        password="StrongPassword123!",
        is_active=True,
    )
    UserProfile.objects.create(user=user, role=UserRole.SEEKER, email_verified_at=timezone.now())
    return user


@pytest.fixture
def facilitator_user(db):
    user = User.objects.create_user(
        username="usr_facilitator123",
        email="facilitator@example.com",
        password="StrongPassword123!",
        is_active=True,
    )
    UserProfile.objects.create(user=user, role=UserRole.FACILITATOR, email_verified_at=timezone.now())
    return user


@pytest.fixture
def future_event(db, facilitator_user):
    start = timezone.now() + timedelta(days=2)
    end = start + timedelta(hours=2)
    return Event.objects.create(
        title="Future Event",
        description="Test event",
        language="English",
        location="Remote",
        starts_at=start,
        ends_at=end,
        capacity=2,
        created_by=facilitator_user,
    )


@pytest.fixture
def seeker_token(api_client, seeker_user):
    response = api_client.post(
        "/api/v1/auth/login",
        {"email": seeker_user.email, "password": "StrongPassword123!"},
        format="json",
    )
    return response.data["access_token"]


@pytest.fixture
def facilitator_token(api_client, facilitator_user):
    response = api_client.post(
        "/api/v1/auth/login",
        {"email": facilitator_user.email, "password": "StrongPassword123!"},
        format="json",
    )
    return response.data["access_token"]

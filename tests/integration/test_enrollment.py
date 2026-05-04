from datetime import timedelta

import pytest
from django.utils import timezone

from enrollments.models import Enrollment, EnrollmentStatus
from events.models import Event


@pytest.mark.integration
@pytest.mark.django_db
def test_seeker_can_enroll(api_client, seeker_token, future_event):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {seeker_token}")
    response = api_client.post(f"/api/v1/events/{future_event.id}/enroll", format="json")
    assert response.status_code == 201
    future_event.refresh_from_db()
    assert future_event.enrolled_count == 1


@pytest.mark.integration
@pytest.mark.django_db
def test_duplicate_enrollment_rejected(api_client, seeker_token, future_event, seeker_user):
    Enrollment.objects.create(event=future_event, seeker=seeker_user, status=EnrollmentStatus.ENROLLED)
    future_event.enrolled_count = 1
    future_event.save(update_fields=["enrolled_count"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {seeker_token}")
    response = api_client.post(f"/api/v1/events/{future_event.id}/enroll", format="json")
    assert response.status_code == 409
    assert response.data["code"] == "ALREADY_ENROLLED"


@pytest.mark.integration
@pytest.mark.django_db
def test_capacity_respected(api_client, seeker_token, future_event, seeker_user):
    other_user = seeker_user.__class__.objects.create_user(
        username="usr_other",
        email="other@example.com",
        password="StrongPassword123!",
        is_active=True,
    )
    other_user.profile = seeker_user.profile.__class__.objects.create(
        user=other_user,
        role=seeker_user.profile.role,
        email_verified_at=timezone.now(),
    )
    Enrollment.objects.create(event=future_event, seeker=seeker_user, status=EnrollmentStatus.ENROLLED)
    Enrollment.objects.create(event=future_event, seeker=other_user, status=EnrollmentStatus.ENROLLED)
    future_event.enrolled_count = 2
    future_event.save(update_fields=["enrolled_count"])

    third_user = seeker_user.__class__.objects.create_user(
        username="usr_third",
        email="third@example.com",
        password="StrongPassword123!",
        is_active=True,
    )
    seeker_user.profile.__class__.objects.create(user=third_user, role=seeker_user.profile.role, email_verified_at=timezone.now())
    response = api_client.post(
        "/api/v1/auth/login",
        {"email": "third@example.com", "password": "StrongPassword123!"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access_token']}")
    full_response = api_client.post(f"/api/v1/events/{future_event.id}/enroll", format="json")
    assert full_response.status_code == 409
    assert full_response.data["code"] == "EVENT_FULL"


@pytest.mark.integration
@pytest.mark.django_db
def test_cannot_enroll_past_event(api_client, seeker_token, facilitator_user):
    start = timezone.now() - timedelta(days=1)
    past_event = Event.objects.create(
        title="Past",
        description="Past event",
        language="English",
        location="Remote",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        capacity=10,
        created_by=facilitator_user,
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {seeker_token}")
    response = api_client.post(f"/api/v1/events/{past_event.id}/enroll", format="json")
    assert response.status_code == 400
    assert response.data["code"] == "EVENT_ALREADY_STARTED"

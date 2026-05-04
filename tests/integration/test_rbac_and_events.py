import pytest


@pytest.mark.integration
@pytest.mark.django_db
def test_seeker_cannot_create_event(api_client, seeker_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {seeker_token}")
    payload = {
        "title": "Blocked event",
        "description": "x",
        "language": "English",
        "location": "Remote",
        "starts_at": "2026-05-20T10:00:00Z",
        "ends_at": "2026-05-20T11:00:00Z",
        "capacity": 10,
    }
    response = api_client.post("/api/v1/events", payload, format="json")
    assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.django_db
def test_facilitator_can_create_event(api_client, facilitator_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {facilitator_token}")
    payload = {
        "title": "Allowed event",
        "description": "x",
        "language": "English",
        "location": "Remote",
        "starts_at": "2026-05-20T10:00:00Z",
        "ends_at": "2026-05-20T11:00:00Z",
        "capacity": 10,
    }
    response = api_client.post("/api/v1/events", payload, format="json")
    assert response.status_code == 201

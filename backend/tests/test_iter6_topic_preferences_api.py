"""Iteration 6 - Topic preferences APIs: health, interests, content modes persistence."""

import os
import uuid

import pytest
import requests


def _base_url() -> str:
    base = os.environ.get("EXPO_BACKEND_URL") or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    if not base:
        pytest.skip("EXPO_BACKEND_URL/EXPO_PUBLIC_BACKEND_URL not configured")
    return base.rstrip("/")


BASE_URL = _base_url()
API = f"{BASE_URL}/api"
TIMEOUT = 30


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture()
def user_id():
    return f"TEST_iter6_{uuid.uuid4().hex[:12]}"


class TestTopicPreferencesApi:
    """/health, /user, /user/interests, /user/content-modes core persistence."""

    def test_health_ok(self, api_client):
        response = api_client.get(f"{API}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("status") in ("ok", "degraded")

    def test_set_interests_persist_via_get(self, api_client, user_id):
        create_response = api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert create_response.status_code == 200

        interests_payload = {"user_id": user_id, "interests": ["spazio", "corpo-umano"]}
        set_response = api_client.post(f"{API}/user/interests", json=interests_payload, timeout=TIMEOUT)
        assert set_response.status_code == 200

        get_response = api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert set(get_data.get("interests", [])) == {"spazio", "corpo-umano"}

    def test_set_all_interest_exclusive_persist_via_get(self, api_client, user_id):
        api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)

        first = api_client.post(
            f"{API}/user/interests",
            json={"user_id": user_id, "interests": ["spazio", "all"]},
            timeout=TIMEOUT,
        )
        assert first.status_code == 200

        get_response = api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        interests = get_response.json().get("interests", [])
        assert "all" in interests

    def test_set_content_modes_stories_only_persist_via_get(self, api_client, user_id):
        api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)

        set_response = api_client.post(
            f"{API}/user/content-modes",
            json={"user_id": user_id, "modes": ["stories"]},
            timeout=TIMEOUT,
        )
        assert set_response.status_code == 200
        assert set_response.json().get("content_modes") == ["stories"]

        get_response = api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        assert get_response.json().get("content_modes") == ["stories"]

    def test_set_content_modes_lessons_only_with_premium_persists(self, api_client, user_id):
        api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)

        premium_response = api_client.post(
            f"{API}/user/premium",
            json={"user_id": user_id, "active": True},
            timeout=TIMEOUT,
        )
        assert premium_response.status_code == 200

        set_response = api_client.post(
            f"{API}/user/content-modes",
            json={"user_id": user_id, "modes": ["lessons"]},
            timeout=TIMEOUT,
        )
        assert set_response.status_code == 200
        assert set_response.json().get("content_modes") == ["lessons"]

        get_response = api_client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        assert get_response.json().get("content_modes") == ["lessons"]

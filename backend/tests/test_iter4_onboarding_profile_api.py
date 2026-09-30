"""Onboarding profile API regression tests."""

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
    """Shared HTTP session fixture for onboarding/profile endpoints."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture()
def test_user_id():
    return f"TEST_profile_{uuid.uuid4().hex[:12]}"


class TestOnboardingProfileApi:
    """Covers /user and /user/profile persistence and validation paths."""

    def test_health_ok(self, api_client):
        response = api_client.get(f"{API}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("status") in ("ok", "degraded")

    def test_set_profile_persists_fields_via_get(self, api_client, test_user_id):
        create_response = api_client.get(f"{API}/user/{test_user_id}", timeout=TIMEOUT)
        assert create_response.status_code == 200

        profile_payload = {
            "user_id": test_user_id,
            "display_name": " Marco ",
            "gender": "man",
            "age": 25,
        }
        set_response = api_client.post(f"{API}/user/profile", json=profile_payload, timeout=TIMEOUT)
        assert set_response.status_code == 200
        set_data = set_response.json()
        assert set_data.get("display_name") == "Marco"

        get_response = api_client.get(f"{API}/user/{test_user_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("display_name") == "Marco"
        assert get_data.get("gender") == "man"
        assert get_data.get("age") == 25

    def test_set_profile_partial_update_preserves_other_fields(self, api_client, test_user_id):
        baseline_payload = {
            "user_id": test_user_id,
            "display_name": "Test Base",
            "gender": "woman",
            "age": 31,
        }
        baseline_response = api_client.post(f"{API}/user/profile", json=baseline_payload, timeout=TIMEOUT)
        assert baseline_response.status_code == 200

        patch_payload = {"user_id": test_user_id, "age": 32}
        patch_response = api_client.post(f"{API}/user/profile", json=patch_payload, timeout=TIMEOUT)
        assert patch_response.status_code == 200

        get_response = api_client.get(f"{API}/user/{test_user_id}", timeout=TIMEOUT)
        assert get_response.status_code == 200
        data = get_response.json()
        assert data.get("display_name") == "Test Base"
        assert data.get("gender") == "woman"
        assert data.get("age") == 32

    def test_invalid_age_returns_422(self, api_client, test_user_id):
        response = api_client.post(
            f"{API}/user/profile",
            json={"user_id": test_user_id, "age": 10},
            timeout=TIMEOUT,
        )
        assert response.status_code == 422
        assert "age" in response.text

    def test_invalid_gender_returns_422(self, api_client, test_user_id):
        response = api_client.post(
            f"{API}/user/profile",
            json={"user_id": test_user_id, "gender": "invalid"},
            timeout=TIMEOUT,
        )
        assert response.status_code == 422
        assert "gender" in response.text

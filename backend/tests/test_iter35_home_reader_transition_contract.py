import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")


@pytest.fixture(scope="session")
def api_client():
    if not BASE_URL:
        pytest.skip("EXPO_PUBLIC_BACKEND_URL is not set")
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def test_user_id():
    # guest flow identity for this iteration only
    return str(uuid.uuid4())


class TestGuestAndReaderContract:
    """Guest onboarding + discover + reader endpoints used by Home↔Reader flows."""

    def test_categories_available(self, api_client):
        response = api_client.get(f"{BASE_URL.rstrip('/')}/api/categories", params={"lang": "it"}, timeout=20)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("id" in item and "name" in item for item in data[:3])

    def test_guest_profile_bootstrap(self, api_client, test_user_id):
        response = api_client.get(f"{BASE_URL.rstrip('/')}/api/user/{test_user_id}", params={"lang": "it"}, timeout=20)
        assert response.status_code == 200
        data = response.json()
        assert data.get("user_id") == test_user_id
        assert isinstance(data.get("interests", []), list)

    def test_guest_onboarding_preferences_persist(self, api_client, test_user_id):
        payload = {"user_id": test_user_id, "interests": ["scienza", "spazio"]}
        update = api_client.post(f"{BASE_URL.rstrip('/')}/api/user/interests", json=payload, timeout=20)
        assert update.status_code == 200

        read_back = api_client.get(f"{BASE_URL.rstrip('/')}/api/user/{test_user_id}", params={"lang": "it"}, timeout=20)
        assert read_back.status_code == 200
        user = read_back.json()
        assert "scienza" in user.get("interests", [])
        assert "spazio" in user.get("interests", [])

    def test_discover_batch_returns_story_contract(self, api_client, test_user_id):
        response = api_client.get(
            f"{BASE_URL.rstrip('/')}/api/discover-batch",
            params={"user_id": test_user_id, "count": 7, "lang": "it"},
            timeout=30,
        )
        assert response.status_code == 200
        stories = response.json()
        assert isinstance(stories, list)
        assert len(stories) > 0
        first = stories[0]
        assert isinstance(first.get("id"), str) and first["id"]
        assert isinstance(first.get("title"), str) and first["title"]

    def test_story_detail_and_next_story(self, api_client, test_user_id):
        batch = api_client.get(
            f"{BASE_URL.rstrip('/')}/api/discover-batch",
            params={"user_id": test_user_id, "count": 2, "lang": "it"},
            timeout=30,
        )
        assert batch.status_code == 200
        stories = batch.json()
        assert len(stories) > 0
        story_id = stories[0]["id"]

        detail = api_client.get(f"{BASE_URL.rstrip('/')}/api/stories/{story_id}", params={"lang": "it"}, timeout=30)
        assert detail.status_code == 200
        body = detail.json()
        assert body.get("id") == story_id
        assert isinstance(body.get("chapters", []), list)
        assert len(body.get("chapters", [])) > 0

        nxt = api_client.get(
            f"{BASE_URL.rstrip('/')}/api/stories/{story_id}/next",
            params={"user_id": test_user_id, "lang": "it"},
            timeout=30,
        )
        assert nxt.status_code == 200
        next_body = nxt.json()
        assert isinstance(next_body.get("id"), str)
        assert next_body.get("id") != story_id

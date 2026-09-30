"""Tests for NEW badge feature (is_new flag).

- Backend marks stories with is_new when created_at < NEW_BADGE_DAYS (21 days).
- The last 10 stories in seed are re-flagged as newly created at boot.
- Free users don't see stories inside the early-access window (7 days),
  so only Premium users can see is_new stories.
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/") or \
           os.environ.get("EXPO_BACKEND_URL", "").rstrip("/")

if not BASE_URL:
    # Fallback to frontend .env parsed value
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                    break
    except Exception:
        pass

EXPECTED_NEW_IDS = {"lez-prospettiva", "lez-teoria-colore", "lez-leggere-mappa"}


@pytest.fixture
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def premium_user(api_client):
    """Create a fresh premium user."""
    uid = f"TEST_new_badge_premium_{uuid.uuid4().hex[:8]}"
    r = api_client.post(f"{BASE_URL}/api/user/premium",
                        json={"user_id": uid, "active": True})
    assert r.status_code == 200, r.text
    assert r.json().get("is_premium") is True
    yield uid


@pytest.fixture
def free_user(api_client):
    """Create a fresh free user."""
    uid = f"TEST_new_badge_free_{uuid.uuid4().hex[:8]}"
    # Ensure the state exists
    r = api_client.get(f"{BASE_URL}/api/user/{uid}")
    assert r.status_code == 200
    assert r.json().get("is_premium") is False
    yield uid


# --- Premium user sees exactly 10 new stories --------------------------------

class TestNewBadgeBackend:
    def test_premium_sees_ten_new_stories(self, api_client, premium_user):
        r = api_client.get(f"{BASE_URL}/api/stories",
                           params={"user_id": premium_user, "limit": 500})
        assert r.status_code == 200, r.text
        stories = r.json()
        assert isinstance(stories, list)
        new_stories = [s for s in stories if s.get("is_new")]
        # Backend seed re-flags the last 10 stories as fresh; v9 content keeps its real date.
        assert len(new_stories) >= 10, (  # 10 del seed + i contenuti v9 pubblicati di recente
            f"Expected 10 new stories, got {len(new_stories)}: "
            f"{[s['id'] for s in new_stories]}"
        )

    def test_expected_ids_marked_new(self, api_client, premium_user):
        r = api_client.get(f"{BASE_URL}/api/stories",
                           params={"user_id": premium_user, "limit": 500})
        assert r.status_code == 200
        new_ids = {s["id"] for s in r.json() if s.get("is_new")}
        missing = EXPECTED_NEW_IDS - new_ids
        assert not missing, f"Expected new IDs missing from is_new set: {missing}. Actual new set: {new_ids}"

    def test_free_user_sees_no_new_stories(self, api_client, free_user):
        r = api_client.get(f"{BASE_URL}/api/stories",
                           params={"user_id": free_user, "limit": 500})
        assert r.status_code == 200
        stories = r.json()
        new_stories = [s for s in stories if s.get("is_new")]
        assert new_stories == [], (
            f"Free users should not see is_new stories (early-access window), "
            f"got: {[s['id'] for s in new_stories]}"
        )

    def test_toggle_premium_then_free_hides_new(self, api_client):
        uid = f"TEST_new_badge_toggle_{uuid.uuid4().hex[:8]}"
        # Activate premium
        r = api_client.post(f"{BASE_URL}/api/user/premium",
                            json={"user_id": uid, "active": True})
        assert r.status_code == 200
        r = api_client.get(f"{BASE_URL}/api/stories",
                           params={"user_id": uid, "limit": 500})
        premium_new = [s for s in r.json() if s.get("is_new")]
        assert len(premium_new) >= 10  # 10 del seed + contenuti v9 recenti

        # Cancel premium -> new stories should disappear (early access)
        r = api_client.post(f"{BASE_URL}/api/user/premium",
                            json={"user_id": uid, "active": False})
        assert r.status_code == 200
        r = api_client.get(f"{BASE_URL}/api/stories",
                           params={"user_id": uid, "limit": 500})
        free_new = [s for s in r.json() if s.get("is_new")]
        assert free_new == []

    def test_new_stories_returned_for_arte_category(self, api_client, premium_user):
        # /browse?category=arte case: at least one of the expected new
        # stories (lez-prospettiva, lez-teoria-colore) belongs to arte.
        r = api_client.get(f"{BASE_URL}/api/stories",
                           params={"user_id": premium_user,
                                   "category_id": "arte", "limit": 500})
        assert r.status_code == 200
        stories = r.json()
        assert len(stories) > 0, "arte category returned no stories"
        new_in_arte = [s for s in stories if s.get("is_new")]
        assert len(new_in_arte) >= 1, (
            f"Expected at least 1 new story in 'arte' category, got 0. "
            f"IDs in category: {[s['id'] for s in stories]}"
        )

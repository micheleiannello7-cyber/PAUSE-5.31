"""Iteration 2 — 7-day early access feature backend tests.

Verifies:
- /api/stories (no user_id) hides the 10 "new" stories → 146 items.
- /api/stories?user_id=<premium> returns all 156 with 10 is_new=true.
- /api/stories?user_id=<free> returns 146 items (no is_new).
- /api/discover-next?user_id=<free> never returns is_new stories.
- /api/discover-next?user_id=<premium> may return is_new stories.
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def free_user(api):
    uid = f"TEST_free_{uuid.uuid4().hex[:8]}"
    # Auto-create via GET /api/user/{id}
    r = api.get(f"{BASE_URL}/api/user/{uid}")
    assert r.status_code == 200
    assert r.json().get("is_premium") is False
    return uid


@pytest.fixture(scope="module")
def premium_user(api):
    uid = f"TEST_premium_{uuid.uuid4().hex[:8]}"
    r = api.get(f"{BASE_URL}/api/user/{uid}")
    assert r.status_code == 200
    # Activate premium
    r = api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
    assert r.status_code == 200
    assert r.json().get("is_premium") is True
    yield uid
    # Cleanup: deactivate premium
    api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": False})


class TestStoriesEarlyAccess:
    def test_stories_no_user_hides_new(self, api):
        r = api.get(f"{BASE_URL}/api/stories", params={"limit": 500})
        assert r.status_code == 200
        stories = r.json()
        assert isinstance(stories, list)
        # 163 = all curiosità (lessons are Premium-only; the 10 early-access
        # items are lessons, so nothing else is hidden for anonymous callers)
        assert len(stories) == 163, f"Expected 163 stories (no user), got {len(stories)}"
        assert all(s.get("kind") != "lesson" for s in stories), "anonymous must not see lessons"
        # No is_new should surface
        news = [s for s in stories if s.get("is_new")]
        assert news == [], f"Expected zero is_new stories for anonymous, got {len(news)}"

    def test_stories_premium_returns_all_with_10_new(self, api, premium_user):
        r = api.get(f"{BASE_URL}/api/stories", params={"limit": 500, "user_id": premium_user})
        assert r.status_code == 200
        stories = r.json()
        assert len(stories) == 222, f"Expected 222 stories for premium, got {len(stories)}"
        news = [s for s in stories if s.get("is_new")]
        assert len(news) == 10, f"Expected exactly 10 is_new stories for premium, got {len(news)}"

    def test_stories_free_returns_146_no_new(self, api, free_user):
        r = api.get(f"{BASE_URL}/api/stories", params={"limit": 500, "user_id": free_user})
        assert r.status_code == 200
        stories = r.json()
        assert len(stories) == 163, f"Expected 163 stories for free, got {len(stories)}"
        news = [s for s in stories if s.get("is_new")]
        assert news == [], f"Expected zero is_new for free, got {len(news)}"


class TestDiscoverNextEarlyAccess:
    def test_discover_next_free_never_returns_new(self, api, free_user):
        # Sample 30 times to have high confidence (10/156 ~= 6.4%)
        for _ in range(30):
            r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": free_user})
            assert r.status_code == 200, r.text
            doc = r.json()
            assert doc.get("is_new") is False, f"Free user got is_new story: {doc.get('id')}"

    def test_discover_next_premium_can_return_new(self, api, premium_user):
        # Given 10/156 chance, 60 attempts → P(no new) ≈ 0.936^60 ≈ 0.02
        # Accept: either we see at least one is_new, or we prove sampling includes
        # all stories (i.e. is_new stories exist in the eligible pool).
        seen_new = False
        for _ in range(200):
            r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": premium_user})
            assert r.status_code == 200
            if r.json().get("is_new"):
                seen_new = True
                break
        assert seen_new, "Premium never returned an is_new story in 60 attempts (statistically unlikely)"

"""Iter 3: verify /api/stories sorts DESC by created_at and returns is_new stories
at the top for premium users, while free users still don't see any is_new items."""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")


@pytest.fixture(scope="module")
def free_user_id():
    uid = f"TEST_free_{uuid.uuid4().hex[:8]}"
    # ensure state exists (default is_premium=False)
    r = requests.get(f"{BASE_URL}/api/user/{uid}", timeout=15)
    assert r.status_code == 200
    return uid


@pytest.fixture(scope="module")
def premium_user_id():
    uid = f"TEST_prem_{uuid.uuid4().hex[:8]}"
    requests.get(f"{BASE_URL}/api/user/{uid}", timeout=15)
    r = requests.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True}, timeout=15)
    assert r.status_code == 200
    assert r.json().get("is_premium") is True
    yield uid
    # teardown - disable premium flag (keeps doc but harmless)
    requests.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": False}, timeout=15)


class TestStoriesSortAndFilter:
    def test_premium_stories_returns_60_with_10_new_on_top(self, premium_user_id):
        r = requests.get(
            f"{BASE_URL}/api/stories",
            params={"limit": 60, "user_id": premium_user_id},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 60, f"expected 60 stories, got {len(data)}"

        # First 10 must be is_new=True
        top10 = data[:10]
        new_flags_top = [s.get("is_new") for s in top10]
        assert all(new_flags_top), f"top10 is_new flags not all True: {new_flags_top}"

        # Total count of is_new in the 60 should be exactly 10
        total_new = sum(1 for s in data if s.get("is_new"))
        assert total_new == 10, f"expected exactly 10 is_new stories, got {total_new}"

        # Every item must have required preview fields
        for s in top10:
            assert "id" in s and "title" in s and "category_id" in s
            assert "is_new" in s

    def test_free_stories_hides_all_new(self, free_user_id):
        r = requests.get(
            f"{BASE_URL}/api/stories",
            params={"limit": 60, "user_id": free_user_id},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # No is_new stories should appear for free users
        new_items = [s for s in data if s.get("is_new")]
        assert len(new_items) == 0, f"free user should not see is_new items, got {len(new_items)}"

    def test_premium_stories_sorted_desc_created_at(self, premium_user_id):
        # Verify sort DESC by created_at by requesting the full field via detail endpoint
        r = requests.get(
            f"{BASE_URL}/api/stories",
            params={"limit": 60, "user_id": premium_user_id},
            timeout=20,
        )
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        # Fetch detail of first item and 11th item and compare created_at
        d0 = requests.get(f"{BASE_URL}/api/stories/{ids[0]}", timeout=15).json()
        d10 = requests.get(f"{BASE_URL}/api/stories/{ids[10]}", timeout=15).json()
        assert d0.get("created_at"), d0
        assert d10.get("created_at"), d10
        assert d0["created_at"] >= d10["created_at"], (
            f"First story ({d0['created_at']}) should be newer than or equal 11th ({d10['created_at']})"
        )


class TestRegression:
    """Ensure the categories + discover-next endpoints still work."""

    def test_categories(self):
        r = requests.get(f"{BASE_URL}/api/categories", timeout=15)
        assert r.status_code == 200
        cats = r.json()
        assert isinstance(cats, list) and len(cats) > 0

    def test_discover_next_free_no_new(self, free_user_id):
        seen = set()
        for _ in range(20):
            r = requests.get(
                f"{BASE_URL}/api/discover-next",
                params={"user_id": free_user_id},
                timeout=15,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            seen.add(data["id"])
            assert data.get("is_new") is False, f"free user got is_new story: {data['id']}"
        assert len(seen) > 0

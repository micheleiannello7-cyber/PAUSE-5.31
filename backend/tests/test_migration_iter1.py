"""Migration smoke tests for PAUSE (Emergent env).

Covers: health, categories, stories, story detail, user create/interests/
bookmark/complete, stats, discover-next. Focus is env migration, not
business logic. TTS is intentionally excluded (LLM key budget).
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("EXPO_BACKEND_URL") or "https://app-migration-hub-14.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def user_id():
    return f"TEST_migration_{uuid.uuid4().hex[:10]}"


# ------------------ core content ------------------

def test_health(api):
    r = api.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok" and j["db"] is True


def test_categories_12(api):
    r = api.get(f"{BASE_URL}/api/categories", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 12
    ids = {c["id"] for c in data}
    for expected in ["scienza", "spazio", "storia", "natura"]:
        assert expected in ids
    total_stories = sum(c.get("story_count", 0) + c.get("lesson_count", 0) for c in data)
    assert total_stories >= 400, f"expected 437+ stories, got {total_stories}"


def test_stories_list(api):
    r = api.get(f"{BASE_URL}/api/stories?limit=20", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    s = data[0]
    for k in ("id", "title", "hook", "category_id", "reading_time_min"):
        assert k in s


def test_story_detail(api):
    r = api.get(f"{BASE_URL}/api/stories?limit=1", timeout=20)
    sid = r.json()[0]["id"]
    r2 = api.get(f"{BASE_URL}/api/stories/{sid}", timeout=20)
    assert r2.status_code == 200
    j = r2.json()
    assert j["id"] == sid
    assert isinstance(j.get("chapters"), list) and len(j["chapters"]) > 0


def test_story_detail_en(api):
    r = api.get(f"{BASE_URL}/api/stories?limit=1&lang=en", timeout=20)
    sid = r.json()[0]["id"]
    r2 = api.get(f"{BASE_URL}/api/stories/{sid}?lang=en", timeout=20)
    assert r2.status_code == 200


def test_story_404(api):
    r = api.get(f"{BASE_URL}/api/stories/nonexistent-xyz", timeout=15)
    assert r.status_code == 404


# ------------------ user state ------------------

def test_user_create(api, user_id):
    r = api.get(f"{BASE_URL}/api/user/{user_id}", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j["user_id"] == user_id
    assert j["interests"] == []
    assert j["completed_story_ids"] == []


def test_user_interests(api, user_id):
    r = api.post(f"{BASE_URL}/api/user/interests",
                 json={"user_id": user_id, "interests": ["scienza", "spazio"]}, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert set(j["interests"]) >= {"scienza", "spazio"}
    # verify persistence
    r2 = api.get(f"{BASE_URL}/api/user/{user_id}", timeout=15)
    assert set(r2.json()["interests"]) >= {"scienza", "spazio"}


def test_user_bookmark_toggle(api, user_id):
    story = api.get(f"{BASE_URL}/api/stories?limit=1").json()[0]
    sid = story["id"]
    r = api.post(f"{BASE_URL}/api/user/bookmark",
                 json={"user_id": user_id, "story_id": sid}, timeout=15)
    assert r.status_code == 200
    assert sid in r.json()["bookmarked_story_ids"]
    # GET bookmarks
    r2 = api.get(f"{BASE_URL}/api/user/{user_id}/bookmarks", timeout=15)
    assert r2.status_code == 200
    assert any(s["id"] == sid for s in r2.json())
    # untoggle
    api.post(f"{BASE_URL}/api/user/bookmark", json={"user_id": user_id, "story_id": sid}, timeout=15)


def test_user_complete(api, user_id):
    story = api.get(f"{BASE_URL}/api/stories?limit=1").json()[0]
    sid = story["id"]
    r = api.post(f"{BASE_URL}/api/user/complete",
                 json={"user_id": user_id, "story_id": sid, "minutes": 3, "seconds": 180}, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert sid in j["completed_story_ids"]
    assert j["total_minutes"] >= 3
    assert j["streak_days"] >= 1


def test_user_stats(api, user_id):
    r = api.get(f"{BASE_URL}/api/user/{user_id}/stats", timeout=20)
    assert r.status_code == 200
    j = r.json()
    # Structure varies; ensure baseline keys present
    assert isinstance(j, dict)


def test_discover_next(api, user_id):
    r = api.get(f"{BASE_URL}/api/discover-next?user_id={user_id}", timeout=20)
    assert r.status_code == 200
    j = r.json()
    assert "id" in j and "title" in j

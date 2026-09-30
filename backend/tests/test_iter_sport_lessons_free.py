"""Backend tests for PAUSE restore iteration.

Covers:
  - GET /api/health
  - GET /api/categories returns 14 categories including 'sport'
    (sport: story_count=6, lesson_count=2)
  - Lessons FREE: content-modes accepts ["stories","lessons"] for a fresh (non
    premium) user WITHOUT clamping; ["lessons"] returns lessons only.
  - GET /api/stories?user_id=<free-user with lessons>&category_id=scienza
    returns kind=lesson items for a non-premium user.
  - POST /api/user/premium active=false does NOT strip "lessons" from content_modes.
  - GET /api/discover-next respects content_modes.
  - GET /api/stories/{id} returns a story (deep-dive direct open).
  - POST /api/user/complete increments session_count / total_minutes.
  - GET /api/user/{id}/limit-check works.
  - GET /api/tts/voices works.

TTS 429 (Universal Key budget) is treated as expected, not a failure.
"""

import os
import uuid
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture()
def fresh_user():
    return f"TEST_{uuid.uuid4().hex[:12]}"


# ---------- Health ----------
def test_health_ok(api_client):
    r = api_client.get(f"{API}/health", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ok", data
    assert data.get("db") is True, data


# ---------- Categories ----------
def test_categories_include_sport(api_client):
    r = api_client.get(f"{API}/categories", timeout=15)
    assert r.status_code == 200, r.text
    cats = r.json()
    assert isinstance(cats, list) and len(cats) == 14, f"expected 14 cats, got {len(cats)}"
    by_id = {c["id"]: c for c in cats}
    assert "sport" in by_id, f"missing 'sport' in {list(by_id)}"
    sport = by_id["sport"]
    assert sport["story_count"] == 6, f"sport.story_count={sport['story_count']}"
    assert sport["lesson_count"] == 2, f"sport.lesson_count={sport['lesson_count']}"


# ---------- Lessons are FREE ----------
def test_content_modes_lessons_free_both(api_client, fresh_user):
    r = api_client.post(
        f"{API}/user/content-modes",
        json={"user_id": fresh_user, "modes": ["stories", "lessons"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    state = r.json()
    assert state["is_premium"] is False
    assert set(state["content_modes"]) == {"stories", "lessons"}, state["content_modes"]


def test_content_modes_lessons_only(api_client, fresh_user):
    r = api_client.post(
        f"{API}/user/content-modes",
        json={"user_id": fresh_user, "modes": ["lessons"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    state = r.json()
    assert state["content_modes"] == ["lessons"], state["content_modes"]
    assert state["is_premium"] is False


def test_stories_lessons_only_returns_lessons_for_free_user(api_client, fresh_user):
    # Set lessons-only for fresh user
    r = api_client.post(
        f"{API}/user/content-modes",
        json={"user_id": fresh_user, "modes": ["lessons"]},
        timeout=15,
    )
    assert r.status_code == 200
    # Fetch stories in scienza for this user
    r = api_client.get(
        f"{API}/stories",
        params={"user_id": fresh_user, "category_id": "scienza", "limit": 50},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list)
    assert len(items) > 0, "expected at least one lesson in scienza for free user"
    kinds = {i.get("kind") for i in items}
    assert kinds == {"lesson"}, f"expected only lessons, got kinds={kinds}"


# ---------- Premium off should NOT strip lessons ----------
def test_premium_off_does_not_strip_lessons(api_client, fresh_user):
    # Configure both modes
    r = api_client.post(
        f"{API}/user/content-modes",
        json={"user_id": fresh_user, "modes": ["stories", "lessons"]},
        timeout=15,
    )
    assert r.status_code == 200
    # Explicitly set premium=false
    r = api_client.post(
        f"{API}/user/premium",
        json={"user_id": fresh_user, "active": False},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    state = r.json()
    assert state["is_premium"] is False
    assert "lessons" in state["content_modes"], (
        f"lessons was stripped when premium turned off: {state['content_modes']}"
    )


# ---------- Discover next respects content_modes ----------
def test_discover_next_respects_content_modes(api_client, fresh_user):
    # lessons-only user
    api_client.post(
        f"{API}/user/content-modes",
        json={"user_id": fresh_user, "modes": ["lessons"]},
        timeout=15,
    )
    r = api_client.get(f"{API}/discover-next", params={"user_id": fresh_user}, timeout=20)
    assert r.status_code == 200, r.text
    item = r.json()
    assert item.get("kind") == "lesson", f"discover-next should be a lesson, got kind={item.get('kind')}"


# ---------- Deep-dive open ----------
def test_get_story_by_id(api_client):
    # Grab any story id via list_stories (no user)
    r = api_client.get(f"{API}/stories", params={"limit": 1}, timeout=15)
    assert r.status_code == 200
    items = r.json()
    assert items, "no stories available"
    sid = items[0]["id"]
    r2 = api_client.get(f"{API}/stories/{sid}", timeout=15)
    assert r2.status_code == 200, r2.text
    story = r2.json()
    assert story["id"] == sid
    assert isinstance(story.get("chapters"), list) and len(story["chapters"]) > 0


# ---------- Complete (5s auto-count) ----------
def test_user_complete_increments_session(api_client, fresh_user):
    # get a story id
    r = api_client.get(f"{API}/stories", params={"limit": 1}, timeout=15)
    sid = r.json()[0]["id"]
    r2 = api_client.post(
        f"{API}/user/complete",
        json={"user_id": fresh_user, "story_id": sid, "minutes": 2, "seconds": 5},
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    state = r2.json()
    assert state["session_count"] == 1, state
    assert sid in state["completed_story_ids"]
    assert state["total_minutes"] >= 2


# ---------- Limit check ----------
def test_limit_check(api_client, fresh_user):
    r = api_client.get(f"{API}/user/{fresh_user}/limit-check", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    for key in ("enforce", "session_count", "limit", "is_premium", "reached", "blocked"):
        assert key in d, f"missing {key} in {d}"
    assert d["limit"] == 5, f"free user limit should be 5, got {d['limit']}"
    assert d["is_premium"] is False


# ---------- TTS voices ----------
def test_tts_voices(api_client):
    r = api_client.get(f"{API}/tts/voices", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert isinstance(d.get("voices"), list) and len(d["voices"]) > 0
    assert d.get("default") in d["voices"]

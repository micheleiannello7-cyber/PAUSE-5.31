"""Iteration 3 — tier/audio regression checks for UI contract support.

Modules/features covered:
- User premium toggle persistence for isolated test users
- Discover/story retrieval used by Home/Reader entry flows
- Single TTS warmup/status probe for premium availability reporting
"""

import os
import requests


BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
FREE_UID = "TEST_ui_free_20260923"
PREMIUM_UID = "TEST_ui_premium_20260923"


def _api() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def test_tier_seed_users_and_persistence():
    api = _api()

    r = api.post(f"{BASE_URL}/api/user/premium", json={"user_id": FREE_UID, "active": False})
    assert r.status_code == 200
    free_state = r.json()
    assert free_state["user_id"] == FREE_UID
    assert free_state["is_premium"] is False

    r = api.post(f"{BASE_URL}/api/user/premium", json={"user_id": PREMIUM_UID, "active": True})
    assert r.status_code == 200
    premium_state = r.json()
    assert premium_state["user_id"] == PREMIUM_UID
    assert premium_state["is_premium"] is True

    # Verify persisted values via GET
    free_get = api.get(f"{BASE_URL}/api/user/{FREE_UID}")
    premium_get = api.get(f"{BASE_URL}/api/user/{PREMIUM_UID}")
    assert free_get.status_code == 200
    assert premium_get.status_code == 200
    assert free_get.json()["is_premium"] is False
    assert premium_get.json()["is_premium"] is True


def test_discover_returns_story_for_free_user():
    api = _api()
    res = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": FREE_UID})
    assert res.status_code == 200
    story = res.json()
    assert isinstance(story.get("id"), str) and story["id"]

    # Create -> GET persistence-style validation on chosen story
    story_res = api.get(f"{BASE_URL}/api/stories/{story['id']}")
    assert story_res.status_code == 200
    detail = story_res.json()
    assert detail["id"] == story["id"]


def test_discover_returns_story_for_premium_user():
    api = _api()
    res = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": PREMIUM_UID})
    assert res.status_code == 200
    story = res.json()
    assert isinstance(story.get("id"), str) and story["id"]

    story_res = api.get(f"{BASE_URL}/api/stories/{story['id']}")
    assert story_res.status_code == 200
    detail = story_res.json()
    assert detail["id"] == story["id"]


def test_single_premium_tts_warmup_probe_contract():
    """One probe only: verifies API contract used by the audio sheet.

    This does NOT assert successful synthesis, only clear status semantics.
    """
    api = _api()
    story = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": PREMIUM_UID}).json()
    story_id = story["id"]

    warm = api.post(f"{BASE_URL}/api/tts/warmup/{story_id}")
    assert warm.status_code == 200
    warm_data = warm.json()
    assert warm_data["story_id"] == story_id
    assert warm_data["status"] in ("cached", "generating")

    status = api.get(f"{BASE_URL}/api/tts/status/{story_id}")
    assert status.status_code == 200
    status_data = status.json()
    assert status_data["story_id"] == story_id
    assert isinstance(status_data.get("ready"), bool)
    assert "url" in status_data and isinstance(status_data["url"], str)

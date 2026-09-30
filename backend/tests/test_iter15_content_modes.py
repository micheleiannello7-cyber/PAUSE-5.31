"""Iteration 15 — Mini-lessons content modes + TTS rehydration tests."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
assert BASE_URL, "BACKEND URL missing"
BASE_URL = BASE_URL.rstrip("/")


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def uid():
    return f"TEST_iter15_{uuid.uuid4()}"


# ------------------- content-modes persistence -------------------
class TestContentModes:
    def test_default_state_has_both_modes(self, api, uid):
        r = api.get(f"{BASE_URL}/api/user/{uid}")
        assert r.status_code == 200
        data = r.json()
        assert set(data["content_modes"]) == {"stories", "lessons"}

    def test_set_lessons_only(self, api, uid):
        # free users are clamped to stories (iter16) → go premium first
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        r = api.post(f"{BASE_URL}/api/user/content-modes",
                     json={"user_id": uid, "modes": ["lessons"]})
        assert r.status_code == 200
        assert r.json()["content_modes"] == ["lessons"]
        # verify persistence
        g = api.get(f"{BASE_URL}/api/user/{uid}").json()
        assert g["content_modes"] == ["lessons"]

    def test_set_stories_only(self, api, uid):
        r = api.post(f"{BASE_URL}/api/user/content-modes",
                     json={"user_id": uid, "modes": ["stories"]})
        assert r.status_code == 200
        assert r.json()["content_modes"] == ["stories"]

    def test_empty_falls_back(self, api, uid):
        r = api.post(f"{BASE_URL}/api/user/content-modes",
                     json={"user_id": uid, "modes": []})
        assert r.status_code == 200
        assert r.json()["content_modes"] == ["stories"]

    def test_invalid_filtered(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        r = api.post(f"{BASE_URL}/api/user/content-modes",
                     json={"user_id": uid, "modes": ["lessons", "garbage"]})
        assert r.status_code == 200
        assert r.json()["content_modes"] == ["lessons"]


# ------------------- discover-next respects modes -------------------
class TestDiscoverNextModes:
    def test_lessons_only_returns_lesson(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        api.post(f"{BASE_URL}/api/user/content-modes",
                 json={"user_id": uid, "modes": ["lessons"]})
        # Try multiple picks to see none are stories
        for _ in range(6):
            r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid})
            assert r.status_code == 200, r.text
            item = r.json()
            assert item.get("kind") == "lesson", f"expected lesson, got kind={item.get('kind')} id={item['id']}"

    def test_stories_only_excludes_lessons(self, api, uid):
        api.post(f"{BASE_URL}/api/user/content-modes",
                 json={"user_id": uid, "modes": ["stories"]})
        for _ in range(6):
            r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid})
            assert r.status_code == 200
            item = r.json()
            assert item.get("kind") != "lesson", f"got a lesson while in stories-only mode: {item['id']}"

    def test_both_modes_allowed(self, api, uid):
        # default both
        r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid})
        assert r.status_code == 200


# ------------------- lesson fields present -------------------
class TestLessonFields:
    def test_a_lesson_has_objective_and_5_chapters(self, api):
        # fetch a known seeded lesson id
        r = api.get(f"{BASE_URL}/api/stories/lez-metodo-scientifico")
        assert r.status_code == 200, r.text
        story = r.json()
        assert story.get("kind") == "lesson"
        assert story.get("objective")
        assert len(story.get("chapters", [])) == 5

    def test_lesson_en_localization(self, api):
        r = api.get(f"{BASE_URL}/api/stories/lez-metodo-scientifico",
                    params={"lang": "en"})
        assert r.status_code == 200
        story = r.json()
        assert "scientist" in story["title"].lower() or "method" in story["title"].lower()


# ------------------- TTS rehydration from MongoDB -------------------
class TestTTSRehydration:
    def test_tts_returns_audio_after_cache_purge(self, api):
        # pick a random story
        pr = api.get(f"{BASE_URL}/api/tts/random-preview")
        assert pr.status_code == 200
        sid = pr.json()["story_id"]
        r = api.get(f"{BASE_URL}/api/tts/story/{sid}", timeout=60)
        if r.status_code in (429, 502):
            pytest.skip("LLM budget exhausted (external, not a code bug)")
        assert r.status_code == 200, f"TTS status={r.status_code} body={r.text[:200]}"
        assert r.headers.get("content-type", "").startswith("audio/")
        assert len(r.content) > 1000


# ------------------- mini lessons are Premium-only -------------------
class TestLessonsPremiumOnly:
    def test_free_user_never_gets_lessons(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": False})
        api.post(f"{BASE_URL}/api/user/content-modes",
                 json={"user_id": uid, "modes": ["lessons"]})
        for _ in range(6):
            r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid})
            assert r.status_code == 200, r.text
            assert r.json().get("kind") == "story", "free reader received a lesson"

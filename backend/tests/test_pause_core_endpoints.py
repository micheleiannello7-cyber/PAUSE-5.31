"""
PAUSE core endpoints regression test.
Validates the endpoints requested for testing after codebase move & dependency fix.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    # Read from frontend/.env at runtime as a fallback
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("EXPO_PUBLIC_BACKEND_URL"):
                    BASE_URL = line.strip().split("=", 1)[1].strip().strip('"')
                    break

assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL is not configured"
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

TIMEOUT = 30


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
class TestHealth:
    def test_health_ok(self, client):
        r = client.get(f"{API}/health", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "ok", data
        # db should be true/ok
        db_val = data.get("db")
        assert db_val in (True, "ok", "up", 1), f"db field unexpected: {data}"


# ---------- Categories ----------
class TestCategories:
    def test_categories_returns_13(self, client):
        r = client.get(f"{API}/categories", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 13, f"Expected 13 categories, got {len(data)}"
        # basic shape
        assert "id" in data[0] and ("name" in data[0] or "title" in data[0])

    def test_categories_lang_it(self, client):
        r = client.get(f"{API}/categories", params={"lang": "it"}, timeout=TIMEOUT)
        assert r.status_code == 200
        assert len(r.json()) == 13


# ---------- Stories ----------
class TestStories:
    def test_stories_it_min_200(self, client):
        r = client.get(f"{API}/stories", params={"lang": "it", "limit": 500}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 150, f"Expected >=150 IT stories, got {len(data)}"

    def test_single_story_it(self, client):
        # Grab a story id first
        r = client.get(f"{API}/stories", params={"lang": "it", "limit": 5}, timeout=TIMEOUT)
        assert r.status_code == 200
        stories = r.json()
        assert stories, "No stories returned"
        story_id = stories[0].get("id")
        assert story_id
        r2 = client.get(f"{API}/stories/{story_id}", params={"lang": "it"}, timeout=TIMEOUT)
        assert r2.status_code == 200, r2.text
        story = r2.json()
        assert story.get("id") == story_id
        # A full story typically has a body/content field
        # PAUSE stories carry content in "chapters" and metadata
        assert any(k in story for k in ("chapters", "summary", "hook", "body", "content")), (
            f"Story shape missing content: keys={list(story.keys())}"
        )
        assert story.get("title"), "Story has no title"


# ---------- User state ----------
class TestUser:
    def test_user_get_creates_or_returns(self, client):
        user_id = f"TEST_{uuid.uuid4()}"
        r = client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("user_id") == user_id or data.get("id") == user_id or "user_id" in data

    def test_user_interests_post(self, client):
        user_id = f"TEST_{uuid.uuid4()}"
        # ensure the user exists
        client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        # Fetch a valid category id
        cats = client.get(f"{API}/categories", timeout=TIMEOUT).json()
        cat_ids = [c["id"] for c in cats[:3]]
        payload = {"user_id": user_id, "interests": cat_ids}
        r = client.post(f"{API}/user/interests", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        returned = data.get("interests") or data.get("interested_categories") or []
        assert set(cat_ids).issubset(set(returned)), f"interests not persisted: {data}"

        # GET back and verify persistence
        r2 = client.get(f"{API}/user/{user_id}", timeout=TIMEOUT)
        assert r2.status_code == 200
        d2 = r2.json()
        returned2 = d2.get("interests") or d2.get("interested_categories") or []
        assert set(cat_ids).issubset(set(returned2))


# ---------- TTS voices ----------
class TestTTS:
    def test_tts_voices(self, client):
        r = client.get(f"{API}/tts/voices", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        # accept either list or dict with voices key
        voices = data if isinstance(data, list) else data.get("voices") or data.get("data")
        assert voices, f"No voices returned: {data}"
        assert isinstance(voices, list)
        assert len(voices) >= 1

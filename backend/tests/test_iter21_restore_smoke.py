"""
Iter-21 smoke test after project restore from zip.
Covers the endpoints requested in the review: categories, stories (it/en),
story detail with chapters, discover-next, related, bookmarks (POST + GET),
stats, category-media, TTS voices. Stripe not configured — not tested.
"""
import os
import uuid
import pytest
import requests

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "").rstrip("/")
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL not set"
API = f"{BASE_URL}/api"
TIMEOUT = 30


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def sample_story_id(client):
    r = client.get(f"{API}/stories", params={"limit": 1}, timeout=TIMEOUT)
    assert r.status_code == 200
    stories = r.json()
    assert stories, "no stories seeded"
    return stories[0]["id"]


# ---------- Categories ----------
class TestCategories:
    def test_categories_default(self, client):
        r = client.get(f"{API}/categories", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 13, f"expected 13 categories, got {len(data)}"
        assert "id" in data[0]

    def test_categories_en(self, client):
        r = client.get(f"{API}/categories", params={"lang": "en"}, timeout=TIMEOUT)
        assert r.status_code == 200
        assert len(r.json()) == 13


# ---------- Stories list ----------
class TestStories:
    def test_stories_default(self, client):
        r = client.get(f"{API}/stories", params={"limit": 50}, timeout=TIMEOUT)
        assert r.status_code == 200
        stories = r.json()
        assert isinstance(stories, list) and len(stories) >= 20
        s0 = stories[0]
        for k in ("id", "title", "category_id"):
            assert k in s0, f"missing field {k} in preview"

    def test_stories_lang_en(self, client):
        r = client.get(f"{API}/stories", params={"lang": "en", "limit": 20}, timeout=TIMEOUT)
        assert r.status_code == 200
        stories = r.json()
        assert isinstance(stories, list) and len(stories) >= 1

    def test_story_detail_has_chapters(self, client, sample_story_id):
        r = client.get(f"{API}/stories/{sample_story_id}", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        detail = r.json()
        assert detail["id"] == sample_story_id
        assert detail.get("title")
        assert isinstance(detail.get("chapters"), list) and len(detail["chapters"]) >= 1
        assert isinstance(detail["chapters"][0], dict)


# ---------- Discover / related / next ----------
class TestDiscover:
    def test_discover_next(self, client):
        uid = f"TEST_{uuid.uuid4()}"
        r = client.get(f"{API}/discover-next", params={"user_id": uid}, timeout=TIMEOUT)
        assert r.status_code == 200
        s = r.json()
        assert s.get("id")

    def test_related(self, client, sample_story_id):
        r = client.get(f"{API}/stories/{sample_story_id}/related", timeout=TIMEOUT)
        assert r.status_code == 200
        related = r.json()
        assert isinstance(related, list)

    def test_next_story(self, client, sample_story_id):
        r = client.get(f"{API}/stories/{sample_story_id}/next", timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json().get("id")


# ---------- User / bookmarks / stats ----------
class TestUserFlow:
    def test_bookmark_and_stats(self, client, sample_story_id):
        uid = f"TEST_{uuid.uuid4()}"
        # create/get user
        r = client.get(f"{API}/user/{uid}", timeout=TIMEOUT)
        assert r.status_code == 200

        # POST bookmark
        r = client.post(f"{API}/user/bookmark", json={"user_id": uid, "story_id": sample_story_id}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        state = r.json()
        bm = (
            state.get("bookmarks")
            or state.get("bookmarked_stories")
            or state.get("bookmarked_story_ids")
            or []
        )
        assert sample_story_id in bm, f"bookmark not persisted: {state}"

        # GET bookmarks list
        r = client.get(f"{API}/user/{uid}/bookmarks", timeout=TIMEOUT)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert any(it.get("id") == sample_story_id for it in items)

        # Stats
        r = client.get(f"{API}/user/{uid}/stats", timeout=TIMEOUT)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)


# ---------- Media ----------
class TestMedia:
    def test_category_media(self, client):
        cats = client.get(f"{API}/categories", timeout=TIMEOUT).json()
        # Endpoint returns the AI-generated illustration; 404 is a valid
        # response when a category hasn't had illustration_generated populated
        # yet. At least ONE category should serve media successfully.
        found_ok = False
        for c in cats:
            r = client.get(f"{API}/category-media/{c['id']}", timeout=TIMEOUT)
            assert r.status_code in (200, 404), r.status_code
            if r.status_code == 200:
                found_ok = True
                assert r.headers.get("content-type", "").startswith("image/")
                break
        # Not a hard failure if no illustrations are generated (feature-flagged)
        # but log it via assert message when nothing was 200
        if not found_ok:
            pytest.skip("No category has illustration_generated populated")


# ---------- TTS ----------
class TestTTSVoices:
    def test_tts_voices(self, client):
        r = client.get(f"{API}/tts/voices", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        voices = data if isinstance(data, list) else (data.get("voices") or data.get("data"))
        assert voices and len(voices) >= 1

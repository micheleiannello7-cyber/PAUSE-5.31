"""Iteration 16 — Premium tier + 12 new hand-written mini lessons.

Covers:
- POST /api/user/premium (activate/deactivate + content_modes side-effects)
- GET /api/user/{id}/limit-check (free=5, premium=6, enforce=false)
- POST /api/user/content-modes clamping for free users
- GET /api/discover-next lesson gating
- 26 lessons total, 12 new mini lessons present with 5 chapters + non-empty
  summary in both IT and EN.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")

NEW_LESSON_IDS = [
    "lez-interesse-composto", "lez-inflazione",
    "lez-prospettiva", "lez-teoria-colore",
    "lez-leggere-mappa", "lez-fusi-orari",
    "lez-etimologia", "lez-calendario",
    "lez-respirazione", "lez-febbre",
    "lez-ghiaccio-galleggia", "lez-eco",
]


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def uid():
    return f"TEST_iter16_{uuid.uuid4().hex[:10]}"


# --------------------------- Premium toggle ---------------------------

class TestPremium:
    def test_activate_premium(self, api, uid):
        r = api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        assert r.status_code == 200
        d = r.json()
        assert d["is_premium"] is True

    def test_deactivate_removes_lessons_from_modes(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        # user now premium — set modes to include lessons
        r = api.post(f"{BASE_URL}/api/user/content-modes", json={"user_id": uid, "modes": ["lessons"]})
        assert r.status_code == 200
        assert "lessons" in r.json()["content_modes"]
        # deactivate
        r = api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": False})
        assert r.status_code == 200
        d = r.json()
        assert d["is_premium"] is False
        assert "lessons" not in d["content_modes"]
        assert "stories" in d["content_modes"]


# --------------------------- Limit check ---------------------------

class TestLimitCheck:
    def test_free_user_limit_5(self, api, uid):
        r = api.get(f"{BASE_URL}/api/user/{uid}/limit-check")
        assert r.status_code == 200
        d = r.json()
        assert d["limit"] == 5
        assert d["is_premium"] is False
        assert d["enforce"] is True  # ENFORCE_LIMIT defaults to true

    def test_premium_user_limit_6(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        r = api.get(f"{BASE_URL}/api/user/{uid}/limit-check")
        assert r.status_code == 200
        d = r.json()
        assert d["limit"] == 6
        assert d["is_premium"] is True


# --------------------------- content-modes clamp ---------------------------

class TestContentModesClamp:
    def test_free_user_lessons_clamped(self, api, uid):
        r = api.post(f"{BASE_URL}/api/user/content-modes", json={"user_id": uid, "modes": ["lessons"]})
        assert r.status_code == 200
        d = r.json()
        assert d["content_modes"] == ["stories"]

    def test_premium_user_lessons_kept(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        r = api.post(f"{BASE_URL}/api/user/content-modes", json={"user_id": uid, "modes": ["lessons"]})
        assert r.status_code == 200
        assert r.json()["content_modes"] == ["lessons"]


# --------------------------- discover-next ---------------------------

class TestDiscoverNext:
    def test_free_user_never_lesson(self, api, uid):
        # Even if we try to set lessons mode, it'll be clamped. Still verify.
        api.post(f"{BASE_URL}/api/user/content-modes", json={"user_id": uid, "modes": ["lessons"]})
        r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid})
        assert r.status_code == 200
        assert r.json().get("kind") != "lesson"

    def test_premium_lessons_returns_lesson(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        api.post(f"{BASE_URL}/api/user/content-modes", json={"user_id": uid, "modes": ["lessons"]})
        r = api.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid})
        assert r.status_code == 200
        assert r.json().get("kind") == "lesson"


# --------------------------- Lessons content ---------------------------

class TestLessons:
    def test_total_lessons_count(self, api):
        # Lessons are Premium-only: anonymous / free callers never see them
        # in the catalog (server-side clamp in _kind_filter).
        r = api.get(f"{BASE_URL}/api/stories", params={"limit": 500})
        assert r.status_code == 200
        lessons = [s for s in r.json() if s.get("kind") == "lesson"]
        assert len(lessons) == 0, f"expected 0 lessons for anonymous, got {len(lessons)}"

    def test_total_lessons_count_premium(self, api, uid):
        api.post(f"{BASE_URL}/api/user/premium", json={"user_id": uid, "active": True})
        api.post(f"{BASE_URL}/api/user/content-modes", json={"user_id": uid, "modes": ["stories", "lessons"]})
        r = api.get(f"{BASE_URL}/api/stories", params={"limit": 500, "user_id": uid})
        assert r.status_code == 200
        lessons = [s for s in r.json() if s.get("kind") == "lesson"]
        # 59 lessons total (14 a + 12 b + 33 v4); premium sees the early-access ones too
        assert len(lessons) == 59, f"expected 59 lessons for premium, got {len(lessons)}"

    @pytest.mark.parametrize("story_id", NEW_LESSON_IDS)
    def test_new_lesson_it(self, api, story_id):
        r = api.get(f"{BASE_URL}/api/stories/{story_id}", params={"lang": "it"})
        assert r.status_code == 200, f"{story_id} IT missing"
        d = r.json()
        assert d["kind"] == "lesson"
        assert len(d["chapters"]) == 5
        assert d["summary"].strip() != ""

    @pytest.mark.parametrize("story_id", NEW_LESSON_IDS)
    def test_new_lesson_en(self, api, story_id):
        r = api.get(f"{BASE_URL}/api/stories/{story_id}", params={"lang": "en"})
        assert r.status_code == 200, f"{story_id} EN missing"
        d = r.json()
        assert len(d["chapters"]) == 5
        assert d["summary"].strip() != ""
        # verify EN was actually applied (title should differ from IT most of the time,
        # or at least summary should be different — we only assert non-empty summary here
        # since some titles could coincidentally match).

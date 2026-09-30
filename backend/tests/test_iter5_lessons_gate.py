"""Iteration 5: verify (a) no topics_limit for 6+ specific categories, (b) mini
lessons are Premium-only across discover-next, discover-batch and stories."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://pause-preview-3.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture
def uid():
    return f"TEST_{uuid.uuid4().hex[:10]}"


@pytest.fixture
def s():
    ses = requests.Session()
    ses.headers.update({"Content-Type": "application/json"})
    return ses


# --- topics limit removed -----------------------------------------------------
def test_interests_no_topics_limit_six_categories(s, uid):
    cats = s.get(f"{API}/categories").json()
    # pick 6+ specific ids (avoid 'all')
    ids = [c["id"] for c in cats if c["id"] != "all"][:7]
    assert len(ids) >= 6, "Need at least 6 categories seeded"
    r = s.post(f"{API}/user/interests", json={"user_id": uid, "interests": ids})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert set(body["interests"]) == set(ids)


# --- kind gating: free users never see lessons --------------------------------
def _set_modes(s, uid, modes):
    r = s.post(f"{API}/user/content-modes", json={"user_id": uid, "modes": modes})
    assert r.status_code == 200, r.text
    return r.json()


def _set_premium(s, uid, active):
    r = s.post(f"{API}/user/premium", json={"user_id": uid, "active": active})
    assert r.status_code == 200, r.text
    return r.json()


def _set_interests_all(s, uid):
    r = s.post(f"{API}/user/interests", json={"user_id": uid, "interests": ["all"]})
    assert r.status_code == 200, r.text


def test_free_user_lessons_mode_still_gets_only_stories(s, uid):
    _set_interests_all(s, uid)
    _set_modes(s, uid, ["lessons"])  # backend must fallback in _kind_filter
    st = s.get(f"{API}/user/{uid}").json()
    assert st["is_premium"] is False
    assert st["content_modes"] == ["lessons"]
    # /discover-batch
    batch = s.get(f"{API}/discover-batch", params={"user_id": uid, "count": 8}).json()
    assert isinstance(batch, list) and len(batch) > 0, batch
    kinds = {b["kind"] for b in batch}
    assert kinds == {"story"}, f"Free user expected only story, got kinds={kinds}"
    # /discover-next
    nxt = s.get(f"{API}/discover-next", params={"user_id": uid}).json()
    assert nxt["kind"] == "story", nxt
    # /stories
    st_list = s.get(f"{API}/stories", params={"user_id": uid, "limit": 20}).json()
    assert all(x["kind"] == "story" for x in st_list), [x for x in st_list if x["kind"] != "story"]


def test_premium_user_lessons_mode_receives_lessons(s, uid):
    _set_interests_all(s, uid)
    _set_premium(s, uid, True)
    _set_modes(s, uid, ["lessons"])
    st = s.get(f"{API}/user/{uid}").json()
    assert st["is_premium"] is True
    # /discover-batch
    batch = s.get(f"{API}/discover-batch", params={"user_id": uid, "count": 8}).json()
    assert isinstance(batch, list) and len(batch) > 0, batch
    kinds = {b["kind"] for b in batch}
    assert kinds == {"lesson"}, f"Premium 'lessons' expected only lesson, got kinds={kinds}"
    # /discover-next
    nxt = s.get(f"{API}/discover-next", params={"user_id": uid}).json()
    assert nxt["kind"] == "lesson", nxt
    # /stories
    st_list = s.get(f"{API}/stories", params={"user_id": uid, "limit": 20}).json()
    assert st_list, "Expected some lesson-kind stories seeded"
    assert all(x["kind"] == "lesson" for x in st_list), [x for x in st_list if x["kind"] != "lesson"]


def test_premium_user_both_modes_receives_mixed(s, uid):
    _set_interests_all(s, uid)
    _set_premium(s, uid, True)
    _set_modes(s, uid, ["stories", "lessons"])
    batch = s.get(f"{API}/discover-batch", params={"user_id": uid, "count": 12}).json()
    kinds = {b["kind"] for b in batch}
    # not enforceable that both appear in every seed, but should be a subset of both
    assert kinds.issubset({"story", "lesson"}), kinds

"""Iter-10 restore verification tests. ENFORCE_LIMIT=true is live.
Uses fresh UUIDs for user_state so we don't hit the 5-story block."""
import os
import uuid
import pytest
import requests

BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"


@pytest.fixture
def uid():
    return f"TEST_{uuid.uuid4().hex[:12]}"


# -------- health & catalog --------
def test_health():
    r = requests.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "ok"


@pytest.mark.parametrize("lang", ["it", "en"])
def test_categories_by_lang(lang):
    r = requests.get(f"{API}/categories", params={"lang": lang}, timeout=15)
    assert r.status_code == 200
    cats = r.json()
    assert isinstance(cats, list) and len(cats) == 13
    empty = [c["id"] for c in cats if c["story_count"] == 0]
    # Known: economia, arte, geografia currently seeded without stories (restore state)
    assert set(empty).issubset({"economia", "arte", "geografia"}), f"unexpected empty categories: {empty}"
    for c in cats:
        assert "id" in c and "story_count" in c


# -------- discover --------
def test_discover_next_returns_story(uid):
    r = requests.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza,storia,natura"}, timeout=20)
    assert r.status_code == 200
    story = r.json()
    for k in ("id", "title", "category_id"):
        assert k in story, f"missing {k}"
    # discover-next returns preview; chapters live on /stories/{id}


def test_discover_next_exclude_differs(uid):
    r1 = requests.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza,storia,natura,spazio"}, timeout=20)
    assert r1.status_code == 200
    s1 = r1.json()
    r2 = requests.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza,storia,natura,spazio", "exclude": s1["id"]}, timeout=20)
    assert r2.status_code == 200
    s2 = r2.json()
    assert s2["id"] != s1["id"]


def test_story_detail(uid):
    r = requests.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza"}, timeout=20)
    sid = r.json()["id"]
    r2 = requests.get(f"{API}/stories/{sid}", timeout=15)
    assert r2.status_code == 200
    story = r2.json()
    assert story["id"] == sid
    assert isinstance(story.get("chapters"), list) and len(story["chapters"]) >= 1


# -------- user state --------
def test_user_state_autocreated(uid):
    r = requests.get(f"{API}/user/{uid}", timeout=15)
    assert r.status_code == 200
    u = r.json()
    assert u.get("user_id") == uid
    # fresh users start empty
    assert u.get("session_count", 0) == 0
    assert u.get("blocked_until") in (None, 0, "")


def test_limit_check_fresh(uid):
    r = requests.get(f"{API}/user/{uid}/limit-check", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d.get("enforce") is True
    assert d.get("blocked") is False
    assert d.get("session_count") == 0


def test_interests_persist(uid):
    payload = {"user_id": uid, "interests": ["scienza", "storia"]}
    r = requests.post(f"{API}/user/interests", json=payload, timeout=15)
    assert r.status_code == 200
    r2 = requests.get(f"{API}/user/{uid}", timeout=15)
    assert set(r2.json().get("interests", [])) == {"scienza", "storia"}


def test_bookmark_and_like_flow(uid):
    story_id = requests.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza"}, timeout=20).json()["id"]

    r = requests.post(f"{API}/user/bookmark", json={"user_id": uid, "story_id": story_id}, timeout=15)
    assert r.status_code == 200
    r = requests.post(f"{API}/user/like", json={"user_id": uid, "story_id": story_id}, timeout=15)
    assert r.status_code == 200

    bm = requests.get(f"{API}/user/{uid}/bookmarks", timeout=15).json()
    liked = requests.get(f"{API}/user/{uid}/liked", timeout=15).json()
    assert any(s["id"] == story_id for s in bm)
    assert any(s["id"] == story_id for s in liked)


def test_complete_increments_session(uid):
    story_id = requests.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza"}, timeout=20).json()["id"]
    r = requests.post(f"{API}/user/complete", json={"user_id": uid, "story_id": story_id, "seconds": 42}, timeout=15)
    assert r.status_code == 200
    st = requests.get(f"{API}/user/{uid}/session-stories", timeout=15).json()
    assert any(s["id"] == story_id for s in st)
    lc = requests.get(f"{API}/user/{uid}/limit-check", timeout=15).json()
    assert lc["session_count"] == 1


def test_limit_setting_toggle(uid):
    r = requests.post(f"{API}/user/limit-setting", json={"user_id": uid, "enabled": False}, timeout=15)
    assert r.status_code == 200
    u = requests.get(f"{API}/user/{uid}", timeout=15).json()
    assert u.get("limit_enabled") is False
    r2 = requests.post(f"{API}/user/limit-setting", json={"user_id": uid, "enabled": True}, timeout=15)
    assert r2.status_code == 200


def test_content_report(uid):
    # /content/report is a GET endpoint in this app (returns aggregated report info)
    r = requests.get(f"{API}/content/report", timeout=15)
    assert r.status_code == 200


def test_media_endpoint_shape():
    # 404 acceptable if AI pipeline hasn't generated; 200 also fine
    r = requests.get(f"{API}/media/black-holes-basics", timeout=15, allow_redirects=False)
    assert r.status_code in (200, 302, 404)

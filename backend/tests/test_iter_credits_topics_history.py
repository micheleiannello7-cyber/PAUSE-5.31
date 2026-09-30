"""
Backend tests for the new credits/topics/history features.

Covers:
- limit-check on fresh user (5/5, blocked false, next_credit_in 0)
- credit consumption via /user/complete (5 stories → 0 credits, blocked)
- reread does not consume credit
- token bucket recharge via credits_at manipulation (free 2h/credit, premium 1h/credit, capped)
- premium capacity 5 (free 4), downgrade clamps
- topics: no limit for free or premium ('all' free)
- history endpoint: newest first, free-only 10 days + hidden_count, premium q/category/since work
- stats ignores reread entries
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    # Read frontend .env as source of truth for the public URL
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"')
                break
BASE_URL = (BASE_URL or "").rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

_mongo = MongoClient(MONGO_URL)
_db = _mongo[DB_NAME]


@pytest.fixture
def s():
    return requests.Session()


@pytest.fixture
def uid():
    """Fresh user id per test — cleaned up after."""
    u = f"TEST_{uuid.uuid4().hex[:12]}"
    yield u
    _db.user_state.delete_one({"user_id": u})


def _get_story_ids(n=6):
    r = requests.get(f"{API}/stories", params={"limit": n})
    r.raise_for_status()
    return [it["id"] for it in r.json()][:n]


# ------------------------- limit-check / credits -------------------------

def test_fresh_user_limit_check(s, uid):
    r = s.get(f"{API}/user/{uid}/limit-check")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["enforce"] is True, f"ENFORCE_LIMIT should be true: {data}"
    assert data["credits"] == 4
    assert data["capacity"] == 4
    assert data["next_credit_in"] == 0
    assert data["blocked"] is False
    assert data["recharge_seconds"] == 7200
    assert data["is_premium"] is False


def test_consume_4_credits_then_block(s, uid):
    ids = _get_story_ids(6)
    assert len(ids) >= 4
    for sid in ids[:4]:
        r = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 2, "seconds": 30})
        assert r.status_code == 200, r.text
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["credits"] == 0, check
    assert check["blocked"] is True
    assert 7100 <= check["next_credit_in"] <= 7200
    assert check["blocked_until"] is not None

    # Re-post the SAME story id (already completed) → no credit change
    r = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": ids[0], "minutes": 2, "seconds": 30})
    assert r.status_code == 200
    check2 = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check2["credits"] == 0
    assert check2["blocked"] is True


def test_token_bucket_free_recharge_2h(s, uid):
    ids = _get_story_ids(5)
    for sid in ids[:4]:
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 1, "seconds": 5})
    # 1h05 ago → nothing yet for a free user (2h per credit)
    past = (datetime.now(timezone.utc) - timedelta(seconds=3600 + 300)).isoformat()
    _db.user_state.update_one({"user_id": uid}, {"$set": {"credits_at": past}})
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["credits"] == 0, check
    # 2h05 ago → +1
    past = (datetime.now(timezone.utc) - timedelta(seconds=7200 + 300)).isoformat()
    _db.user_state.update_one({"user_id": uid}, {"$set": {"credits_at": past}})
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["credits"] == 1, check
    assert check["blocked"] is False
    assert check["capacity"] == 4


def test_token_bucket_caps_after_days(s, uid):
    ids = _get_story_ids(5)
    for sid in ids[:4]:
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 1, "seconds": 5})
    past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    _db.user_state.update_one({"user_id": uid}, {"$set": {"credits_at": past}})
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["credits"] == 4, check
    assert check["next_credit_in"] == 0


def test_premium_capacity_5_hourly_and_downgrade(s, uid):
    s.get(f"{API}/user/{uid}/limit-check")
    r = s.post(f"{API}/user/premium", json={"user_id": uid, "active": True})
    assert r.status_code == 200
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["capacity"] == 5
    assert check["recharge_seconds"] == 3600
    assert check["is_premium"] is True
    assert 4 <= check["credits"] <= 5, check
    # Premium recharges hourly
    ids = _get_story_ids(3)
    for sid in ids[:2]:
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 1, "seconds": 5})
    past = (datetime.now(timezone.utc) - timedelta(seconds=3600 + 60)).isoformat()
    _db.user_state.update_one({"user_id": uid}, {"$set": {"credits_at": past}})
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["credits"] == 3, check

    # Downgrade → clamp to 4
    _db.user_state.update_one({"user_id": uid}, {"$set": {"credits": 5}})
    s.post(f"{API}/user/premium", json={"user_id": uid, "active": False})
    check = s.get(f"{API}/user/{uid}/limit-check").json()
    assert check["capacity"] == 4
    assert check["credits"] <= 4, check


# ------------------------- topics limit -------------------------

def test_topics_no_limit_free(s, uid):
    # Nessun limite di argomenti per l'utente base: 5+ categorie → 200.
    cats = s.get(f"{API}/categories").json()
    cat_ids = [c["id"] for c in cats if c["id"] != "all"][:6]
    assert len(cat_ids) >= 5
    r = s.post(f"{API}/user/interests", json={"user_id": uid, "interests": cat_ids})
    assert r.status_code == 200, r.text
    assert len(r.json()["interests"]) == len(cat_ids)


def test_topics_limit_premium_unlimited(s, uid):
    s.post(f"{API}/user/premium", json={"user_id": uid, "active": True})
    cats = s.get(f"{API}/categories").json()
    cat_ids = [c["id"] for c in cats if c["id"] != "all"][:12]
    r = s.post(f"{API}/user/interests", json={"user_id": uid, "interests": cat_ids})
    assert r.status_code == 200, r.text


# ------------------------- history -------------------------

def test_history_free_windowed_and_hidden(s, uid):
    ids = _get_story_ids(3)
    for sid in ids:
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 2, "seconds": 10})

    # All within 10 days initially
    r = s.get(f"{API}/user/{uid}/history")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["is_premium"] is False
    assert data["window_days"] == 10
    assert data["hidden_count"] == 0
    assert data["total"] == 3
    assert len(data["items"]) == 3
    # Newest first: read_at desc
    read_ats = [it["read_at"] for it in data["items"]]
    assert read_ats == sorted(read_ats, reverse=True)
    # Contains story preview fields
    it = data["items"][0]
    assert "story" in it and "title" in it["story"]
    assert "read_at" in it

    # Backdate 2 of the 3 completions to > 10 days ago → hidden 2
    old_at = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
    st = _db.user_state.find_one({"user_id": uid})
    completions = st["completions"]
    completions[0]["at"] = old_at
    completions[1]["at"] = old_at
    _db.user_state.update_one({"user_id": uid}, {"$set": {"completions": completions}})

    data2 = s.get(f"{API}/user/{uid}/history").json()
    assert data2["hidden_count"] == 2, data2
    assert len(data2["items"]) == 1
    assert data2["total"] == 3

    # Free: q/category_id/since must be IGNORED
    data3 = s.get(f"{API}/user/{uid}/history", params={"q": "xyz-none", "category_id": "spazio", "since": "2020-01-01"}).json()
    assert len(data3["items"]) == 1, "free should ignore filters"


def test_history_premium_filters(s, uid):
    ids = _get_story_ids(3)
    for sid in ids:
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 2, "seconds": 10})
    s.post(f"{API}/user/premium", json={"user_id": uid, "active": True})

    # Backdate first completion 30 days ago
    old_at = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    st = _db.user_state.find_one({"user_id": uid})
    st["completions"][0]["at"] = old_at
    _db.user_state.update_one({"user_id": uid}, {"$set": {"completions": st["completions"]}})

    data = s.get(f"{API}/user/{uid}/history").json()
    assert data["is_premium"] is True
    assert data["window_days"] is None
    assert len(data["items"]) == 3  # premium sees all

    # since filter: last 7 days → should hide the backdated one
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    d2 = s.get(f"{API}/user/{uid}/history", params={"since": since}).json()
    assert len(d2["items"]) == 2, d2

    # category filter
    known_cat = data["items"][0]["story"]["category_id"]
    d3 = s.get(f"{API}/user/{uid}/history", params={"category_id": known_cat}).json()
    assert all(it["story"]["category_id"] == known_cat for it in d3["items"])
    assert len(d3["items"]) >= 1

    # q filter (by title substring)
    title = data["items"][0]["story"]["title"]
    needle = title.split()[0][:4].lower()
    d4 = s.get(f"{API}/user/{uid}/history", params={"q": needle}).json()
    assert len(d4["items"]) >= 1
    assert any(needle in it["story"]["title"].lower() or needle in it["story"].get("hook", "").lower() for it in d4["items"])


def test_reread_counted_in_history_but_not_stats(s, uid):
    ids = _get_story_ids(2)
    for sid in ids:
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 3, "seconds": 0})
    # Re-read first story
    r = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": ids[0], "minutes": 3, "seconds": 0})
    assert r.status_code == 200

    # History: still 2 unique stories (latest per story) — first item is the reread'd one
    hist = s.get(f"{API}/user/{uid}/history").json()
    assert hist["total"] == 2
    assert hist["items"][0]["story"]["id"] == ids[0]
    assert hist["items"][0]["reread"] is True

    # Stats: reread must not inflate discovery totals. The stats payload uses
    # `minutes` (not `total_minutes`) as the reader-facing key.
    stats = s.get(f"{API}/user/{uid}/stats").json()
    assert stats.get("stories") == 2, stats  # unique stories, not 3
    assert stats.get("minutes") == 6, stats  # 2 completions × 3, reread ignored

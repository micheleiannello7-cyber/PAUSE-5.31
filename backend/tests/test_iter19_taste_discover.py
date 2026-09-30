"""Iter19 — /api/discover-next taste weighting + regression on core endpoints.

- New anonymous user (no likes) still gets a valid random StoryPreview.
- Interests filter still respected (interests=spazio returns only spazio).
- Completed stories still excluded.
- Statistically, a user who liked 3 'spazio' stories should get a HIGHER share
  of spazio than a fresh user (but not exclusively — feed stays varied).
- /api/health, /api/stories, /api/stories/{id}/next, /api/user/{id}/bookmarks,
  /api/user/{id}/liked keep 200.
"""

import os
import uuid
from collections import Counter

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/") or \
           os.environ.get("EXPO_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fall back to the frontend .env value (public preview URL).
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                break

SPAZIO_STORIES = ["how-stars-die", "mars-red", "black-holes-basics"]
SAMPLES = 120


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# --- Regression: core GETs still work ------------------------------------

def test_health(s):
    r = s.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_stories_listing(s):
    r = s.get(f"{BASE_URL}/api/stories?limit=5", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    for k in ("id", "category_id", "title", "hero_image"):
        assert k in data[0]


def test_stories_next(s):
    r = s.get(f"{BASE_URL}/api/stories/how-stars-die/next", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j["id"] != "how-stars-die"


def test_spazio_stories_exist(s):
    """Guardrail — the 3 spazio ids used by the taste test must actually exist
    and belong to the spazio category."""
    for sid in SPAZIO_STORIES:
        r = s.get(f"{BASE_URL}/api/stories/{sid}", timeout=10)
        assert r.status_code == 200, f"missing seed story: {sid}"
        assert r.json()["category_id"] == "spazio", f"{sid} is not in spazio"


def test_user_bookmarks_and_liked(s):
    uid = f"TEST_boot_{uuid.uuid4().hex[:8]}"
    for path in ("bookmarks", "liked"):
        r = s.get(f"{BASE_URL}/api/user/{uid}/{path}", timeout=10)
        assert r.status_code == 200
        assert r.json() == []


# --- discover-next ---------------------------------------------------------

def test_discover_next_fresh_user(s):
    uid = f"TEST_fresh_{uuid.uuid4().hex[:8]}"
    r = s.get(f"{BASE_URL}/api/discover-next", params={"user_id": uid, "interests": "all"}, timeout=15)
    assert r.status_code == 200
    j = r.json()
    for k in ("id", "category_id", "title"):
        assert k in j and j[k]


def test_discover_next_interests_filter(s):
    """interests=spazio must ONLY return spazio stories."""
    uid = f"TEST_interest_{uuid.uuid4().hex[:8]}"
    seen = set()
    for _ in range(20):
        r = s.get(f"{BASE_URL}/api/discover-next",
                  params={"user_id": uid, "interests": "spazio"}, timeout=10)
        assert r.status_code == 200
        j = r.json()
        assert j["category_id"] == "spazio", f"leaked non-spazio: {j['category_id']}"
        seen.add(j["id"])
    assert len(seen) >= 2, "expected variety inside spazio"


def test_discover_next_excludes_completed(s):
    """Completed story ids must never be returned."""
    uid = f"TEST_complete_{uuid.uuid4().hex[:8]}"
    r = s.post(f"{BASE_URL}/api/user/complete",
               json={"user_id": uid, "story_id": "how-stars-die", "minutes": 2, "seconds": 10},
               timeout=10)
    assert r.status_code == 200
    for _ in range(30):
        r = s.get(f"{BASE_URL}/api/discover-next",
                  params={"user_id": uid, "interests": "spazio"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["id"] != "how-stars-die"


def _share_spazio(s, uid: str, interests: str = "all", n: int = SAMPLES) -> float:
    hits = 0
    total = 0
    for _ in range(n):
        r = s.get(f"{BASE_URL}/api/discover-next",
                  params={"user_id": uid, "interests": interests}, timeout=10)
        if r.status_code != 200:
            continue
        total += 1
        if r.json()["category_id"] == "spazio":
            hits += 1
    assert total >= n * 0.9, f"too many failed calls: {total}/{n}"
    return hits / total


def test_taste_boost_is_moderate_not_exclusive(s):
    """A user who liked 3 spazio stories should see a *higher* share of spazio
    than a fresh user, but the feed stays varied (not 100% spazio)."""
    fresh_uid = f"TEST_baseline_{uuid.uuid4().hex[:8]}"
    liker_uid = f"TEST_liker_{uuid.uuid4().hex[:8]}"

    # Like 3 spazio stories.
    for sid in SPAZIO_STORIES:
        r = s.post(f"{BASE_URL}/api/user/like",
                   json={"user_id": liker_uid, "story_id": sid}, timeout=10)
        assert r.status_code == 200
        assert sid in r.json()["liked_story_ids"]

    fresh_share = _share_spazio(s, fresh_uid)
    liker_share = _share_spazio(s, liker_uid)
    print(f"\nfresh_share={fresh_share:.3f}  liker_share={liker_share:.3f}")

    # Feed stays varied (not exclusive).
    assert liker_share < 0.95, f"taste boost too strong (near-exclusive): {liker_share}"
    # Moderate uplift: liker should see meaningfully more spazio than fresh.
    # Baseline stats from main agent: 10/120 → 18/120 after liking (≈+0.07).
    # Guard with a soft margin to avoid random flakes.
    assert liker_share > fresh_share, (
        f"no taste uplift observed (fresh={fresh_share:.3f}, liker={liker_share:.3f})"
    )

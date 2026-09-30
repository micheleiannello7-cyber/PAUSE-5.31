"""PAUSE backend API regression tests."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="module")
def user_id():
    return f"TEST_{uuid.uuid4()}"


def _no_mongo_id(obj):
    """Recursively assert no `_id` key present."""
    if isinstance(obj, dict):
        assert "_id" not in obj, f"Found _id in {list(obj.keys())}"
        for v in obj.values():
            _no_mongo_id(v)
    elif isinstance(obj, list):
        for v in obj:
            _no_mongo_id(v)


# --------------------------- Categories ---------------------------
class TestCategories:
    def test_list_categories_count_and_shape(self, s):
        r = s.get(f"{API}/categories")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 13, f"expected 13 categories, got {len(data)}"
        required = {"id", "name", "icon", "color"}
        for cat in data:
            missing = required - set(cat.keys())
            assert not missing, f"cat missing keys {missing}: {cat}"
        _no_mongo_id(data)


# --------------------------- Stories list ---------------------------
class TestStoriesList:
    def test_list_stories_15_no_chapters_no_id(self, s):
        r = s.get(f"{API}/stories")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 15, f"expected >=15 stories, got {len(data)}"
        for st in data:
            assert "chapters" not in st, "preview should not contain chapters"
            assert "summary" not in st, "preview should not contain summary"
        _no_mongo_id(data)

    def test_filter_by_single_category(self, s):
        r = s.get(f"{API}/stories", params={"category_id": "scienza"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        for st in data:
            assert st["category_id"] == "scienza"

    def test_filter_by_multiple_interests(self, s):
        r = s.get(f"{API}/stories", params={"interests": "scienza,spazio"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2
        for st in data:
            assert st["category_id"] in {"scienza", "spazio"}

    def test_filter_all_returns_all(self, s):
        r = s.get(f"{API}/stories", params={"category_id": "all"})
        assert r.status_code == 200
        assert len(r.json()) >= 15


# --------------------------- Story detail ---------------------------
class TestStoryDetail:
    def test_get_specific_story_full(self, s):
        r = s.get(f"{API}/stories/sky-blue-sunset-orange")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "sky-blue-sunset-orange"
        assert isinstance(data.get("chapters"), list)
        assert len(data["chapters"]) == 6, f"expected 6 chapters, got {len(data['chapters'])}"
        for ch in data["chapters"]:
            for k in ("number", "title", "body", "icon", "glow_color"):
                assert k in ch
        assert data.get("summary")
        _no_mongo_id(data)

    def test_story_not_found_404(self, s):
        r = s.get(f"{API}/stories/does-not-exist-xyz")
        assert r.status_code == 404


# --------------------------- Next recommendation ---------------------------
class TestNextStory:
    def test_next_prefers_same_category(self, s):
        # sky-blue is category scienza; there are no other scienza stories,
        # so it will fall back. Use a category with >=2 stories: spazio.
        r = s.get(f"{API}/stories/black-holes-basics/next", params={"user_id": f"TEST_{uuid.uuid4()}"})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] != "black-holes-basics"
        # The thematic path (related-first) may cross categories by design.
        assert "chapters" not in data
        _no_mongo_id(data)

    def test_next_different_from_current(self, s):
        r = s.get(f"{API}/stories/sky-blue-sunset-orange/next")
        assert r.status_code == 200
        assert r.json()["id"] != "sky-blue-sunset-orange"


# --------------------------- User state flows ---------------------------
class TestUserFlows:
    def test_set_interests(self, s, user_id):
        r = s.post(f"{API}/user/interests", json={"user_id": user_id, "interests": ["scienza", "spazio"]})
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == user_id
        assert data["interests"] == ["scienza", "spazio"]
        _no_mongo_id(data)

    def test_bookmark_toggle_add_then_remove(self, s, user_id):
        # add
        r = s.post(f"{API}/user/bookmark", json={"user_id": user_id, "story_id": "black-holes-basics"})
        assert r.status_code == 200
        assert "black-holes-basics" in r.json()["bookmarked_story_ids"]
        # remove
        r = s.post(f"{API}/user/bookmark", json={"user_id": user_id, "story_id": "black-holes-basics"})
        assert r.status_code == 200
        assert "black-holes-basics" not in r.json()["bookmarked_story_ids"]

    def test_like_toggle(self, s, user_id):
        r = s.post(f"{API}/user/like", json={"user_id": user_id, "story_id": "mars-red"})
        assert r.status_code == 200
        assert "mars-red" in r.json()["liked_story_ids"]
        r = s.post(f"{API}/user/like", json={"user_id": user_id, "story_id": "mars-red"})
        assert r.status_code == 200
        assert "mars-red" not in r.json()["liked_story_ids"]

    def test_complete_two_stories_updates_counters(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        r1 = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "sky-blue-sunset-orange", "minutes": 2})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["session_count"] == 1
        assert d1["total_minutes"] == 2
        assert d1["streak_days"] == 1
        assert "sky-blue-sunset-orange" in d1["completed_story_ids"]

        r2 = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "mars-red", "minutes": 3})
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["session_count"] == 2, f"expected 2, got {d2['session_count']}"
        assert d2["total_minutes"] == 5
        # limit check
        lc = s.get(f"{API}/user/{uid}/limit-check")
        assert lc.status_code == 200
        lc_data = lc.json()
        # ENFORCE_LIMIT=true by default; under the limit → not blocked
        assert lc_data["enforce"] is True
        assert lc_data["blocked"] is False
        assert lc_data["session_count"] == 2

    def test_complete_same_story_not_double_counted(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "mars-red", "minutes": 2})
        r = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "mars-red", "minutes": 2})
        d = r.json()
        assert d["session_count"] == 1
        assert d["total_minutes"] == 2

    def test_limit_check_default_enforce_true(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        r = s.get(f"{API}/user/{uid}/limit-check")
        assert r.status_code == 200
        data = r.json()
        # ENFORCE_LIMIT defaults to true in this environment
        assert data["enforce"] is True
        assert data["blocked"] is False
        assert data["limit"] == 5


# --------------------------- Pause-limit & recap ---------------------------
class TestPauseLimitFlow:
    """Simulate 5 story completions and verify blocked + recap + liked."""

    def test_full_pause_flow(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        story_ids: list = []
        # 5 discover-next → complete cycle
        for _ in range(5):
            r = s.get(f"{API}/discover-next", params={"user_id": uid})
            assert r.status_code == 200
            sid = r.json()["id"]
            assert sid not in story_ids, "discover-next returned duplicate before limit"
            story_ids.append(sid)
            rc = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": sid, "minutes": 2})
            assert rc.status_code == 200
        # Like the first 2
        for sid in story_ids[:2]:
            r = s.post(f"{API}/user/like", json={"user_id": uid, "story_id": sid})
            assert r.status_code == 200

        # After 5 completions — ENFORCE_LIMIT=true → reached and blocked
        lc = s.get(f"{API}/user/{uid}/limit-check")
        assert lc.status_code == 200
        lc_data = lc.json()
        assert lc_data["enforce"] is True
        assert lc_data["session_count"] == 5
        assert lc_data["reached"] is True
        assert lc_data["blocked"] is True

        # session-stories returns 5 ordered recap items with summary
        sr = s.get(f"{API}/user/{uid}/session-stories")
        assert sr.status_code == 200
        recap = sr.json()
        assert len(recap) == 5, f"expected 5 recap, got {len(recap)}"
        assert [r["id"] for r in recap] == story_ids, "recap order must match completion order"
        for r in recap:
            assert r.get("summary"), f"recap missing summary for {r['id']}"
            assert "chapters" not in r
        _no_mongo_id(recap)

        # liked returns exactly the 2 liked stories (order-agnostic)
        lr = s.get(f"{API}/user/{uid}/liked")
        assert lr.status_code == 200
        liked = lr.json()
        assert {x["id"] for x in liked} == set(story_ids[:2])
        for x in liked:
            assert "chapters" not in x
            assert "summary" not in x
        _no_mongo_id(liked)

        # Toggle limit off → not blocked
        rs = s.post(f"{API}/user/limit-setting", json={"user_id": uid, "enabled": False})
        assert rs.status_code == 200
        assert rs.json()["limit_enabled"] is False
        lc2 = s.get(f"{API}/user/{uid}/limit-check").json()
        assert lc2["enforce"] is False
        assert lc2["blocked"] is False

        # Toggle back on → blocked again (ENFORCE_LIMIT=true, limit reached)
        rs2 = s.post(f"{API}/user/limit-setting", json={"user_id": uid, "enabled": True})
        assert rs2.status_code == 200
        lc3 = s.get(f"{API}/user/{uid}/limit-check").json()
        assert lc3["enforce"] is True
        assert lc3["blocked"] is True

    def test_session_stories_empty_for_new_user(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        r = s.get(f"{API}/user/{uid}/session-stories")
        assert r.status_code == 200
        assert r.json() == []

    def test_liked_empty_for_new_user(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        r = s.get(f"{API}/user/{uid}/liked")
        assert r.status_code == 200
        assert r.json() == []

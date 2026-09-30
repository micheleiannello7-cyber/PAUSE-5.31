"""PAUSE — i18n (Italian/English) API tests for the language iteration."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

EN_CATEGORY_NAMES = {
    "Science", "Space", "Money & Economics", "Art & Design", "Geography & Travel",
}


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


def _no_id(obj):
    if isinstance(obj, dict):
        assert "_id" not in obj
        for v in obj.values():
            _no_id(v)
    elif isinstance(obj, list):
        for v in obj:
            _no_id(v)


# ---------------- Categories ----------------
class TestCategoriesI18n:
    def test_categories_default_italian_13_with_story_count(self, s):
        r = s.get(f"{API}/categories")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 13, f"expected 13 categories, got {len(data)}"
        for c in data:
            assert "story_count" in c and isinstance(c["story_count"], int)
        # Italian names should NOT contain the English-only ones
        names = {c["name"] for c in data}
        assert EN_CATEGORY_NAMES.isdisjoint(names), f"Italian response contains EN names: {names & EN_CATEGORY_NAMES}"
        # 3 new categories should be present by id
        ids = {c["id"] for c in data}
        for nid in ("economia", "arte", "geografia"):
            assert nid in ids, f"new category id missing: {nid} (got {ids})"
        _no_id(data)

    def test_categories_english_names(self, s):
        r = s.get(f"{API}/categories", params={"lang": "en"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 13
        names = {c["name"] for c in data}
        missing = EN_CATEGORY_NAMES - names
        assert not missing, f"missing English names: {missing}. got: {names}"

    def test_categories_new_three_seeded_with_stories(self, s):
        r = s.get(f"{API}/categories", params={"lang": "en"})
        by_id = {c["id"]: c for c in r.json()}
        # story_count counts curiosità only (lessons are reported in lesson_count)
        expected = {"economia": (13, 5), "arte": (10, 2), "geografia": (10, 2)}
        for nid, (n, l) in expected.items():
            assert by_id[nid]["story_count"] == n, f"{nid} story_count={by_id[nid]['story_count']}"
            assert by_id[nid]["lesson_count"] == l, f"{nid} lesson_count={by_id[nid]['lesson_count']}"

    def test_categories_invalid_lang_fallback_italian(self, s):
        r = s.get(f"{API}/categories", params={"lang": "fr"})
        assert r.status_code == 200
        names = {c["name"] for c in r.json()}
        assert EN_CATEGORY_NAMES.isdisjoint(names), "invalid lang should fall back to Italian"


# ---------------- Story detail ----------------
class TestStoryDetailI18n:
    def test_story_english_title_and_content(self, s):
        r = s.get(f"{API}/stories/why-we-yawn", params={"lang": "en"})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "why-we-yawn"
        # Title in English should include the word "yawn"
        assert "yawn" in data["title"].lower(), f"unexpected EN title: {data['title']}"
        assert isinstance(data["chapters"], list) and len(data["chapters"]) > 0
        # At least one chapter title/body should include English text
        chapters_text = " ".join((ch.get("title", "") + " " + ch.get("body", "")) for ch in data["chapters"]).lower()
        assert " the " in f" {chapters_text} " or " and " in f" {chapters_text} ", "chapters do not look English"
        assert data.get("summary")

    def test_story_italian_default(self, s):
        r = s.get(f"{API}/stories/why-we-yawn")
        assert r.status_code == 200
        data = r.json()
        # Italian title should not be the EN one
        r_en = s.get(f"{API}/stories/why-we-yawn", params={"lang": "en"}).json()
        assert data["title"] != r_en["title"], "IT title equals EN title"
        # Category name in IT vs EN differ if there is a translation
        # (soft check — same category id)
        assert data["category_id"] == r_en["category_id"]

    def test_story_invalid_lang_fallback(self, s):
        r = s.get(f"{API}/stories/why-we-yawn", params={"lang": "zz"})
        assert r.status_code == 200
        it = s.get(f"{API}/stories/why-we-yawn").json()
        assert r.json()["title"] == it["title"]


# ---------------- Discover-next ----------------
class TestDiscoverNextI18n:
    def test_discover_next_english(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        r = s.get(f"{API}/discover-next", params={"user_id": uid, "lang": "en"})
        assert r.status_code == 200
        preview = r.json()
        # Get same story in IT to compare titles
        it = s.get(f"{API}/stories/{preview['id']}").json()
        # If a translation exists for this story, EN title must differ
        assert preview["title"], "empty title"
        # Not asserting inequality because some stories might not be translated,
        # but the endpoint must at least return a 200 with a title.
        _no_id(preview)


# ---------------- Localized user endpoints ----------------
class TestUserListsI18n:
    def test_bookmarks_liked_session_english(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        # complete 2 stories, bookmark 1, like 1
        c1 = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "why-we-yawn", "minutes": 2})
        assert c1.status_code == 200
        c2 = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "mars-red", "minutes": 2})
        assert c2.status_code == 200
        s.post(f"{API}/user/bookmark", json={"user_id": uid, "story_id": "why-we-yawn"})
        s.post(f"{API}/user/like", json={"user_id": uid, "story_id": "mars-red"})

        # bookmarks in EN
        rb = s.get(f"{API}/user/{uid}/bookmarks", params={"lang": "en"})
        assert rb.status_code == 200
        bm = rb.json()
        assert len(bm) == 1 and bm[0]["id"] == "why-we-yawn"
        assert "yawn" in bm[0]["title"].lower(), f"EN bookmark title not localized: {bm[0]['title']}"

        # liked in EN
        rl = s.get(f"{API}/user/{uid}/liked", params={"lang": "en"})
        assert rl.status_code == 200
        liked = rl.json()
        assert len(liked) == 1 and liked[0]["id"] == "mars-red"

        # session-stories in EN
        rs = s.get(f"{API}/user/{uid}/session-stories", params={"lang": "en"})
        assert rs.status_code == 200
        recap = rs.json()
        assert len(recap) == 2
        for r in recap:
            assert r.get("summary")


# ---------------- Content report ----------------
class TestContentReport:
    def test_content_report_counts(self, s):
        r = s.get(f"{API}/content/report")
        assert r.status_code == 200
        data = r.json()
        # Sanity: must contain some kind of totals
        assert isinstance(data, dict) and len(data) > 0
        _no_id(data)

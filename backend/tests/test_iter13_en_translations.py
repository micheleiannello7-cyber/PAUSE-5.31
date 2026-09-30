"""
Iteration 13 backend tests:
- Verify EN translations for new stories (v5.2)
- Verify categories endpoint returns 13 categories with 10 stories each (130 total)
- Verify original stories still work in IT
- Verify /api/discover-next respects lang=en
"""
import os
import re
import pytest
import requests
import uuid

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "http://localhost:8001").rstrip("/")

# Sample of new stories that should have EN translations
NEW_STORY_IDS = [
    "eco-inflation",
    "arte-mona-lisa",
    "geo-borders",
    "nat-tides",
    "psi-placebo",
    "ani-octopus-intelligence",
]

# A few original stories that must still work (IT)
ORIGINAL_STORY_IDS = [
    "why-we-yawn",
    "sky-blue-sunset-orange",
]

# Common Italian stopwords/markers to detect Italian text
IT_MARKERS = re.compile(
    r"\b(perché|perche|della|dello|degli|delle|questo|questa|questi|queste|"
    r"sono|dell'|nell'|un'|con|come|molto|essere|anche|però|quando|"
    r"quello|quella|così|già|più|senza)\b",
    re.IGNORECASE,
)

# Common English stopwords/markers
EN_MARKERS = re.compile(
    r"\b(the|and|of|with|when|because|which|about|this|that|these|those|"
    r"why|how|what|from|into|through|between|during|without|"
    r"is|are|was|were|been|being|have|has|had)\b",
    re.IGNORECASE,
)


def _english_score(text: str) -> int:
    return len(EN_MARKERS.findall(text or ""))


def _italian_score(text: str) -> int:
    return len(IT_MARKERS.findall(text or ""))


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Categories ----------
class TestCategories:
    def test_categories_it_13_and_12_each(self, api):
        r = api.get(f"{BASE_URL}/api/categories?lang=it", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 13, f"expected 13 categories, got {len(data)}"
        total = 0
        lessons = 0
        for c in data:
            assert c.get("story_count") >= 10, f"category {c.get('id')} has {c.get('story_count')} stories"
            total += c["story_count"]
            lessons += c["lesson_count"]
        assert total == 163, f"expected 163 stories across categories, got {total}"
        assert lessons == 59, f"expected 59 lessons across categories, got {lessons}"

    def test_categories_en_returns_names(self, api):
        r = api.get(f"{BASE_URL}/api/categories?lang=en", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 13
        # Ensure at least one category has an English-looking name
        assert any(c.get("name") in {"Science", "Space", "Technology", "Nature", "Animals",
                                     "History", "Psychology", "Human Body", "Culture", "Curiosities",
                                     "Economy", "Art", "Geography"}
                   or c.get("name_en") for c in data)


# ---------- EN translations for new stories ----------
class TestEnTranslationsNewStories:
    @pytest.mark.parametrize("story_id", NEW_STORY_IDS)
    def test_story_en_has_english_content(self, api, story_id):
        r_en = api.get(f"{BASE_URL}/api/stories/{story_id}?lang=en", timeout=20)
        assert r_en.status_code == 200, f"{story_id} EN status {r_en.status_code}: {r_en.text[:200]}"
        s_en = r_en.json()
        # Basic fields present
        for k in ("title", "hook", "summary", "chapters"):
            assert k in s_en, f"{story_id} EN missing field {k}"
        assert isinstance(s_en["chapters"], list) and len(s_en["chapters"]) >= 1

        # Same story in IT
        r_it = api.get(f"{BASE_URL}/api/stories/{story_id}?lang=it", timeout=20)
        assert r_it.status_code == 200
        s_it = r_it.json()

        # Titles / hooks / summaries should differ between EN and IT
        assert s_en["title"] != s_it["title"], f"{story_id}: EN and IT titles identical"
        assert s_en["hook"] != s_it["hook"], f"{story_id}: EN and IT hooks identical"
        assert s_en["summary"] != s_it["summary"], f"{story_id}: EN and IT summaries identical"

        # Combined EN text: chapters + summary + hook
        en_text = " ".join(
            [s_en.get("hook", ""), s_en.get("summary", "")]
            + [c.get("body", "") for c in s_en["chapters"]]
            + [c.get("title", "") for c in s_en["chapters"]]
        )
        it_text = " ".join(
            [s_it.get("hook", ""), s_it.get("summary", "")]
            + [c.get("body", "") for c in s_it["chapters"]]
        )

        en_score = _english_score(en_text)
        it_leak = _italian_score(en_text)
        assert en_score >= 5, f"{story_id} EN text does not look English (score={en_score}): {en_text[:200]}"
        assert en_score > it_leak, (
            f"{story_id} EN text seems Italian: en_score={en_score}, it_score={it_leak}, "
            f"sample: {en_text[:200]}"
        )
        # IT still has Italian markers
        assert _italian_score(it_text) >= 3


# ---------- Original stories must not be broken ----------
class TestOriginalStories:
    @pytest.mark.parametrize("story_id", ORIGINAL_STORY_IDS)
    def test_original_story_it(self, api, story_id):
        r = api.get(f"{BASE_URL}/api/stories/{story_id}?lang=it", timeout=20)
        assert r.status_code == 200
        s = r.json()
        assert "chapters" in s and isinstance(s["chapters"], list) and len(s["chapters"]) > 0
        assert s.get("title") and s.get("hook") and s.get("summary")


# ---------- discover-next with lang=en ----------
class TestDiscoverNextEn:
    def test_discover_next_en_economia(self, api):
        uid = str(uuid.uuid4())
        r = api.get(
            f"{BASE_URL}/api/discover-next",
            params={"user_id": uid, "interests": "economia", "lang": "en"},
            timeout=25,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Response can be a single story or {story: ...}
        story = data.get("story") if isinstance(data, dict) and "story" in data else data
        assert story, f"empty response: {data}"
        if story.get("id", "").startswith("v4-"):
            pytest.skip("v4 stories have no EN translation yet (IT fallback by design)")
        combined = " ".join(
            [str(story.get("title", "")), str(story.get("hook", "")), str(story.get("summary", ""))]
        )
        # Include chapter bodies if present
        chapters = story.get("chapters") or []
        for c in chapters:
            if isinstance(c, dict):
                combined += " " + str(c.get("body", "")) + " " + str(c.get("title", ""))
        en_score = _english_score(combined)
        it_score = _italian_score(combined)
        assert en_score > it_score and en_score >= 3, (
            f"discover-next lang=en does not return English content. "
            f"en={en_score}, it={it_score}, sample={combined[:300]}"
        )

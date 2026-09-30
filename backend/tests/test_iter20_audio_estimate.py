"""
Tests for iteration 20: audio minutes estimation bug fix (badge/TTS mismatch).

Verifies:
- Every story returns reading_time_min == deep_dive_time_min == ceil(minutes).
- The value matches the local estimator computed from full doc (title+hook+
  chapters+summary) using ~12.5 chars/sec + 1.5s chapter pause + 1.5s intro pause.
- List endpoint and detail endpoint agree on minutes for the same story/lang.
- English translation, when present, produces its own (potentially different)
  minutes value based on the translated text.
"""

import math
import os
import re
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")

_CHARS_PER_SEC = 12.5
_CHAPTER_PAUSE_S = 1.5
_INTRO_PAUSE_S = 1.5


def _clean(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"https?://\S+", "", text)
    t = re.sub(r"[*_#>~|`]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _estimate_minutes(doc: dict) -> int:
    total = 0
    total += len(_clean(doc.get("title") or ""))
    total += len(_clean(doc.get("hook") or ""))
    total += len(_clean(doc.get("summary") or ""))
    chapters = doc.get("chapters") or []
    for ch in chapters:
        total += len(_clean(ch.get("title") or ""))
        total += len(_clean(ch.get("body") or ""))
    seconds = total / _CHARS_PER_SEC
    seconds += len(chapters) * _CHAPTER_PAUSE_S
    if doc.get("hook") or doc.get("title"):
        seconds += _INTRO_PAUSE_S
    return max(1, math.ceil(seconds / 60.0))


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def stories_list(api):
    r = api.get(f"{BASE_URL}/api/stories", params={"limit": 50, "lang": "it"}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list) and len(data) >= 5
    return data


class TestListMinutesShape:
    """List endpoint must return sane minute fields for every item."""

    def test_all_stories_have_positive_minutes(self, stories_list):
        bad = [s for s in stories_list if not (isinstance(s.get("reading_time_min"), int) and s["reading_time_min"] >= 1)]
        assert not bad, f"stories with bad reading_time_min: {[b['id'] for b in bad[:5]]}"

    def test_reading_equals_deep_dive_in_list(self, stories_list):
        bad = [s["id"] for s in stories_list if s.get("reading_time_min") != s.get("deep_dive_time_min")]
        assert not bad, f"reading!=deep_dive for {bad[:5]}"


class TestEstimateMatches:
    """For 6 sample stories, fetching the full doc must match the local estimator."""

    @pytest.fixture(scope="class")
    def sample(self, stories_list):
        # Pick a diverse sample: first 6 stories from list.
        return stories_list[:6]

    def test_it_estimate_matches_full_doc(self, api, sample):
        mismatches = []
        for s in sample:
            r = api.get(f"{BASE_URL}/api/stories/{s['id']}", params={"lang": "it"}, timeout=30)
            assert r.status_code == 200, f"detail {s['id']}: {r.status_code}"
            full = r.json()
            expected = _estimate_minutes(full)
            got = full.get("deep_dive_time_min")
            if got != expected:
                mismatches.append((s["id"], expected, got))
        assert not mismatches, f"IT ceil estimate mismatches: {mismatches}"

    def test_list_and_detail_agree_it(self, api, sample):
        mismatches = []
        for s in sample:
            r = api.get(f"{BASE_URL}/api/stories/{s['id']}", params={"lang": "it"}, timeout=30)
            full = r.json()
            if full.get("deep_dive_time_min") != s.get("deep_dive_time_min"):
                mismatches.append((s["id"], s.get("deep_dive_time_min"), full.get("deep_dive_time_min")))
        assert not mismatches, f"list vs detail mismatches (IT): {mismatches}"


class TestEnglishTranslation:
    """When a story has a translation, English deep_dive_time_min must reflect the English text."""

    def test_en_estimate_matches_translated_text(self, api, stories_list):
        # Look for a story that has an English translation available.
        found = None
        for s in stories_list[:25]:
            r = api.get(f"{BASE_URL}/api/stories/{s['id']}", params={"lang": "en"}, timeout=30)
            if r.status_code != 200:
                continue
            full = r.json()
            # Heuristic: if title is different from the IT title in list, we have EN.
            if full.get("title") and full["title"] != s.get("title"):
                found = full
                break
        if not found:
            pytest.skip("No story with English translation available in first 25")
        expected = _estimate_minutes(found)
        assert found.get("deep_dive_time_min") == expected, (
            f"EN estimate mismatch on {found.get('id')}: expected {expected}, got {found.get('deep_dive_time_min')}"
        )
        assert found.get("reading_time_min") == expected


class TestConsistencyAcrossLangs:
    """List(lang=it) and List(lang=en) may differ but both must equal their detail counterpart."""

    def test_en_list_matches_en_detail(self, api):
        rl = api.get(f"{BASE_URL}/api/stories", params={"limit": 10, "lang": "en"}, timeout=30)
        assert rl.status_code == 200
        lst = rl.json()
        mismatches = []
        for s in lst[:5]:
            rd = api.get(f"{BASE_URL}/api/stories/{s['id']}", params={"lang": "en"}, timeout=30)
            if rd.status_code != 200:
                continue
            d = rd.json()
            if s.get("deep_dive_time_min") != d.get("deep_dive_time_min"):
                mismatches.append((s["id"], s.get("deep_dive_time_min"), d.get("deep_dive_time_min")))
        assert not mismatches, f"EN list vs detail mismatches: {mismatches}"

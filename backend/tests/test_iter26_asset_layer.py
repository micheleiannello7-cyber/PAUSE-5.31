"""Iteration 26 – Asset layer tests: TTS assets, media cache, ETag/Range, assets-report, story trim."""
import os
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
if not BASE_URL:
    # Try reading from frontend/.env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().strip('"')
                    break
    except Exception:
        pass
BASE_URL = (BASE_URL or "").rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- 1. TTS status for cached combination ----------
class TestTTSStatus:
    def test_moon_tides_it_ready(self, api):
        r = api.get(f"{BASE_URL}/api/tts/status/moon-tides", params={"lang": "it"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ready") is True, f"expected ready:true, got {data}"
        assert data.get("key"), "key must be non-null"
        assert data.get("generating") is False
        assert data.get("error") in (None, ""), f"unexpected error: {data.get('error')}"
        url = data.get("url") or ""
        assert "/api/tts/story/moon-tides" in url
        assert "lang=it" in url
        assert "v=" in url
        # content_hash equals v param
        ch = data.get("content_hash")
        assert ch, "content_hash must be present"
        # extract v param
        v = url.split("v=", 1)[1].split("&", 1)[0]
        assert v == ch, f"v param {v} != content_hash {ch}"
        # persist for later
        pytest.moon_tides_it_key = data["key"]
        pytest.moon_tides_it_url = url
        pytest.moon_tides_it_v = v

    def test_moon_tides_en_onyx_not_ready(self, api):
        r = api.get(
            f"{BASE_URL}/api/tts/status/moon-tides",
            params={"lang": "en", "voice": "onyx"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # do NOT call warmup; should be not ready
        assert data.get("ready") is False, f"expected ready:false, got {data}"


def _fetch_moon_tides_it_status(api):
    r = api.get(f"{BASE_URL}/api/tts/status/moon-tides", params={"lang": "it"}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("ready") and d.get("key") and d.get("url")
    return d["key"], d["url"]


# ---------- 3. Range + ETag + 304 ----------
class TestRangeAndETag:
    def test_range_request_206(self, api):
        key, url = _fetch_moon_tides_it_status(api)
        full = url if url.startswith("http") else f"{BASE_URL}{url}"
        r = api.get(full, headers={"Range": "bytes=0-99"}, timeout=15)
        assert r.status_code == 206, f"expected 206, got {r.status_code}"
        cr = r.headers.get("Content-Range", "")
        assert cr.startswith("bytes 0-99/"), f"Content-Range: {cr}"
        assert r.headers.get("Accept-Ranges", "").lower() == "bytes"
        etag = r.headers.get("ETag", "")
        assert etag == f'"{key}"', f"ETag {etag} != \"{key}\""

    def test_conditional_304(self, api):
        key, url = _fetch_moon_tides_it_status(api)
        full = url if url.startswith("http") else f"{BASE_URL}{url}"
        r = api.get(full, headers={"If-None-Match": f'"{key}"'}, timeout=15)
        assert r.status_code == 304, f"expected 304, got {r.status_code}"


# ---------- 4. Non-versioned url doesn't duplicate assets ----------
class TestNoDuplicateAssets:
    def test_no_new_asset_created(self, api):
        r0 = api.get(f"{BASE_URL}/api/content/assets-report", timeout=15)
        assert r0.status_code == 200
        before = r0.json().get("tts", {}).get("assets")
        assert isinstance(before, int)

        r1 = api.get(f"{BASE_URL}/api/tts/story/moon-tides", params={"lang": "it"}, timeout=20)
        assert r1.status_code == 200, r1.text
        ctype = r1.headers.get("Content-Type", "")
        assert "audio/mpeg" in ctype, f"Content-Type: {ctype}"
        assert r1.headers.get("ETag"), "ETag header must be present"

        r2 = api.get(f"{BASE_URL}/api/content/assets-report", timeout=15)
        after = r2.json().get("tts", {}).get("assets")
        assert after == before, f"asset count changed {before}->{after}"
        # spec expects 27
        assert after == 27, f"expected tts.assets == 27, got {after}"


# ---------- 5. Warmup for cached combinations returns 'cached' ----------
class TestWarmupCached:
    def test_warmup_moon_tides_it(self, api):
        r = api.post(f"{BASE_URL}/api/tts/warmup/moon-tides", params={"lang": "it"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "cached", f"expected 'cached', got {data}"
        assert data.get("url"), "url must be present"

    def test_warmup_sky_blue_en(self, api):
        r = api.post(
            f"{BASE_URL}/api/tts/warmup/sky-blue-sunset-orange",
            params={"lang": "en"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "cached"


# ---------- 6. Category media ----------
class TestCategoryMedia:
    def test_category_media_spazio(self, api):
        r = api.get(f"{BASE_URL}/api/category-media/spazio", timeout=15)
        assert r.status_code == 200, r.text
        assert "image/webp" in r.headers.get("Content-Type", "")
        etag = r.headers.get("ETag")
        assert etag, "ETag must be present"
        # 304 on repeat
        r2 = api.get(
            f"{BASE_URL}/api/category-media/spazio",
            headers={"If-None-Match": etag},
            timeout=15,
        )
        assert r2.status_code == 304, f"expected 304, got {r2.status_code}"

    def test_category_media_all(self, api):
        r = api.get(f"{BASE_URL}/api/category-media/all", timeout=15)
        assert r.status_code == 200
        assert "image/webp" in r.headers.get("Content-Type", "")


# ---------- 7. Media endpoint 404s ----------
class TestMedia404:
    def test_media_moon_tides_no_cover(self, api):
        r = api.get(f"{BASE_URL}/api/media/moon-tides", timeout=15)
        assert r.status_code == 404, f"expected 404, got {r.status_code}"

    def test_media_nonexistent(self, api):
        r = api.get(f"{BASE_URL}/api/media/nonexistent", timeout=15)
        assert r.status_code == 404


# ---------- 8. Assets report shape ----------
class TestAssetsReport:
    def test_assets_report_shape(self, api):
        r = api.get(f"{BASE_URL}/api/content/assets-report", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        tts = data.get("tts", {})
        assert isinstance(tts.get("assets"), int)
        assert isinstance(tts.get("by_combination"), list)
        covers = data.get("covers", {})
        assert covers.get("stories") == 437, f"expected 437, got {covers.get('stories')}"
        assert "image_disk_cache" in data


# ---------- 9. Story fields + trim ----------
class TestStoryTrim:
    def test_moon_tides_hero_thumb_field(self, api):
        r = api.get(f"{BASE_URL}/api/stories/moon-tides", params={"lang": "it"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "hero_image_thumb" in data, "hero_image_thumb field must exist"
        rt = data.get("reading_time_min")
        assert rt is None or rt <= 4, f"reading_time_min={rt} should be <=4"

    def test_fire_hot_trimmed_it(self, api):
        r = api.get(
            f"{BASE_URL}/api/stories/v8-why-is-fire-hot-and-what-is-a-flame-made-of",
            params={"lang": "it"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("reading_time_min") == 4, f"got {data.get('reading_time_min')}"
        chapters = data.get("chapters") or []
        assert len(chapters) == 6, f"expected 6 chapters, got {len(chapters)}"

    def test_fire_hot_trimmed_en(self, api):
        r = api.get(
            f"{BASE_URL}/api/stories/v8-why-is-fire-hot-and-what-is-a-flame-made-of",
            params={"lang": "en"},
            timeout=15,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("reading_time_min") == 4, f"got {data.get('reading_time_min')}"
        chapters = data.get("chapters") or []
        assert len(chapters) == 6, f"expected 6 chapters, got {len(chapters)}"


# ---------- 10. Regression ----------
class TestRegression:
    def test_categories(self, api):
        r = api.get(f"{BASE_URL}/api/categories", params={"lang": "it"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        cats = data if isinstance(data, list) else data.get("categories") or data.get("items")
        assert isinstance(cats, list)
        assert len(cats) == 12, f"expected 12 categories, got {len(cats)}"
        for c in cats:
            assert "illustration_generated" in c, f"missing illustration_generated on {c.get('id') or c}"

    def test_stories_list(self, api):
        r = api.get(f"{BASE_URL}/api/stories", params={"limit": 5}, timeout=15)
        assert r.status_code == 200

    def test_health(self, api):
        r = api.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200

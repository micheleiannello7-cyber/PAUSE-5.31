"""Iteration 11 — deck batch behaviour, tight category media and hero disk cache.

Focuses on the exact backend contracts the new Home relies on:
- /api/discover-batch pagination, uniqueness, count limits and interests filter
- /api/category-media with cutout+tight PNG RGBA output
- /api/media/{id}?size=hero versioned WebP served from disk cache
"""
import io
import os

import pytest
import requests
from PIL import Image

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/") or \
           os.environ.get("EXPO_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL must be set in frontend/.env or shell env"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    # Cold-cache first-hit can be slow on preview; use a generous default.
    orig = s.request
    def _req(method, url, **kw):
        kw.setdefault("timeout", 60)
        return orig(method, url, **kw)
    s.request = _req  # type: ignore
    return s


# ---------- /api/discover-batch ----------
class TestDiscoverBatch:
    def test_first_batch_returns_seven_unique(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/discover-batch",
                           params={"user_id": "t1", "count": 7, "lang": "it"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list) and len(data) == 7
        ids = [s["id"] for s in data]
        assert len(set(ids)) == 7, f"Duplicated ids: {ids}"
        for s in data:
            for k in ("id", "category_id", "title", "reading_time_min"):
                assert k in s, f"missing {k}"

    def test_second_batch_with_exclude_is_disjoint(self, api_client):
        first = api_client.get(f"{BASE_URL}/api/discover-batch",
                               params={"user_id": "t1", "count": 7, "lang": "it"}, timeout=20).json()
        exclude = ",".join(s["id"] for s in first)
        r = api_client.get(f"{BASE_URL}/api/discover-batch",
                           params={"user_id": "t1", "count": 7, "lang": "it", "exclude": exclude}, timeout=20)
        assert r.status_code == 200
        second = r.json()
        assert len(second) == 7
        second_ids = {s["id"] for s in second}
        assert not (second_ids & set(s["id"] for s in first)), "exclude ids leaked"
        assert len(second_ids) == 7

    def test_count_fourteen_ok_fifteen_rejected(self, api_client):
        r14 = api_client.get(f"{BASE_URL}/api/discover-batch",
                             params={"user_id": "t1", "count": 14, "lang": "it"}, timeout=20)
        assert r14.status_code == 200
        assert len(r14.json()) == 14
        r15 = api_client.get(f"{BASE_URL}/api/discover-batch",
                             params={"user_id": "t1", "count": 15, "lang": "it"}, timeout=20)
        assert r15.status_code == 422, r15.text

    def test_interests_filter_spazio(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/discover-batch",
                           params={"user_id": "t1", "count": 7, "lang": "it", "interests": "spazio"}, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data, "expected at least one spazio story"
        for s in data:
            assert s["category_id"] == "spazio", f"unexpected category {s['category_id']}"


# ---------- /api/category-media ----------
class TestCategoryMediaTight:
    def test_spazio_cutout_tight_png_rgba(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/category-media/spazio",
                           params={"cutout": "true", "tight": "true"}, timeout=30)
        assert r.status_code == 200, r.text
        ctype = r.headers.get("Content-Type", "")
        assert ctype.startswith("image/png"), f"unexpected content-type {ctype}"
        img = Image.open(io.BytesIO(r.content))
        assert img.mode == "RGBA", f"expected RGBA got {img.mode}"
        assert img.width > 0 and img.height > 0


# ---------- /api/media/{id} ----------
class TestMediaHero:
    def test_black_holes_hero_webp(self, api_client):
        v = "pause/hero/black-holes-basics-fe4c6d5d3d08.webp"
        r = api_client.get(f"{BASE_URL}/api/media/black-holes-basics",
                           params={"size": "hero", "v": v}, timeout=30)
        assert r.status_code == 200, r.text
        ctype = r.headers.get("Content-Type", "")
        assert ctype.startswith("image/webp"), f"unexpected content-type {ctype}"
        img = Image.open(io.BytesIO(r.content))
        assert img.width >= 800, f"hero too small: {img.width}x{img.height}"

"""Iter 32: category media (glossy-3d-v4) + onboarding data contract.

Covers what the onboarding redesign relies on:
- GET /api/categories returns 12 categories with illustration paths
  starting with pause/category/glossy-3d-v4/
- GET /api/category-media/animali and /api/category-media/all serve images
  (webp base, PNG for cutout variants) with correct content-types and 200 status.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not configured", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")

EXPECTED_CATEGORY_IDS = {
    "scienza", "spazio", "tecnologia", "natura", "animali", "storia",
    "psicologia", "corpo-umano", "cultura", "economia", "arte", "geografia",
}
MANIFEST_PREFIX = "pause/category/glossy-3d-v4/"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


# ---- /api/categories -------------------------------------------------------

def test_categories_returns_12_with_glossy_v4_paths(api):
    r = api.get(f"{BASE_URL}/api/categories?lang=it", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 12
    assert {c["id"] for c in data} == EXPECTED_CATEGORY_IDS
    # curiosita must be gone after the migration
    assert "curiosita" not in {c["id"] for c in data}
    for c in data:
        p = c.get("illustration_generated")
        assert isinstance(p, str) and p, f"{c['id']} missing illustration_generated"
        assert p.startswith(MANIFEST_PREFIX), f"{c['id']} -> {p}"
        assert p.endswith(".webp")


# ---- /api/category-media/{id} ---------------------------------------------

def test_media_animali_webp(api):
    r = api.get(f"{BASE_URL}/api/category-media/animali", timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/webp")
    assert int(r.headers.get("content-length", "0")) > 0 or r.content


def test_media_all_webp(api):
    r = api.get(f"{BASE_URL}/api/category-media/all", timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/webp")


def test_media_animali_cutout_v2(api):
    r = api.get(f"{BASE_URL}/api/category-media/animali", params={"cutout": "true", "cut": "2"}, timeout=30)
    assert r.status_code == 200
    # cutout returns PNG (RGBA) per implementation
    assert r.headers.get("content-type", "").startswith("image/png")


def test_media_animali_cutout_tight(api):
    r = api.get(f"{BASE_URL}/api/category-media/animali", params={"cutout": "true", "tight": "true"}, timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/png")


def test_media_unknown_404(api):
    r = api.get(f"{BASE_URL}/api/category-media/does-not-exist", timeout=30)
    assert r.status_code == 404

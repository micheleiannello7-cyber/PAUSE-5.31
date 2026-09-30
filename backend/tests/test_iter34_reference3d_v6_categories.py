"""Iter 34: reference-3d-v6 categories and media regression checks.

Scope:
- /api/categories returns exactly 12 expected categories with v6 artwork paths
- /api/category-media/{id} returns bytes for all 12 + all (13/13)
- cutout=true regression on selected IDs returns image bytes
"""

import os
import pytest
import requests


BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not configured", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")

EXPECTED_CATEGORY_IDS = {
    "scienza",
    "spazio",
    "tecnologia",
    "natura",
    "animali",
    "storia",
    "psicologia",
    "corpo-umano",
    "cultura",
    "economia",
    "arte",
    "geografia",
}

ALL_MEDIA_IDS = sorted(list(EXPECTED_CATEGORY_IDS | {"all"}))
V6_PREFIX = "pause/category/reference-3d-v6/"


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    return session


# categories contract
def test_categories_exact_12_and_reference_v6_paths(api_client):
    response = api_client.get(f"{BASE_URL}/api/categories?lang=it", timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 12

    ids = {row.get("id") for row in payload}
    assert ids == EXPECTED_CATEGORY_IDS

    for row in payload:
        generated = row.get("illustration_generated")
        assert isinstance(generated, str) and generated
        assert generated.startswith(V6_PREFIX), f"{row.get('id')} -> {generated}"
        assert generated.endswith(".webp")


# media delivery
@pytest.mark.parametrize("category_id", ALL_MEDIA_IDS)
def test_category_media_all_13_return_image_bytes(api_client, category_id):
    response = api_client.get(f"{BASE_URL}/api/category-media/{category_id}", timeout=30)
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("image/"), f"{category_id} content-type={content_type}"
    assert len(response.content) > 0


# cutout badge regression
@pytest.mark.parametrize("category_id", ["corpo-umano", "spazio", "geografia"])
def test_category_media_cutout_true_selected_ids(api_client, category_id):
    response = api_client.get(
        f"{BASE_URL}/api/category-media/{category_id}",
        params={"cutout": "true", "cut": "2"},
        timeout=30,
    )
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("image/"), f"{category_id} cutout content-type={content_type}"
    assert len(response.content) > 0

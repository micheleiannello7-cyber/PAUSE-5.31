"""Iteration 28: colorful-3d-v3 category artwork/media regression tests."""

# Module coverage: /api/categories and /api/category-media/{id} for colorful-3d-v3.
import io
import os

import pytest
import requests
from PIL import Image


BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not configured", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")


EXPECTED_12_IDS = {
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


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


def test_categories_are_v3_and_expected_12(session: requests.Session):
    response = session.get(f"{BASE_URL}/api/categories?lang=it", timeout=30)
    assert response.status_code == 200

    categories = response.json()
    returned_ids = {c["id"] for c in categories}
    assert returned_ids == EXPECTED_12_IDS
    assert len(categories) == 12

    for category in categories:
        generated = category.get("illustration_generated")
        assert isinstance(generated, str) and generated
        assert generated.startswith("pause/category/colorful-3d-v3/")
        assert generated.endswith(".webp")


def test_category_media_v3_12_plus_all_is_decodable_webp(session: requests.Session):
    categories_response = session.get(f"{BASE_URL}/api/categories?lang=it", timeout=30)
    assert categories_response.status_code == 200
    categories = categories_response.json()

    for category in categories:
        category_id = category["id"]
        version_token = category["illustration_generated"]
        response = session.get(
            f"{BASE_URL}/api/category-media/{category_id}?v={requests.utils.quote(version_token, safe='')}",
            timeout=30,
        )
        assert response.status_code == 200, f"media failed for {category_id}"
        assert response.headers.get("content-type", "").startswith("image/webp")
        image = Image.open(io.BytesIO(response.content))
        image.verify()
        assert image.format == "WEBP"

    all_response = session.get(f"{BASE_URL}/api/category-media/all?v=colorful-3d-v3", timeout=30)
    assert all_response.status_code == 200
    assert all_response.headers.get("content-type", "").startswith("image/webp")
    all_image = Image.open(io.BytesIO(all_response.content))
    all_image.verify()
    assert all_image.format == "WEBP"

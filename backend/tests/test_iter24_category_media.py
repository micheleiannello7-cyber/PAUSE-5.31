"""Iteration 24: category artwork/media API regression tests."""

# Module coverage: /api/categories and /api/category-media/{id} illustrated assets.
import os
from pathlib import Path

import pytest
import requests


BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not configured", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")


EXPECTED_CATEGORY_IDS = {
    "scienza", "spazio", "tecnologia", "natura", "animali", "storia", "psicologia",
    "corpo-umano", "cultura", "curiosita", "economia", "arte", "geografia",
}


def _parse_webp_size(payload: bytes) -> tuple[int, int]:
    if len(payload) < 30 or payload[0:4] != b"RIFF" or payload[8:12] != b"WEBP":
        raise AssertionError("Not a valid WEBP RIFF payload")

    idx = 12
    while idx + 8 <= len(payload):
        chunk = payload[idx:idx + 4]
        chunk_size = int.from_bytes(payload[idx + 4:idx + 8], "little")
        data_start = idx + 8
        data_end = data_start + chunk_size
        if data_end > len(payload):
            break

        if chunk == b"VP8X" and chunk_size >= 10:
            w = int.from_bytes(payload[data_start + 4:data_start + 7], "little") + 1
            h = int.from_bytes(payload[data_start + 7:data_start + 10], "little") + 1
            return w, h
        if chunk == b"VP8L" and chunk_size >= 5:
            b0, b1, b2, b3 = payload[data_start + 1:data_start + 5]
            w = ((b1 & 0x3F) << 8 | b0) + 1
            h = ((b3 & 0x0F) << 10 | (b2 << 2) | ((b1 & 0xC0) >> 6)) + 1
            return w, h
        if chunk == b"VP8 " and chunk_size >= 10:
            w = int.from_bytes(payload[data_start + 6:data_start + 8], "little") & 0x3FFF
            h = int.from_bytes(payload[data_start + 8:data_start + 10], "little") & 0x3FFF
            return w, h

        idx = data_end + (chunk_size % 2)

    raise AssertionError("Unable to parse WEBP dimensions")


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


def test_categories_have_expected_ids_and_generated_paths(session: requests.Session):
    response = session.get(f"{BASE_URL}/api/categories?lang=it", timeout=30)
    assert response.status_code == 200
    categories = response.json()

    returned_ids = {c["id"] for c in categories}
    assert returned_ids == EXPECTED_CATEGORY_IDS
    assert len(categories) == 13

    for category in categories:
        path = category.get("illustration_generated")
        assert isinstance(path, str) and path
        assert path.startswith("pause/category/glass-2026-09-v1/")
        assert path.endswith(".webp")
        assert "base64" not in path.lower()
        assert not path.startswith(("http://", "https://"))

    animali = next(c for c in categories if c["id"] == "animali")
    assert animali["illustration_generated"].endswith("animali-6570109e3527.webp")


def test_category_media_cache_headers(session: requests.Session):
    version = "glass-2026-09-v1"
    for category_id in sorted(EXPECTED_CATEGORY_IDS | {"all"}):
        response = session.get(f"{BASE_URL}/api/category-media/{category_id}?v={version}", timeout=30)
        assert response.status_code == 200, f"media failed for {category_id}"
        assert response.headers.get("content-type", "").startswith("image/webp")
        cache_control = response.headers.get("cache-control", "")
        assert "max-age=31536000" in cache_control
        assert "immutable" in cache_control


def test_category_media_webp_dimensions_480(session: requests.Session):
    version = "glass-2026-09-v1"
    for category_id in sorted(EXPECTED_CATEGORY_IDS | {"all"}):
        response = session.get(f"{BASE_URL}/api/category-media/{category_id}?v={version}", timeout=30)
        assert response.status_code == 200, f"media failed for {category_id}"

        width, height = _parse_webp_size(response.content)
        assert (width, height) == (480, 480), f"{category_id} returned {width}x{height}"


def test_unknown_category_media_returns_404(session: requests.Session):
    response = session.get(f"{BASE_URL}/api/category-media/unknown-category-id?v=glass-2026-09-v1", timeout=30)
    assert response.status_code == 404
